#!/usr/bin/env python3

import sys
import os
from datetime import date, timedelta, datetime
import random

# Añadir el directorio src al path para importar los modelos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from sqlalchemy.exc import IntegrityError

from src.extensiones import db
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.ejercicio import Ejercicio
from src.modelos.sesion import Sesion
from src.modelos.asociaciones import Paciente_Profesional, Ejercicio_Profesional
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.modelos.videoRespuesta import VideoRespuesta
from src.modelos.evaluacion import Evaluacion


def create_app():
    app = Flask(__name__)

    # Usar DATABASE_URL de Heroku si existe, sino SQLite local
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///TerapiTrack.db')

    # Corregir prefijo de Heroku (postgres:// → postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = '1234albertolancharesdiez'
    db.init_app(app)
    return app


def poblar_datos():
    print("🔄 Limpiando base de datos...")
    db.drop_all()
    db.create_all()

    print("👥 Creando 20 usuarios (5 profesionales + 15 pacientes con Parkinson)...")
    usuarios_data = [
        # 1 Administrador
        {'nombre': 'Admin', 'apellidos': 'Sistema', 'email': 'admin@terapitrack.com', 'rol': 0, 'password': 'admin123'},

        # 5 Profesionales
        {'nombre': 'Dr. Juan', 'apellidos': 'Perez', 'email': 'juan.perez@terapitrack.com', 'rol': 2,
         'password': 'medico123', 'especialidad': 'Rehabilitación Neurológica', 'tipo': 'MEDICO'},
        {'nombre': 'Terapeuta Ana', 'apellidos': 'Lopez', 'email': 'ana.lopez@terapitrack.com', 'rol': 2,
         'password': 'terapeuta123', 'especialidad': 'Fisioterapia Neurológica', 'tipo': 'TERAPEUTA'},
        {'nombre': 'Psicólogo Carlos', 'apellidos': 'Gomez', 'email': 'carlos.gomez@terapitrack.com', 'rol': 2,
         'password': 'psicologo123', 'especialidad': 'Neuropsicología', 'tipo': 'PSICOLOGO'},
        {'nombre': 'Enfermero Luis', 'apellidos': 'Martinez', 'email': 'luis.martinez@terapitrack.com', 'rol': 2,
         'password': 'enfermero123', 'especialidad': 'Cuidados Neurológicos', 'tipo': 'ENFERMERO'},
        {'nombre': 'Dr. Maria', 'apellidos': 'Sanchez', 'email': 'maria.sanchez@terapitrack.com', 'rol': 2,
         'password': 'medico123', 'especialidad': 'Neurología', 'tipo': 'MEDICO'},

        # 15 Pacientes con Parkinson
        {'nombre': 'Antonio', 'apellidos': 'García Martín', 'email': 'antonio.garcia@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1950, 1, 15),
         'condicion': 'Parkinson - Estadio I', 'notas': 'Temblor leve en mano derecha'},
        {'nombre': 'María Carmen', 'apellidos': 'López Silva', 'email': 'mariacarmen.lopez@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1948, 3, 22),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Rigidez bilateral, bradicinesia'},
        {'nombre': 'José Manuel', 'apellidos': 'Rodríguez Vega', 'email': 'josemanuel.rodriguez@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1952, 7, 8),
         'condicion': 'Parkinson - Estadio I', 'notas': 'Diagnóstico reciente'},
        {'nombre': 'Isabel', 'apellidos': 'Fernández Ruiz', 'email': 'isabel.fernandez@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1945, 11, 30),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Problemas de equilibrio'},
        {'nombre': 'Francisco', 'apellidos': 'Jiménez Torres', 'email': 'francisco.jimenez@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1949, 5, 12),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Temblor en reposo'},
        {'nombre': 'Carmen', 'apellidos': 'Moreno Castillo', 'email': 'carmen.moreno@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1951, 9, 18),
         'condicion': 'Parkinson - Estadio I', 'notas': 'Lentitud de movimientos'},
        {'nombre': 'Miguel', 'apellidos': 'Sánchez Herrera', 'email': 'miguel.sanchez@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1946, 2, 14),
         'condicion': 'Parkinson - Estadio III', 'notas': 'Inestabilidad postural'},
        {'nombre': 'Dolores', 'apellidos': 'Ortega Muñoz', 'email': 'dolores.ortega@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1953, 8, 25),
         'condicion': 'Parkinson - Estadio I', 'notas': 'Temblor de acción'},
        {'nombre': 'Rafael', 'apellidos': 'Delgado Peña', 'email': 'rafael.delgado@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1947, 12, 3),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Rigidez en cuello'},
        {'nombre': 'Pilar', 'apellidos': 'Romero Aguilar', 'email': 'pilar.romero@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1950, 6, 19),
         'condicion': 'Parkinson - Estadio I', 'notas': 'Micrografía'},
        {'nombre': 'Fernando', 'apellidos': 'Vargas Medina', 'email': 'fernando.vargas@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1954, 4, 7),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Marcha festinante'},
        {'nombre': 'Rosa', 'apellidos': 'Iglesias Cortés', 'email': 'rosa.iglesias@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1948, 10, 11),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Bradicinesia severa'},
        {'nombre': 'Eduardo', 'apellidos': 'Castro Blanco', 'email': 'eduardo.castro@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1951, 1, 28),
         'condicion': 'Parkinson - Estadio I', 'notas': 'Pérdida de expresión facial'},
        {'nombre': 'Amparo', 'apellidos': 'Prieto Navarro', 'email': 'amparo.prieto@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1949, 7, 16),
         'condicion': 'Parkinson - Estadio III', 'notas': 'Congelamiento de la marcha'},
        {'nombre': 'Joaquín', 'apellidos': 'Rubio Serrano', 'email': 'joaquin.rubio@email.com',
         'rol': 1, 'password': 'paciente123', 'fecha_nac': date(1952, 3, 9),
         'condicion': 'Parkinson - Estadio II', 'notas': 'Distonía focal'}
    ]

    usuarios = []
    for udata in usuarios_data:
        u = Usuario(
            Nombre=udata['nombre'],
            Apellidos=udata['apellidos'],
            Email=udata['email'],
            Rol_Id=udata['rol'],
            Estado=1
        )
        u.set_contraseña(udata['password'])
        db.session.add(u)
        db.session.flush()
        usuarios.append((u, udata))

    # Crear profesionales
    for u, data in usuarios:
        if u.Rol_Id == 2:
            p = Profesional(
                Usuario_Id=u.Id,
                Especialidad=data['especialidad'],
                Tipo_Profesional=data['tipo']
            )
            db.session.add(p)

    # Crear pacientes
    for u, data in usuarios:
        if u.Rol_Id == 1:
            p = Paciente(
                Usuario_Id=u.Id,
                Fecha_Nacimiento=data['fecha_nac'],
                Condicion_Medica=data['condicion'],
                Notas=data['notas']
            )
            db.session.add(p)

    print("🏃‍♂️ Creando ejercicios específicos para Parkinson...")
    ejercicios_data = [
        {'nombre': 'Flexión de codo asistida', 'descripcion': 'Dobla el codo con ayuda de la otra mano. Sentado o tumbado.', 'tipo': 'Fortalecimiento', 'video': 'flexion_codo.mp4', 'duracion': 43},
        {'nombre': 'Rotación de muñeca', 'descripcion': 'Rota suavemente la muñeca en círculos, apoyando el antebrazo.', 'tipo': 'Movilidad', 'video': 'rotacion_muneca.mp4', 'duracion': 105},
        {'nombre': 'Separar y juntar dedos', 'descripcion': 'Abre y cierra los dedos de la mano lentamente.', 'tipo': 'Movilidad', 'video': 'dedos.mp4', 'duracion': 85},
        {'nombre': 'Flexión de tobillo', 'descripcion': 'Mueve el pie hacia arriba y abajo desde la cama o silla.', 'tipo': 'Movilidad', 'video': 'flexion_tobillo.mp4', 'duracion': 15},
        {'nombre': 'Respiración profunda', 'descripcion': 'Inspira por la nariz y suelta el aire por la boca lentamente.', 'tipo': 'Relajación', 'video': 'respiracion_profunda.mp4', 'duracion': 59},
        {'nombre': 'Encoger hombros', 'descripcion': 'Lleva los hombros hacia las orejas y relájalos.', 'tipo': 'Movilidad', 'video': 'hombros.mp4', 'duracion': 10},
        {'nombre': 'Giro de cabeza', 'descripcion': 'Gira la cabeza suavemente a un lado y luego al otro.', 'tipo': 'Movilidad', 'video': 'giro_cabeza.mp4', 'duracion': 57},
        {'nombre': 'Marcha en el lugar', 'descripcion': 'Simula caminar levantando alternadamente los pies.', 'tipo': 'Equilibrio', 'video': 'marcha_sentado.mp4', 'duracion': 25},
        {'nombre': 'Expresión facial', 'descripcion': 'Ejercicios de músculos faciales: sonreír, fruncir ceño, abrir ojos.', 'tipo': 'Movilidad', 'video': 'expresion_facial.mp4', 'duracion': 350},
        {'nombre': 'Vocalizaciones', 'descripcion': 'Ejercicios de voz: decir "AH" fuerte y claro durante 10 segundos.', 'tipo': 'Relajación', 'video': 'vocalizaciones.mp4', 'duracion': 326},
        {'nombre': 'Pasos amplios', 'descripcion': 'Caminar con pasos exagerados para mejorar la longitud del paso.', 'tipo': 'Equilibrio', 'video': 'pasos_amplios.mp4', 'duracion': 162},
        {'nombre': 'Balanceo de brazos', 'descripcion': 'Caminar balanceando exageradamente los brazos alternos.', 'tipo': 'Equilibrio', 'video': 'balanceo_brazos.mp4', 'duracion': 55},
        {'nombre': 'Levantarse de silla', 'descripcion': 'Práctica de levantarse y sentarse sin usar las manos.', 'tipo': 'Fortalecimiento', 'video': 'levantarse_silla.mp4', 'duracion': 69},
        {'nombre': 'Aplausos rítmicos', 'descripcion': 'Aplaudir siguiendo diferentes ritmos y velocidades.', 'tipo': 'Movilidad', 'video': 'aplausos_ritmicos.mp4', 'duracion': 185}
    ]

    ejercicios = []
    for edata in ejercicios_data:
        e = Ejercicio(
            Nombre=edata['nombre'],
            Descripcion=edata['descripcion'],
            Tipo=edata['tipo'],
            Video=edata['video'],
            Duracion=edata['duracion']
        )
        db.session.add(e)
        db.session.flush()
        ejercicios.append(e)

    print("IDs de ejercicios creados:")
    for e in ejercicios:
        print(e.Id, "-", e.Nombre)

    print("🔗 Asociando ejercicios con profesionales...")
    profesionales_objs = [u for u, d in usuarios if u.Rol_Id == 2]
    for profesional in profesionales_objs:
        for ejercicio in ejercicios:
            existe = Ejercicio_Profesional.query.filter_by(
                Profesional_Id=profesional.Id,
                Ejercicio_Id=ejercicio.Id
            ).first()
            if not existe:
                asociacion = Ejercicio_Profesional(
                    Profesional_Id=profesional.Id,
                    Ejercicio_Id=ejercicio.Id
                )
                db.session.add(asociacion)

    print("🔗 Creando vinculaciones paciente-profesional...")
    pacientes_objs = [u for u, d in usuarios if u.Rol_Id == 1]
    profesionales_objs = [u for u, d in usuarios if u.Rol_Id == 2]
    vinculaciones = []

    for i, paciente in enumerate(pacientes_objs):
        profesional = profesionales_objs[i % len(profesionales_objs)]
        v = Paciente_Profesional(
            Paciente_Id=paciente.Id,
            Profesional_Id=profesional.Id,
            Fecha_Asignacion=date.today() - timedelta(days=random.randint(1, 60))
        )
        db.session.add(v)
        vinculaciones.append((paciente.Id, profesional.Id))

    print("📅 Creando múltiples sesiones (pendientes y completadas)...")
    sesiones = []

    for pid, prid in vinculaciones:
        num_sesiones = random.randint(6, 10)

        for j in range(num_sesiones):
            if j < num_sesiones * 0.5:
                estado = 'COMPLETADA'
                fecha_programada = date.today() - timedelta(days=random.randint(5, 90))
            else:
                estado = 'PENDIENTE'
                fecha_programada = date.today() + timedelta(days=random.randint(1, 30))

            s = Sesion(
                Paciente_Id=pid,
                Profesional_Id=prid,
                Estado=estado,
                Fecha_Asignacion=fecha_programada - timedelta(days=random.randint(1, 20)),
                Fecha_Programada=fecha_programada
            )
            db.session.add(s)
            db.session.flush()
            sesiones.append(s)

    print("🏃‍♂️ Asignando ejercicios a sesiones...")
    Evaluacion.query.delete()
    VideoRespuesta.query.delete()
    Ejercicio_Sesion.query.delete()
    db.session.commit()

    for s in sesiones:
        num_ejercicios = random.randint(2, 4)
        selected_ej = random.sample(ejercicios, num_ejercicios)

        for ej in selected_ej:
            existe = Ejercicio_Sesion.query.filter_by(
                Sesion_Id=s.Id,
                Ejercicio_Id=ej.Id
            ).first()
            if existe:
                continue

            es = Ejercicio_Sesion(
                Sesion_Id=s.Id,
                Ejercicio_Id=ej.Id
            )
            db.session.add(es)

            if s.Estado == 'COMPLETADA':
                video_resp = VideoRespuesta(
                    Ejercicio_Sesion_Id=es.Id,
                    Ruta_Almacenamiento="cloudinary://<438427374897353>:<jlQrF-JJ4yAMoScxwDj78J_W3k8>@dck4l5hfp",
                    Fecha_Expiracion=date.today() + timedelta(days=30)
                )
                db.session.add(video_resp)

                if random.random() < 0.7:
                    evaluacion = Evaluacion(
                        Ejercicio_Sesion_Id=es.Id,
                        Puntuacion=random.randint(2, 5),
                        Comentarios=random.choice([
                            "Excelente ejecución del ejercicio",
                            "Buena técnica, mantener el ritmo",
                            "Necesita mejorar la amplitud del movimiento",
                            "Progreso notable desde la última sesión",
                            "Ejercicio realizado correctamente",
                            "Se observa rigidez, aumentar frecuencia",
                            "Muy buen control del temblor"
                        ]),
                        Fecha_Evaluacion=s.Fecha_Programada + timedelta(days=random.randint(1, 3))
                    )
                    db.session.add(evaluacion)

    db.session.commit()

    print(f"✅ Base de datos poblada exitosamente:")
    print(f"   👥 Usuarios totales: {len(usuarios)}")
    print(f"   🏥 Profesionales: {len(profesionales_objs)}")
    print(f"   🤒 Pacientes con Parkinson: {len(pacientes_objs)}")
    print(f"   🏃‍♂️ Ejercicios específicos: {len(ejercicios)}")
    print(f"   🔗 Vinculaciones: {len(vinculaciones)}")
    print(f"   📅 Sesiones totales: {len(sesiones)}")
    print(f"   ✅ Sesiones completadas: {len([s for s in sesiones if s.Estado == 'COMPLETADA'])}")
    print(f"   ⏳ Sesiones pendientes: {len([s for s in sesiones if s.Estado == 'PENDIENTE'])}")




if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            poblar_datos()
            print("🎉 ¡Base de datos poblada correctamente!")
        except Exception as e:
            print(f"❌ Error al poblar la base de datos: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
