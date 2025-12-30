"""
Tests del modelo VideoRespuesta.
Prueba almacenamiento de videos, fechas de expiración y métodos auxiliares.
"""

import pytest
from datetime import date, timedelta
from src.modelos.videoRespuesta import VideoRespuesta
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.extensiones import db

class TestVideoRespuesta:
    """Suite de tests para el modelo VideoRespuesta."""

    def test_creacion_y_relacion(self, app):
        """Prueba la creación de video y relación con Ejercicio_Sesion."""
        with app.app_context():
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=1,
                Ejercicio_Id=1
            )
            db.session.add(ejercicio_sesion)
            db.session.commit()
            video = VideoRespuesta(
                Ejercicio_Sesion_Id=ejercicio_sesion.Id,
                Ruta_Almacenamiento="videos/rehab_paciente1.mp4",
                Fecha_Expiracion=date.today() + timedelta(days=7)
            )
            db.session.add(video)
            db.session.commit()
            assert video.ejercicio_sesion.Id == ejercicio_sesion.Id
            assert video.Ruta_Almacenamiento == "videos/rehab_paciente1.mp4"
            assert video.Fecha_Expiracion > date.today()

    def test_nombre_archivo(self, app):
        """Prueba la extracción del nombre de archivo desde la ruta."""
        with app.app_context():
            video = VideoRespuesta(
                Ejercicio_Sesion_Id=2,
                Ruta_Almacenamiento="videos/rehabilitacion/ejercicio2.mp4",
                Fecha_Expiracion=date.today()
            )
            assert video.nombre_archivo() == "ejercicio2.mp4"

    def test_repr(self, app):
        """Prueba el método __repr__()."""
        with app.app_context():
            video = VideoRespuesta(
                Ejercicio_Sesion_Id=3,
                Ruta_Almacenamiento="videos/ej3.mp4",
                Fecha_Expiracion=date.today()
            )
            esperado = f"<VideoRespuesta Ejercicio_Sesion_Id={video.Ejercicio_Sesion_Id}>"
            assert repr(video) == esperado

    def test_to_dict(self, app):
        """Prueba la serialización a diccionario."""
        with app.app_context():
            fecha = date(2025, 6, 17)
            video = VideoRespuesta(
                Ejercicio_Sesion_Id=4,
                Ruta_Almacenamiento="videos/ej4.mp4",
                Fecha_Expiracion=fecha
            )
            data = video.to_dict()
            assert data["Ejercicio_Sesion_Id"] == 4
            assert data["Ruta_Almacenamiento"] == "videos/ej4.mp4"
            assert data["Fecha_Expiracion"] == str(fecha)
