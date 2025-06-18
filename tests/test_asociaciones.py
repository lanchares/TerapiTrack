import pytest
from datetime import date, timedelta
from src.modelos.asociaciones import Paciente_Profesional, Ejercicio_Profesional
from src.extensiones import db

class TestPacienteProfesional:
    def test_creacion_y_dict(self, app):
        with app.app_context():
            hoy = date.today()
            asociacion = Paciente_Profesional(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=hoy
            )
            db.session.add(asociacion)
            db.session.commit()
            # Comprobar campos
            assert asociacion.Paciente_Id == 1
            assert asociacion.Profesional_Id == 2
            assert asociacion.Fecha_Asignacion == hoy
            # Comprobar to_dict
            data = asociacion.to_dict()
            assert data["Paciente_Id"] == 1
            assert data["Profesional_Id"] == 2
            assert data["Fecha_Asignacion"] == str(hoy)
            # Comprobar __repr__
            esperado = f"<PacienteProfesional Paciente_Id=1 Profesional_Id=2>"
            assert repr(asociacion) == esperado

    def test_fecha_asignacion_default(self, app):
        with app.app_context():
            asociacion = Paciente_Profesional(
                Paciente_Id=3,
                Profesional_Id=4
            )
            db.session.add(asociacion)
            db.session.commit()
            assert asociacion.Fecha_Asignacion == date.today()

class TestEjercicioProfesional:
    def test_creacion_y_dict(self, app):
        with app.app_context():
            asociacion = Ejercicio_Profesional(
                Profesional_Id=5,
                Ejercicio_Id=6
            )
            db.session.add(asociacion)
            db.session.commit()
            # Comprobar campos
            assert asociacion.Profesional_Id == 5
            assert asociacion.Ejercicio_Id == 6
            # Comprobar to_dict
            data = asociacion.to_dict()
            assert data["Profesional_Id"] == 5
            assert data["Ejercicio_Id"] == 6
            # Comprobar __repr__
            esperado = f"<EjercicioProfesional Usuario_Id=5 Ejercicio_Id=6>"
            assert repr(asociacion) == esperado
