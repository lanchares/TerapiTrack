"""
Tests del registro de blueprints.
Prueba que todos los blueprints se registran correctamente en la aplicación.
"""

from flask import Flask
from src.controladores import register_blueprints

def test_register_blueprints():
    """Prueba que register_blueprints() registra todos los blueprints."""
    # Crear una app nueva SIN blueprints
    app = Flask(__name__)
    app.secret_key = "test"

    # Ejecutar la función que queremos cubrir
    register_blueprints(app)

    # Comprobar que se han registrado todos los blueprints
    assert 'auth' in app.blueprints
    assert 'admin' in app.blueprints
    assert 'paciente' in app.blueprints
    assert 'profesional' in app.blueprints
