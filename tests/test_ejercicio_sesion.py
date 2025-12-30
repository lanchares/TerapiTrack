"""
Tests del modelo Ejercicio_Sesion.
Prueba relaciones, restricciones UNIQUE y métodos auxiliares.
"""

import pytest
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.modelos.sesion import Sesion
from src.modelos.ejercicio import Ejercicio
from src.modelos.videoRespuesta import VideoRespuesta
from src.modelos.evaluacion import Evaluacion
from src.extensiones import db
from datetime import date

class TestEjercicioSesion:
    """Suite de tests para el modelo Ejercicio_Sesion."""

    def test_creacion_y_relaciones(self, app):
        """Prueba la creación y relaciones con Sesion y Ejercicio."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Flexión de codo",
                Descripcion="Flexionar y extender el codo suavemente.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=30
            )
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=date.today()
            )
            db.session.add_all([ejercicio, sesion])
            db.session.commit()
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=sesion.Id,
                Ejercicio_Id=ejercicio.Id
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            assert ejercicio_sesion.sesion.Id == sesion.Id
            assert ejercicio_sesion.ejercicio.Id == ejercicio.Id

    def test_unique_constraint(self, app):
        """Prueba la restricción UNIQUE (Sesion_Id, Ejercicio_Id)."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Rotación de tobillo",
                Descripcion="Girar el tobillo en círculos.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=20
            )
            sesion = Sesion(
                Paciente_Id=1,
                Profesional_Id=2,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=date.today()
            )
            db.session.add_all([ejercicio, sesion])
            db.session.commit()
            ejercicio_sesion1 = Ejercicio_Sesion(
                Sesion_Id=sesion.Id,
                Ejercicio_Id=ejercicio.Id
            )
            db.session.add(ejercicio_sesion1)
            db.session.commit()
            ejercicio_sesion2 = Ejercicio_Sesion(
                Sesion_Id=sesion.Id,
                Ejercicio_Id=ejercicio.Id
            )
            db.session.add(ejercicio_sesion2)
            with pytest.raises(Exception):
                db.session.commit()
                db.session.rollback()

    def test_tiene_video_respuesta(self, app):
        """Prueba el método tiene_video_respuesta()."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=1,
                Ejercicio_Id=1
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            assert ejercicio_sesion.tiene_video_respuesta() is False
            video = VideoRespuesta(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Ruta_Almacenamiento="videos/ej1.mp4",
                Fecha_Expiracion=date.today()
            )
            db.session.add(video)
            db.session.commit()
            db.session.refresh(ejercicio_sesion)
            assert ejercicio_sesion.tiene_video_respuesta() is True

    def test_tiene_evaluacion(self, app):
        """Prueba el método tiene_evaluacion()."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=1,
                Ejercicio_Id=1
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            assert ejercicio_sesion.tiene_evaluacion() is False
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Puntuacion=4,
                Comentarios="Bien hecho",
                Fecha_Evaluacion=date.today()
            )
            db.session.add(evaluacion)
            db.session.commit()
            db.session.refresh(ejercicio_sesion)
            assert ejercicio_sesion.tiene_evaluacion() is True

    def test_obtener_puntuacion(self, app):
        """Prueba el método obtener_puntuacion()."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=1,
                Ejercicio_Id=1
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            assert ejercicio_sesion.obtener_puntuacion() is None
            evaluacion = Evaluacion(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Puntuacion=5,
                Comentarios="Excelente",
                Fecha_Evaluacion=date.today()
            )
            db.session.add(evaluacion)
            db.session.commit()
            db.session.refresh(ejercicio_sesion)
            assert ejercicio_sesion.obtener_puntuacion() == 5

    def test_obtener_ruta_video(self, app):
        """Prueba el método obtener_ruta_video()."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=1,
                Ejercicio_Id=1
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            assert ejercicio_sesion.obtener_ruta_video() is None
            video = VideoRespuesta(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Ruta_Almacenamiento="videos/ej2.mp4",
                Fecha_Expiracion=date.today()
            )
            db.session.add(video)
            db.session.commit()
            db.session.refresh(ejercicio_sesion)
            assert ejercicio_sesion.obtener_ruta_video() == "videos/ej2.mp4"

    def test_repr(self, app):
        """Prueba el método __repr__()."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=10,
                Ejercicio_Id=20
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            esperado = f"<Ejercicio_Sesion Id={ejercicio_sesion.Id} Sesion_Id={ejercicio_sesion.Sesion_Id} Ejercicio_Id={ejercicio_sesion.Ejercicio_Id}>"
            assert repr(ejercicio_sesion) == esperado

    def test_to_dict(self, app):
        """Prueba la serialización a diccionario."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=5,
                Ejercicio_Id=15
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            data = ejercicio_sesion.to_dict()
            assert data["Sesion_Id"] == 5
            assert data["Ejercicio_Id"] == 15
            assert "Id" in data
