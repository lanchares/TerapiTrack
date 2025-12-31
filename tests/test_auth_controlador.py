"""
Tests del controlador de autenticación.
Prueba login, logout, cambio de contraseña, recuperación y redirección por roles.
"""

import pytest
from flask import session

from src.controladores.auth_controlador import redirect_by_role
from src.extensiones import db
from src.modelos.usuario import Usuario

# Tests de redirect_by_role

def test_redirect_by_role_admin(app):
    """Prueba redirección de administrador al dashboard de admin."""
    user = Usuario(Nombre="A", Apellidos="B", Email="a@a.com",
                   Rol_Id=0, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/admin" in resp.location

def test_redirect_by_role_profesional(app):
    """Prueba redirección de profesional a su dashboard."""
    user = Usuario(Nombre="A", Apellidos="B", Email="p@p.com",
                   Rol_Id=2, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/profesional" in resp.location

def test_redirect_by_role_paciente(app):
    """Prueba redirección de paciente a su dashboard."""
    user = Usuario(Nombre="A", Apellidos="B", Email="c@c.com",
                   Rol_Id=1, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/paciente" in resp.location

def test_redirect_by_role_desconocido_muestra_error(app, client):
    """Prueba que rol desconocido redirige a login con error."""
    user = Usuario(Nombre="A", Apellidos="B", Email="x@x.com",
                   Rol_Id=99, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/login" in resp.location

# Tests de login

def test_login_get_form(client):
    """Prueba acceso al formulario de login."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"email" in resp.data.lower()

def test_login_redirige_si_autenticado(client, user_factory, login_user_fixture, app):
    """Prueba que usuario autenticado es redirigido a su dashboard."""
    user = user_factory(Rol_Id=1, Email="p1@example.com")
    login_user_fixture(user)

    resp = client.get("/login", follow_redirects=False)

    assert resp.status_code == 302
    assert "/paciente" in resp.location



def test_login_bloqueado_por_intentos(client):
    """Prueba protección contra fuerza bruta (5 intentos fallidos)."""
    with client.session_transaction() as s:
        s["login_attempts_127.0.0.1"] = 5
    resp = client.post(
        "/login",
        data={"email": "x@y.com", "password": "bad"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"demasiados intentos fallidos" in resp.data.lower()

def test_login_usuario_no_existe_incrementa_intentos(client):
    """Prueba que intento con usuario inexistente incrementa contador."""
    resp = client.post(
        "/login",
        data={"email": "no@no.com", "password": "x"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with client.session_transaction() as s:
        assert s.get("login_attempts_127.0.0.1") == 1

def test_login_usuario_desactivado(client, user_factory):
    """Prueba que login con usuario desactivado muestra error."""
    user = user_factory(Email="des@example.com", Estado=0)
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"desactivada" in resp.data.lower()

def test_login_contrasena_incorrecta(client, user_factory):
    """Prueba que contraseña incorrecta incrementa intentos fallidos."""
    user = user_factory(Email="u1@example.com")
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "mala"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with client.session_transaction() as s:
        assert s.get("login_attempts_127.0.0.1") == 1
    assert b"credenciales incorrectas" in resp.data.lower()

def test_login_paciente_sesion_larga(client, user_factory):
    """Prueba que pacientes reciben sesión persistente de 30 días."""
    user = user_factory(Email="pac@example.com", Rol_Id=1)
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/paciente" in resp.location

def test_login_admin_sesion_corta(client, user_factory):
    """Prueba que admin/profesional reciben sesión temporal de 8 horas."""
    user = user_factory(Email="adm@example.com", Rol_Id=0)
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/admin" in resp.location

def test_login_next_param(client, user_factory):
    """Prueba redirección a página solicitada (parámetro next)."""
    user = user_factory(Email="next@example.com", Rol_Id=1)
    resp = client.post(
        "/login?next=/ruta/protegida",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/ruta/protegida" in resp.location

# Tests de logout

def test_logout_no_autenticado(client):
    """Prueba logout sin estar autenticado redirige a login."""
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_logout_autenticado_limpia_sesion(client, user_factory, login_user_fixture, app):
    """Prueba que logout limpia sesión y cookies correctamente."""
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.location
    assert "Cache-Control" in resp.headers
    assert "no-cache" in resp.headers["Cache-Control"]

# Tests de cambiar_contrasena

def test_cambiar_contrasena_get(client, user_factory, login_user_fixture, app):
    """Prueba acceso al formulario de cambio de contraseña."""
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/cambiar_contrasena")
    assert resp.status_code == 200


def test_cambiar_contrasena_actual_incorrecta(client, user_factory, login_user_fixture, app):
    """Prueba que contraseña actual incorrecta muestra error."""
    user = user_factory()
    login_user_fixture(user)
    resp = client.post(
        "/cambiar_contrasena",
        data={
            "contrasena_actual": "mala",
            "nueva_contrasena": "nueva1234",
            "confirmar_contrasena": "nueva1234",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"incorrecta" in resp.data.lower()

def test_cambiar_contrasena_ok(client, user_factory, login_user_fixture, app):
    """Prueba cambio exitoso de contraseña."""
    user = user_factory()
    login_user_fixture(user)
    resp = client.post(
        "/cambiar_contrasena",
        data={
            "contrasena_actual": "password123",
            "nueva_contrasena": "otra1234",
            "confirmar_contrasena": "otra1234",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/perfil" in resp.location

# Tests de recuperar_contrasena

def test_recuperar_contrasena_redirige_si_autenticado(client, user_factory, login_user_fixture, app):
    """Prueba que usuario autenticado es redirigido al hacer recuperación."""
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/recuperar_contrasena")
    assert resp.status_code == 302

def test_recuperar_contrasena_usuario_desactivado(client, user_factory):
    """Prueba que usuario desactivado no puede recuperar contraseña."""
    user = user_factory(Email="rec1@example.com", Estado=0)
    resp = client.post(
        "/recuperar_contrasena",
        data={"email": user.Email},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"desactivada" in resp.data.lower()

def test_recuperar_contrasena_usuario_activo(client, user_factory):
    """Prueba envío de instrucciones de recuperación (simulado)."""
    user = user_factory(Email="rec2@example.com", Estado=1)
    resp = client.post(
        "/recuperar_contrasena",
        data={"email": user.Email},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login" in resp.location

def test_recuperar_contrasena_email_inexistente(client):
    """Prueba que email inexistente muestra mensaje genérico (seguridad)."""
    resp = client.post(
        "/recuperar_contrasena",
        data={"email": "noexiste@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"instrucciones de recuperaci" in resp.data.lower()

# Tests de perfil

def test_perfil_renderiza_con_usuario(client, user_factory, login_user_fixture, app):
    """Prueba visualización del perfil del usuario."""
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/perfil")
    assert resp.status_code == 200
    assert user.Nombre.encode() in resp.data