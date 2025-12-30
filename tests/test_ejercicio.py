"""
Tests del modelo Ejercicio.
Prueba duración, tipos, videos y serialización.
"""

import pytest
from src.modelos.ejercicio import Ejercicio
from src.extensiones import db

class TestEjercicio:
    """Suite de tests para el modelo Ejercicio."""

    def test_duracion_legible_valor(self, app):
        """Prueba conversión de segundos a formato legible (Xm Ys)."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Apretar una pelota blanda",
                Descripcion="Con la mano, apretar suavemente una pelota blanda para estimular la movilidad.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=60
            )
            # 60 segundos = 1 min 0 seg
            assert ejercicio.duracion_legible() == "1 min 0 seg"

    def test_duracion_legible_none(self, app):
        """Prueba que duracion_legible() maneja valores None correctamente."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Movimientos de dedos",
                Descripcion="Mover lentamente los dedos de la mano uno a uno.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=None
            )
            assert ejercicio.duracion_legible() == "No especificada"

    def test_es_tipo(self, app):
        """Prueba comparación de tipo de ejercicio (case-insensitive)."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Flexión de tobillo asistida",
                Descripcion="Con ayuda, flexionar y extender el tobillo suavemente.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=30
            )
            assert ejercicio.es_tipo("rehabilitación") is True
            assert ejercicio.es_tipo("fuerza") is False

    def test_tiene_video(self, app):
        """Prueba detección de presencia de video."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Giro de cabeza lateral",
                Descripcion="Girar la cabeza suavemente hacia un lado y luego al otro, con apoyo si es necesario.",
                Tipo="Rehabilitación",
                Video="videos/cabeza.mp4",
                Duracion=45
            )
            assert ejercicio.tiene_video() is True
            ejercicio.Video = None
            assert ejercicio.tiene_video() is False

    def test_repr(self, app):
        """Prueba el método __repr__()."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Levantamiento de brazo con ayuda",
                Descripcion="Con ayuda, elevar el brazo lentamente hasta donde sea posible.",
                Tipo="Rehabilitación",
                Video=None,
                Duracion=20
            )
            esperado = f"<Ejercicio Id={ejercicio.Id} Nombre={ejercicio.Nombre}>"
            assert repr(ejercicio) == esperado

    def test_to_dict(self, app):
        """Prueba la serialización a diccionario."""
        with app.app_context():
            ejercicio = Ejercicio(
                Nombre="Rotación de muñeca",
                Descripcion="Rotar la muñeca en círculos pequeños, sentado o acostado.",
                Tipo="Rehabilitación",
                Video="videos/muneca.mp4",
                Duracion=15
            )
            data = ejercicio.to_dict()
            assert data["Nombre"] == "Rotación de muñeca"
            assert data["Descripcion"] == "Rotar la muñeca en círculos pequeños, sentado o acostado."
            assert data["Tipo"] == "Rehabilitación"
            assert data["Video"] == "videos/muneca.mp4"
            assert data["Duracion"] == 15
