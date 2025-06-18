import pytest
from datetime import date, timedelta
from src.modelos.sesion import Sesion
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.ejercicio import Ejercicio
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.extensiones import db

class TestSesion:
    def test_creacion_y_relaciones(self, app):
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=1,
                Fecha_Nacimiento=date(2000, 1, 1),
                Condicion_Medica="Condición",
                Notas="Notas"
            )
            profesional = Profesional(
                Usuario_Id=2,
                Especialidad="Fisioterapia",
                Tipo_Profesional="TERAPEUTA"
            )
            db.session.add_all([paciente, profesional])
            db.session.commit()
            sesion = Sesion(
                Paciente_Id=paciente.Usuario_Id,
                Profesional_Id=profesional.Usuario_Id,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=date.today() + timedelta(days=3)
            )
            db.session.add(sesion)
            db.session.commit()
            assert sesion.paciente.Usuario_Id == paciente.Usuario_Id
            assert sesion.profesional.Usuario_Id == profesional.Usuario_Id

    def test_estados(self, app):
        with app.app_context():
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=date.today()
            )
            assert sesion.es_pendiente() is True
            sesion.Estado = "COMPLETADA"
            assert sesion.es_completada() is True
            sesion.Estado = "CANCELADA"
            assert sesion.es_cancelada() is True

    def test_check_constraint_estado(self, app):
        with app.app_context():
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="INVALIDO",
                Fecha_Programada=date.today()
            )
            db.session.add(sesion)
            with pytest.raises(Exception):
                db.session.commit()
                db.session.rollback()

    def test_obtener_ejercicios(self, app):
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Rotación de muñeca",
                Descripcion="Mover la muñeca suavemente.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=15
            )
            db.session.add(ejercicio)
            db.session.commit()

            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=date.today()
            )
            db.session.add(sesion)
            db.session.commit()

            # Sin ejercicios asociados
            assert sesion.obtener_ejercicios() == 0
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=sesion.Id,
                Ejercicio_Id=ejercicio.Id
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()

            # Refresca la relación para asegurar que SQLAlchemy la ve
            db.session.refresh(sesion)
            assert sesion.obtener_ejercicios() == 1


    def test_fecha_programada_legible(self, app):
        with app.app_context():
            fecha = date(2025, 6, 17)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=fecha
            )
            assert sesion.fecha_programada_legible() == "17/06/2025"
            sesion.Fecha_Programada = None
            assert sesion.fecha_programada_legible() == ""

    def test_repr(self, app):
        with app.app_context():
            fecha = date(2025, 6, 17)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="COMPLETADA",
                Fecha_Programada=fecha
            )
            esperado = f"<Sesion Id={sesion.Id} Estado={sesion.Estado} Fecha_Programada={sesion.Fecha_Programada}>"
            assert repr(sesion) == esperado

    def test_to_dict(self, app):
        with app.app_context():
            fecha = date(2025, 6, 17)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=fecha
            )
            data = sesion.to_dict()
            assert data["Paciente_Id"] == 1
            assert data["Profesional_Id"] == 2
            assert data["Estado"] == "PENDIENTE"
            assert data["Fecha_Programada"] == str(fecha)
