"""
Configuración de fixtures de pytest para tests de TerapiTrack.
Define fixtures reutilizables para app, cliente, base de datos y autenticación.
"""

import pytest
from app import create_app
from src.extensiones import db
from src.modelos.usuario import Usuario
from flask_login import login_user


@pytest.fixture
def app():
    """
    Crea una instancia de la aplicación Flask para testing.
    
    Configura:
        - Base de datos en memoria SQLite
        - Modo testing activado
        - CSRF deshabilitado para facilitar tests
    
    Yields:
        Flask: Aplicación configurada para tests
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False  # para que los formularios funcionen en tests
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    """
    Proporciona un cliente de prueba para hacer peticiones HTTP.
    
    Args:
        app: Fixture de la aplicación Flask
        
    Returns:
        FlaskClient: Cliente de testing de Flask
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Proporciona un runner para comandos CLI de Flask.
    
    Args:
        app: Fixture de la aplicación Flask
        
    Returns:
        FlaskCliRunner: Runner de comandos CLI
    """
    return app.test_cli_runner()


@pytest.fixture
def user_factory(app):
    """
    Factory para crear usuarios de prueba en la base de datos.
    
    Args:
        app: Fixture de la aplicación Flask
        
    Returns:
        function: Función para crear usuarios con parámetros personalizados
        
    Ejemplo:
        user = user_factory(Nombre="Juan", Email="juan@test.com", Rol_Id=2)
    """
    def _make(**kwargs):
        data = {
            "Nombre": kwargs.get("Nombre", "Nombre"),
            "Apellidos": kwargs.get("Apellidos", "Apellidos"),
            "Email": kwargs.get("Email", "user@example.com"),
            "Rol_Id": kwargs.get("Rol_Id", 1),
            "Estado": kwargs.get("Estado", 1),
        }
        user = Usuario(**data)
        user.set_contraseña(kwargs.get("password", "password123"))
        db.session.add(user)
        db.session.commit()
        return user
    return _make


@pytest.fixture
def login_user_fixture(app):
    """
    Simula login de usuario para tests de vistas protegidas con @login_required.
    
    Args:
        app: Fixture de la aplicación Flask
        
    Returns:
        function: Función para marcar usuario como autenticado
    """
    def _login(user):
        with app.test_request_context():
            login_user(user)
        return user
    return _login
