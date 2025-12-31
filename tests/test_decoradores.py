"""
Tests de decoradores de autorización.
Prueba admin_required, profesional_required y paciente_required.
"""

from src.controladores import decoradores
from werkzeug.exceptions import Forbidden
from unittest.mock import patch

class DummyUser:
    """Usuario ficticio para simular current_user en tests."""
    def __init__(self, authenticated, rol_id):
        self.is_authenticated = authenticated
        self.Rol_Id = rol_id
        self.Nombre = "Test"

def test_admin_required_no_autenticado(app):
    """Prueba que admin_required redirige a login si no está autenticado."""
    @app.route("/solo_admin_no_auth")
    @decoradores.admin_required
    def vista():
        return "OK"

    with app.test_request_context("/solo_admin_no_auth"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=False, rol_id=0),
        ):
            resp = vista()
            assert resp.status_code == 302
            assert "/login" in resp.location

def test_admin_required_no_admin_403(app):
    """Prueba que admin_required lanza 403 si no es administrador."""
    @app.route("/solo_admin_no_admin")
    @decoradores.admin_required
    def vista():
        return "OK"

    with app.test_request_context("/solo_admin_no_admin"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=True, rol_id=1),
        ):
            try:
                vista()
                assert False, "Debió lanzar 403"
            except Forbidden:
                pass

def test_admin_required_ok(app):
    """Prueba que admin_required permite acceso a administradores."""
    @app.route("/solo_admin_ok")
    @decoradores.admin_required
    def vista():
        return "OK"

    with app.test_request_context("/solo_admin_ok"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=True, rol_id=0),
        ):
            resp = vista()
            assert resp == "OK"

def test_profesional_required_ramas(app):
    """Prueba todas las ramas de profesional_required."""
    @app.route("/solo_prof")
    @decoradores.profesional_required
    def vista():
        return "P"

    # No autenticado -> redirect
    with app.test_request_context("/solo_prof"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=False, rol_id=2),
        ):
            resp = vista()
            assert resp.status_code == 302
            assert "/login" in resp.location

    # Rol incorrecto -> 403
    with app.test_request_context("/solo_prof"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=True, rol_id=1),
        ):
            try:
                vista()
                assert False, "Debió lanzar 403"
            except Forbidden:
                pass

    # Rol correcto -> OK
    with app.test_request_context("/solo_prof"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=True, rol_id=2),
        ):
            resp = vista()
            assert resp == "P"

def test_paciente_required_ramas(app):
    """Prueba todas las ramas de paciente_required."""
    @app.route("/solo_pac")
    @decoradores.paciente_required
    def vista():
        return "X"

    # No autenticado -> redirect
    with app.test_request_context("/solo_pac"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=False, rol_id=1),
        ):
            resp = vista()
            assert resp.status_code == 302
            assert "/login" in resp.location

    # Rol incorrecto -> 403
    with app.test_request_context("/solo_pac"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=True, rol_id=2),
        ):
            try:
                vista()
                assert False, "Debió lanzar 403"
            except Forbidden:
                pass

    # Rol correcto -> OK
    with app.test_request_context("/solo_pac"):
        with patch(
            "src.controladores.decoradores.current_user",
            DummyUser(authenticated=True, rol_id=1),
        ):
            resp = vista()
            assert resp == "X"
