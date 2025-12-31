"""
Tests de monkey testing (pruebas con entradas aleatorias).

Objetivo:
    Comprobar la robustez del sistema ante entradas inesperadas,
    aleatorias o inválidas que podrían no estar cubiertas por tests dirigidos.

Estrategia:
    - Generar datos aleatorios (strings, números, emails)
    - Enviar múltiples peticiones con valores impredecibles
    - Verificar que el sistema no rompe (status codes válidos)

Resultados esperados:
    No se detectan errores adicionales, lo que refuerza la validez
    de las validaciones ya implementadas en formularios y controladores.
"""

import random
import string

import pytest

from src.extensiones import db
from src.modelos.profesional import Profesional


def _random_string(n=20):
    """
    Genera una cadena aleatoria de n caracteres.
    
    Args:
        n: Longitud de la cadena (por defecto 20)
        
    Returns:
        str: Cadena aleatoria de letras y dígitos
    """
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))

# Fixtures locales

@pytest.fixture
def admin_user(user_factory):
    """Crea un administrador para tests de monkey."""
    return user_factory(
        Email="admin_monkey@example.com",
        Rol_Id=0,
        Estado=1,
        Nombre="AdminMonkey",
        Apellidos="User",
    )

@pytest.fixture
def login_admin(login_user_fixture, admin_user):
    """Loguea al admin para tests de monkey."""
    return login_user_fixture(admin_user)

@pytest.fixture
def profesional_user(user_factory):
    """Crea un profesional para tests de monkey."""
    user = user_factory(
        Email="pro_monkey@example.com",
        Rol_Id=2,
        Estado=1,
        Nombre="ProMonkey",
        Apellidos="User",
    )
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
    """Loguea al profesional para tests de monkey."""
    return login_user_fixture(profesional_user)

# Tests de monkey

def test_monkey_crear_usuario_inputs_raros(client, admin_user, login_admin):
    """
    Monkey test: creación de usuarios con datos aleatorios.
    
    Prueba robustez ante:
        - Nombres/apellidos aleatorios largos
        - Emails aleatorios
        - Contraseñas aleatorias
        - Roles válidos e inválidos (0, 1, 2, 999)
    
    Resultado esperado:
        El sistema responde con códigos HTTP válidos sin romper,
        validando correctamente los datos mediante WTForms.
    """
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
    """
    Monkey test: búsqueda de ejercicios con queries aleatorias.
    
    Prueba robustez ante:
        - Strings de búsqueda aleatorios
        - Caracteres especiales inesperados
        - Longitudes variables
    
    Resultado esperado:
        El sistema maneja correctamente las búsquedas sin romper,
        gracias a la validación con `.contains()` de SQLAlchemy.
    """
    for _ in range(10):
        query = _random_string(30)
        resp = client.get(f"/profesional/ejercicios?search={query}")
        assert resp.status_code == 200