"""
Tests del modelo Sesion.
Prueba estados, relaciones, restricciones y métodos de formateo.
"""

import pytest
from datetime import datetime, timedelta
from src.modelos.sesion import Sesion
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.ejercicio import Ejercicio
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.extensiones import db


class TestSesion:
    """Suite de tests para el modelo Sesion."""

    def test_creacion_y_relaciones(self, app):
        """Prueba la creación de sesión y relaciones con Paciente y Profesional."""
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=1,
                Fecha_Nacimiento=datetime(2000, 1, 1).date(),
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

            ahora = datetime.now()
            sesion = Sesion(
                Paciente_Id=paciente.Usuario_Id,
                Profesional_Id=profesional.Usuario_Id,
                Fecha_Asignacion=ahora,
                Estado="PENDIENTE",
                Fecha_Programada=ahora + timedelta(days=3)
            )
            db.session.add(sesion)
            db.session.commit()

            assert sesion.paciente.Usuario_Id == paciente.Usuario_Id
            assert sesion.profesional.Usuario_Id == profesional.Usuario_Id

    def test_estados(self, app):
        """Prueba los métodos es_pendiente(), es_completada() y es_cancelada()."""
        with app.app_context():
            ahora = datetime.now()
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=ahora,
                Estado="PENDIENTE",
                Fecha_Programada=ahora
            )
            assert sesion.es_pendiente() is True
            sesion.Estado = "COMPLETADA"
            assert sesion.es_completada() is True
            sesion.Estado = "CANCELADA"
            assert sesion.es_cancelada() is True

    def test_check_constraint_estado(self, app):
        """Prueba la restricción CHECK de Estado (solo valores permitidos)."""
        with app.app_context():
            ahora = datetime.now()
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=ahora,
                Estado="INVALIDO",
                Fecha_Programada=ahora
            )
            db.session.add(sesion)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_obtener_ejercicios(self, app):
        """Prueba el método obtener_ejercicios() que cuenta ejercicios asignados."""
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

            ahora = datetime.now()
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=ahora,
                Estado="PENDIENTE",
                Fecha_Programada=ahora
            )
            db.session.add(sesion)
            db.session.commit()

            assert sesion.obtener_ejercicios() == 0

            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=sesion.Id,
                Ejercicio_Id=ejercicio.Id
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()

            db.session.refresh(sesion)
            assert sesion.obtener_ejercicios() == 1

    def test_fecha_programada_legible(self, app):
        """Prueba el formateo de fecha programada a formato dd/mm/aaaa."""
        with app.app_context():
            fecha = datetime(2025, 6, 17, 15, 5)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=datetime.now(),
                Estado="PENDIENTE",
                Fecha_Programada=fecha
            )
            # El método del modelo solo devuelve la parte de fecha
            assert sesion.fecha_programada_legible() == "17/06/2025"
            sesion.Fecha_Programada = None
            assert sesion.fecha_programada_legible() == ""

    def test_hora_programada_legible(self, app):
        """Prueba el formateo de hora programada a formato HH:MM."""
        with app.app_context():
            fecha = datetime(2025, 6, 17, 15, 5)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=datetime.now(),
                Estado="PENDIENTE",
                Fecha_Programada=fecha
            )
            # Cuando hay fecha, devuelve la hora en formato HH:MM
            assert sesion.hora_programada_legible() == "15:05"

            # Cuando no hay fecha, devuelve cadena vacía
            sesion.Fecha_Programada = None
            assert sesion.hora_programada_legible() == ""


    def test_repr(self, app):
        """Prueba el método __repr__()."""
        with app.app_context():
            fecha = datetime(2025, 6, 17, 15, 5)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=datetime.now(),
                Estado="COMPLETADA",
                Fecha_Programada=fecha
            )
            esperado = (
                f"<Sesion Id={sesion.Id} Estado={sesion.Estado} "
                f"Fecha_Programada={sesion.Fecha_Programada}>"
            )
            assert repr(sesion) == esperado

    def test_to_dict(self, app):
        """Prueba la serialización a diccionario."""
        with app.app_context():
            fecha = datetime(2025, 6, 17, 15, 5)
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=datetime.now(),
                Estado="PENDIENTE",
                Fecha_Programada=fecha
            )
            data = sesion.to_dict()
            assert data["Paciente_Id"] == 1
            assert data["Profesional_Id"] == 2
            assert data["Estado"] == "PENDIENTE"
            # to_dict usa str(self.Fecha_Programada), así que comparamos con str(fecha)
            assert data["Fecha_Programada"] == str(fecha)
