"""
Tests del controlador de paciente.
Prueba dashboard, sesiones, ejercicios, progreso y utilidades.
"""

import json
from datetime import datetime, timedelta

import pytest
import os

from src.extensiones import db
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.sesion import Sesion
from src.modelos.ejercicio import Ejercicio
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.modelos.evaluacion import Evaluacion
from src.controladores import paciente_controlador

# Fixtures específicos

@pytest.fixture
def paciente_user(user_factory):
    """Crea un usuario con rol paciente + registro en Paciente."""
    user = user_factory(Rol_Id=1, Email="paciente@example.com", Nombre="Pac", Apellidos="Test")
    pac = Paciente(
        Usuario_Id=user.Id,
        Fecha_Nacimiento=datetime(2000, 1, 1),
        Condicion_Medica="Cond",
        Notas="Notas",
    )
    db.session.add(pac)
    db.session.commit()
    return user

@pytest.fixture
def profesional_user(user_factory):
    """Crea un usuario profesional + registro en Profesional."""
    user = user_factory(Rol_Id=2, Email="prof@example.com", Nombre="Pro", Apellidos="Fesional")
    prof = Profesional(
        Usuario_Id=user.Id,
        Especialidad="Fisio",
        Tipo_Profesional="TERAPEUTA",
    )
    db.session.add(prof)
    db.session.commit()
    return user

@pytest.fixture
def login_paciente(login_user_fixture, paciente_user):
    """Loguea al paciente para tests de rutas protegidas."""
    return login_user_fixture(paciente_user)

# Tests de dashboard

def test_dashboard_paciente_sin_sesiones(client, paciente_user, login_paciente):
    """Prueba dashboard de paciente sin sesiones pendientes."""
    resp = client.get("/paciente/dashboard")
    assert resp.status_code == 200

def test_dashboard_paciente_con_sesion_futura(client, paciente_user, profesional_user, login_paciente):
    """Prueba dashboard con sesión futura programada."""
    sesion = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=2),
        Estado="PENDIENTE",
    )
    db.session.add(sesion)
    db.session.commit()

    resp = client.get("/paciente/dashboard")
    assert resp.status_code == 200
    
# Tests de mis_sesiones

def test_mis_sesiones_rango_tres_semanas(client, paciente_user, profesional_user, login_paciente):
    """Prueba que mis_sesiones muestra solo sesiones de las próximas 3 semanas."""
    # una sesión dentro del rango
    sesion1 = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=3),
        Estado="PENDIENTE",
    )
    # una sesión fuera del rango
    sesion2 = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(weeks=5),
        Estado="PENDIENTE",
    )
    db.session.add_all([sesion1, sesion2])
    db.session.commit()

    resp = client.get("/paciente/mis_sesiones")
    assert resp.status_code == 200
    assert sesion1.Fecha_Programada.strftime("%Y-%m-%d").encode() in resp.data
    assert sesion2.Fecha_Programada.strftime("%Y-%m-%d").encode() not in resp.data

# Tests de ejecutar_sesion

def test_ejecutar_sesion_ok(client, paciente_user, profesional_user, login_paciente):
    """Prueba ejecución exitosa de sesión con ejercicios asignados."""
    sesion = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=1),
        Estado="PENDIENTE",
    )
    db.session.add(sesion)
    db.session.commit()
    sesion_id = sesion.Id  

    ej = Ejercicio(
        Nombre="Sentadillas",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="video1.mp4",
        Duracion=30,
    )
    db.session.add(ej)
    db.session.commit()

    es = Ejercicio_Sesion(
        Sesion_Id=sesion_id,
        Ejercicio_Id=ej.Id,
    )
    db.session.add(es)
    db.session.commit()

    resp = client.get(f"/paciente/ejecutar_sesion/{sesion_id}")
    assert resp.status_code == 200
    assert b"Sentadillas" in resp.data

