import pytest
from flask import session

from src.controladores.auth_controlador import redirect_by_role
from src.extensiones import db
from src.modelos.usuario import Usuario


# ---------- redirect_by_role ----------

def test_redirect_by_role_admin(app):
    user = Usuario(Nombre="A", Apellidos="B", Email="a@a.com",
                   Rol_Id=0, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/admin" in resp.location


def test_redirect_by_role_profesional(app):
    user = Usuario(Nombre="A", Apellidos="B", Email="p@p.com",
                   Rol_Id=2, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/profesional" in resp.location


def test_redirect_by_role_paciente(app):
    user = Usuario(Nombre="A", Apellidos="B", Email="c@c.com",
                   Rol_Id=1, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/paciente" in resp.location


def test_redirect_by_role_desconocido_muestra_error(app, client):
    user = Usuario(Nombre="A", Apellidos="B", Email="x@x.com",
                   Rol_Id=99, Estado=1)
    user.set_contraseña("x")
    with app.test_request_context():
        resp = redirect_by_role(user)
        assert resp.status_code == 302
        assert "/login" in resp.location


# ---------- login ----------

def test_login_get_form(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"email" in resp.data.lower()


def test_login_redirige_si_autenticado(client, user_factory, login_user_fixture, app):
    # Usuario ya autenticado
    user = user_factory(Rol_Id=1, Email="p1@example.com")
    login_user_fixture(user)

    # Llamar a la vista /login: entra en el if current_user.is_authenticated
    resp = client.get("/login", follow_redirects=False)

    assert resp.status_code == 302
    assert "/paciente" in resp.location



def test_login_bloqueado_por_intentos(client):
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
    user = user_factory(Email="des@example.com", Estado=0)
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"desactivada" in resp.data.lower()


def test_login_contrasena_incorrecta(client, user_factory):
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
    user = user_factory(Email="pac@example.com", Rol_Id=1)
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/paciente" in resp.location


def test_login_admin_sesion_corta(client, user_factory):
    user = user_factory(Email="adm@example.com", Rol_Id=0)
    resp = client.post(
        "/login",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/admin" in resp.location


def test_login_next_param(client, user_factory):
    user = user_factory(Email="next@example.com", Rol_Id=1)
    resp = client.post(
        "/login?next=/ruta/protegida",
        data={"email": user.Email, "password": "password123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/ruta/protegida" in resp.location


# ---------- logout ----------

def test_logout_no_autenticado(client):
    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_logout_autenticado_limpia_sesion(client, user_factory, login_user_fixture, app):
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.location
    assert "Cache-Control" in resp.headers
    assert "no-cache" in resp.headers["Cache-Control"]


# ---------- cambiar_contrasena ----------

def test_cambiar_contrasena_get(client, user_factory, login_user_fixture, app):
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/cambiar_contrasena")
    assert resp.status_code == 200


def test_cambiar_contrasena_actual_incorrecta(client, user_factory, login_user_fixture, app):
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


# ---------- recuperar_contrasena ----------

def test_recuperar_contrasena_redirige_si_autenticado(client, user_factory, login_user_fixture, app):
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/recuperar_contrasena")
    assert resp.status_code == 302


def test_recuperar_contrasena_usuario_desactivado(client, user_factory):
    user = user_factory(Email="rec1@example.com", Estado=0)
    resp = client.post(
        "/recuperar_contrasena",
        data={"email": user.Email},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"desactivada" in resp.data.lower()


def test_recuperar_contrasena_usuario_activo(client, user_factory):
    user = user_factory(Email="rec2@example.com", Estado=1)
    resp = client.post(
        "/recuperar_contrasena",
        data={"email": user.Email},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login" in resp.location


def test_recuperar_contrasena_email_inexistente(client):
    resp = client.post(
        "/recuperar_contrasena",
        data={"email": "noexiste@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"instrucciones de recuperaci" in resp.data.lower()


# ---------- perfil ----------

def test_perfil_renderiza_con_usuario(client, user_factory, login_user_fixture, app):
    user = user_factory()
    login_user_fixture(user)
    resp = client.get("/perfil")
    assert resp.status_code == 200
    assert user.Nombre.encode() in resp.data
