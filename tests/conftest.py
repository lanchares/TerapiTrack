import pytest
from app import create_app
from src.extensiones import db
from src.modelos.usuario import Usuario
from flask_login import login_user


@pytest.fixture
def app():
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
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def user_factory(app):
    """Crea y guarda usuarios en la BD para los tests."""
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
    """Marca un usuario como autenticado para vistas con @login_required."""
    def _login(user):
        with app.test_request_context():
            login_user(user)
        return user
    return _login