def test_ejecutar_sesion_otro_paciente_redirige_dashboard(client, paciente_user, profesional_user, user_factory, login_paciente):
    """Prueba que paciente no puede ejecutar sesión de otro paciente."""
    otro_pac = user_factory(Rol_Id=1, Email="otro@example.com")
    sesion = Sesion(
        Paciente_Id=otro_pac.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=1),
        Estado="PENDIENTE",
    )
    db.session.add(sesion)
    db.session.commit()

    resp = client.get(f"/paciente/ejecutar_sesion/{sesion.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"No tienes permisos para esta sesi" in resp.data

# Tests de ejercicios

def test_ejercicios_agrupa_y_cuenta(client, paciente_user, profesional_user, login_paciente, app):
    """Prueba agrupación de ejercicios únicos y conteo de asignaciones."""
    with app.app_context():
        ej1 = Ejercicio(
            Nombre="Puente",
            Descripcion="Desc",
            Tipo="Fuerza",
            Video="vid1.mp4",
            Duracion=20,
        )
        ej2 = Ejercicio(
            Nombre="Estiramiento",
            Descripcion="Desc2",
            Tipo="Movilidad",
            Video="vid2.mp4",
            Duracion=15,
        )
        db.session.add_all([ej1, ej2])
        db.session.commit()

        # dos sesiones con mismo ejercicio ej1, una con ej2
        for offset, ejercicio in [(1, ej1), (2, ej1), (3, ej2)]:
            sesion = Sesion(
                Paciente_Id=paciente_user.Id,
                Profesional_Id=profesional_user.Id,
                Fecha_Asignacion=datetime.now(),
                Fecha_Programada=datetime.now() + timedelta(days=offset),
                Estado="PENDIENTE",
            )
            db.session.add(sesion)
            db.session.commit()
            es = Ejercicio_Sesion(
                Sesion_Id=sesion.Id,
                Ejercicio_Id=ejercicio.Id,
            )
            db.session.add(es)
            db.session.commit()

    resp = client.get("/paciente/ejercicios")
    assert resp.status_code == 200
    assert b"Puente" in resp.data
    assert b"Estiramiento" in resp.data

# Tests de progreso

def _crear_evaluacion_completa(paciente_id, profesional_id, ejercicio, puntuacion, dias_offset):
    """Helper para crear Sesion, Ejercicio_Sesion y Evaluacion relacionados."""
    sesion = Sesion(
        Paciente_Id=paciente_id,
        Profesional_Id=profesional_id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=dias_offset),
        Estado="COMPLETADA",
    )
    db.session.add(sesion)
    db.session.commit()

    es = Ejercicio_Sesion(
        Sesion_Id=sesion.Id,
        Ejercicio_Id=ejercicio.Id,
    )
    db.session.add(es)
    db.session.commit()

    ev = Evaluacion(
        Ejercicio_Sesion_Id=es.Id,
        Puntuacion=puntuacion,
        Comentarios="Bien",
        Fecha_Evaluacion=datetime.now() + timedelta(days=dias_offset),
    )
    db.session.add(ev)
    db.session.commit()
    return ev

def test_progreso_sin_evaluaciones(client, paciente_user, login_paciente):
    """Prueba página de progreso sin evaluaciones previas."""
    resp = client.get("/paciente/progreso")
    assert resp.status_code == 200
    assert b"0" in resp.data  

def test_progreso_con_evaluaciones(client, paciente_user, profesional_user, login_paciente, app):
    """Prueba cálculo de estadísticas con evaluaciones existentes."""
    with app.app_context():
        ej = Ejercicio(
            Nombre="Equilibrio",
            Descripcion="Desc",
            Tipo="Equilibrio",
            Video="eq.mp4",
            Duracion=10,
        )
        db.session.add(ej)
        db.session.commit()

        _crear_evaluacion_completa(paciente_user.Id, profesional_user.Id, ej, 3, 1)
        _crear_evaluacion_completa(paciente_user.Id, profesional_user.Id, ej, 5, 2)
        _crear_evaluacion_completa(paciente_user.Id, profesional_user.Id, ej, 4, 3)

    resp = client.get("/paciente/progreso")
    assert resp.status_code == 200
    assert b"Equilibrio" in resp.data
    assert b"4.0" in resp.data or b"4," in resp.data

# Tests de ayuda y session_info

def test_ayuda(client, paciente_user, login_paciente):
    """Prueba acceso a página de ayuda."""
    resp = client.get("/paciente/ayuda")
    assert resp.status_code == 200


def test_session_info(
    client, paciente_user, login_paciente, monkeypatch
):
    """Prueba endpoint JSON con información de sesión."""
    resp = client.get("/paciente/session_info")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["usuario"] == "Pac"
    assert data["rol"] == "Paciente"
    assert data["mando_conectado"] is False

def test_get_video_path_usa_uploads_si_existe(app, tmp_path):
    """Prueba que get_video_path() detecta videos en uploads/ejercicios."""
    from src.controladores.paciente_controlador import get_video_path
    video_name = "demo.mp4"

    static_dir = tmp_path / "static"
    uploads_dir = static_dir / "uploads" / "ejercicios"
    uploads_dir.mkdir(parents=True)
    (uploads_dir / video_name).write_bytes(b"")

    with app.app_context():
        app.static_folder = str(static_dir)
        path = get_video_path(video_name)

    assert path == f"/static/uploads/ejercicios/{video_name}"

def test_get_video_path_usa_videos_si_no_hay_uploads(app, tmp_path):
    """Prueba que get_video_path() detecta videos en videos/ como fallback."""
    from src.controladores.paciente_controlador import get_video_path
    video_name = "demo2.mp4"

    static_dir = tmp_path / "static"
    videos_dir = static_dir / "videos"
    videos_dir.mkdir(parents=True)
    (videos_dir / video_name).write_bytes(b"")

    with app.app_context():
        app.static_folder = str(static_dir)
        path = get_video_path(video_name)

    assert path == f"/static/videos/{video_name}"