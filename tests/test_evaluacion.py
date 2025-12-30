"""
Tests del modelo Evaluacion.
Prueba restricciones de puntuación, métodos auxiliares y serialización.
"""

import pytest
from datetime import date
from src.modelos.evaluacion import Evaluacion
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.extensiones import db

class TestEvaluacion:
    """Suite de tests para el modelo Evaluacion."""

    def test_creacion_y_relacion(self, app):
        """Prueba la creación de evaluación y relación con Ejercicio_Sesion."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=1,
                Ejercicio_Id=1
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Puntuacion=4,
                Comentarios="Muy bien",
                Fecha_Evaluacion=date(2025, 6, 17)
            )
            db.session.add(evaluacion)
            db.session.commit()
            assert evaluacion.ejercicio_sesion.Id == ejercicio_sesion.Id
            assert evaluacion.Puntuacion == 4
            assert evaluacion.Comentarios == "Muy bien"
            assert evaluacion.Fecha_Evaluacion == date(2025, 6, 17)

    def test_check_constraint_puntuacion(self, app):
        """Prueba la restricción CHECK de Puntuacion (1-5)."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=2,
                Ejercicio_Id=2
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()

            # Puntuación fuera de rango inferior
            evaluacion1 = Evaluacion(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Puntuacion=0,
                Comentarios="Mal",
                Fecha_Evaluacion=date.today()
            )
            db.session.add(evaluacion1)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

            # Puntuación fuera de rango superior
            evaluacion2 = Evaluacion(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Puntuacion=6,
                Comentarios="Excelente",
                Fecha_Evaluacion=date.today()
            )
            db.session.add(evaluacion2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_es_aprobado(self, app):
        """Prueba el método es_aprobado() con diferentes mínimos."""
        with app.app_context():
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=3,
                Puntuacion=3,
                Comentarios="Aprobado",
                Fecha_Evaluacion=date.today()
            )
            assert evaluacion.es_aprobado() is True
            assert evaluacion.es_aprobado(minimo=4) is False

    def test_resumen(self, app):
        """Prueba el método resumen() con y sin comentarios."""
        with app.app_context():
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=4,
                Puntuacion=5,
                Comentarios="Excelente trabajo",
                Fecha_Evaluacion=date.today()
            )
            assert evaluacion.resumen() == "Puntuación: 5 - Excelente trabajo"
            evaluacion.Comentarios = None
            assert evaluacion.resumen() == "Puntuación: 5 - Sin comentarios"

    def test_repr(self, app):
        """Prueba el método __repr__()."""
        with app.app_context():
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=5,
                Puntuacion=2,
                Comentarios="Debe mejorar",
                Fecha_Evaluacion=date.today()
            )
            esperado = f"<Evaluacion Ejercicio_Sesion_Id={evaluacion.Ejercicio_Sesion_Id} Puntuacion={evaluacion.Puntuacion}>"
            assert repr(evaluacion) == esperado

    def test_to_dict(self, app):
        """Prueba la serialización a diccionario."""
        with app.app_context():
            fecha = date(2025, 6, 17)
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=6,
                Puntuacion=4,
                Comentarios="Correcto",
                Fecha_Evaluacion=fecha
            )
            data = evaluacion.to_dict()
            assert data["Ejercicio_Sesion_Id"] == 6
            assert data["Puntuacion"] == 4
            assert data["Comentarios"] == "Correcto"
            assert data["Fecha_Evaluacion"] == str(fecha)
