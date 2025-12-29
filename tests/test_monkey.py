# tests/test_monkey.py
import random
import string

import pytest

from src.extensiones import db
from src.modelos.profesional import Profesional


def _random_string(n=20):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


# --- fixtures locales para este archivo ---

@pytest.fixture
def admin_user(user_factory):
    # Admin sencillo para loguear en /admin
    return user_factory(
        Email="admin_monkey@example.com",
        Rol_Id=0,
        Estado=1,
        Nombre="AdminMonkey",
        Apellidos="User",
    )


@pytest.fixture
def login_admin(login_user_fixture, admin_user):
    return login_user_fixture(admin_user)


@pytest.fixture
def profesional_user(user_factory):
    # Profesional mínimo para las rutas de /profesional
    user = user_factory(
        Email="pro_monkey@example.com",
        Rol_Id=2,
        Estado=1,
        Nombre="ProMonkey",
        Apellidos="User",
    )
    # Crear registro en Profesional para que las vistas lo reconozcan
    prof = Profesional(
        Usuario_Id=user.Id,
        Especialidad="Fisio",
        Tipo_Profesional="TERAPEUTA",
    )
    db.session.add(prof)
    db.session.commit()
    return user


@pytest.fixture
def login_profesional(login_user_fixture, profesional_user):
    return login_user_fixture(profesional_user)


# --- monkey tests ---

def test_monkey_crear_usuario_inputs_raros(client, admin_user, login_admin):
    for _ in range(10):
        data = {
            "nombre": _random_string(50),
            "apellidos": _random_string(50),
            "email": f"{_random_string(5)}@example.com",
            "password": _random_string(30),
            "rol_id": str(random.choice([0, 1, 2, 999])),
        }
        resp = client.post("/admin/crear_usuario", data=data, follow_redirects=True)
        assert resp.status_code in (200, 302, 400, 403)


def test_monkey_profesional_ejercicios_search(client, profesional_user, login_profesional):
    for _ in range(10):
        query = _random_string(30)
        resp = client.get(f"/profesional/ejercicios?search={query}")
        assert resp.status_code == 200

'''Indica que has añadido:

- Un monkey test sobre creación de usuarios en admin con datos aleatorios y roles incluso inválidos.

- Un monkey test sobre el buscador de ejercicios del profesional con queries aleatorias.

Explica que el objetivo es comprobar robustez ante entradas inesperadas y que no se han detectado errores adicionales,
lo que refuerza la validez de las validaciones ya testadas con pruebas dirigidas.​'''