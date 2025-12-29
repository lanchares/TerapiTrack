import json
from datetime import datetime, timedelta

import pytest

from src.extensiones import db
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.sesion import Sesion
from src.modelos.ejercicio import Ejercicio
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.modelos.evaluacion import Evaluacion
from src.controladores import paciente_controlador


# --------- helpers / fixtures específicos paciente ---------


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


# ---------------------- dashboard -------------------------


def test_dashboard_paciente_sin_sesiones(client, paciente_user, login_paciente):
    resp = client.get("/paciente/dashboard")
    assert resp.status_code == 200


def test_dashboard_paciente_con_sesion_futura(
    client, paciente_user, profesional_user, login_paciente
):
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
    


# ---------------------- mis_sesiones ----------------------


def test_mis_sesiones_rango_tres_semanas(
    client, paciente_user, profesional_user, login_paciente
):
    # una sesión dentro del rango
    sesion1 = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=3),
        Estado="PENDIENTE",
    )
    # una sesión fuera del rango (muy en el futuro)
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
    # debería aparecer la más cercana en el HTML (fecha programada)
    assert sesion1.Fecha_Programada.strftime("%Y-%m-%d").encode() in resp.data
    # la que está fuera de 3 semanas no debería estar
    assert sesion2.Fecha_Programada.strftime("%Y-%m-%d").encode() not in resp.data


# -------------------- ejecutar_sesion ---------------------


def test_ejecutar_sesion_ok(
    client, paciente_user, profesional_user, login_paciente
):
    # crear sesión y ejercicios asociados directamente (ya hay app_context por el client)
    sesion = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=1),
        Estado="PENDIENTE",
    )
    db.session.add(sesion)
    db.session.commit()
    sesion_id = sesion.Id  # guardar el id antes de que se “desenganche”

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



def test_ejecutar_sesion_otro_paciente_redirige_dashboard(
    client, paciente_user, profesional_user, user_factory, login_paciente
):
    # sesión asignada a otro paciente
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


# ------------------ get_controller_state ------------------


def test_get_controller_state_sin_mando(client, paciente_user, login_paciente, monkeypatch):
    # asegurar mando None
    monkeypatch.setattr(paciente_controlador, "snes_controller", None)
    resp = client.get("/paciente/get_controller_state")
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert data["error"] == "Mando no conectado"


class DummyController:
    """Simula un mando SNES simple."""

    def __init__(self, buttons=None, axes=None):
        self._buttons = buttons or {0: 0, 1: 1, 2: 0, 3: 0}
        self._axes = axes or {0: 0.6, 1: -0.7}

    def get_button(self, idx):
        return self._buttons.get(idx, 0)

    def get_numaxes(self):
        return len(self._axes)

    def get_axis(self, idx):
        return self._axes.get(idx, 0.0)


def test_get_controller_state_con_mando(
    client, paciente_user, login_paciente, monkeypatch
):
    dummy = DummyController()
    monkeypatch.setattr(paciente_controlador, "snes_controller", dummy)
    # pygame.event.pump se llama pero no necesitamos que haga nada
    resp = client.get("/paciente/get_controller_state")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["A"] is True
    # por ejes simulados: right y up deberían estar activos
    assert data["right"] is True
    assert data["up"] is True

def test_get_controller_state_error_lectura(
    client, paciente_user, login_paciente, monkeypatch
):
    dummy = DummyController()
    monkeypatch.setattr(paciente_controlador, "snes_controller", dummy)

    # Hacemos que pygame.event.pump lance una excepción
    def fake_pump():
        raise Exception("lectura fallida")

    import pygame
    monkeypatch.setattr(pygame.event, "pump", fake_pump)

    resp = client.get("/paciente/get_controller_state")
    assert resp.status_code == 500
    data = json.loads(resp.data)
    assert "Error leyendo mando" in data["error"]


# --------------------- reconectar_mando -------------------


def test_reconectar_mando_ok(
    client, paciente_user, login_paciente, monkeypatch
):
    # simular que init_snes_controller deja un mando conectado
    def fake_init():
        paciente_controlador.snes_controller = DummyController()

    monkeypatch.setattr(paciente_controlador, "init_snes_controller", fake_init)

    resp = client.get("/paciente/reconectar_mando")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["conectado"] is True


def test_reconectar_mando_sin_mando(
    client, paciente_user, login_paciente, monkeypatch
):
    def fake_init():
        paciente_controlador.snes_controller = None

    monkeypatch.setattr(paciente_controlador, "init_snes_controller", fake_init)

    resp = client.get("/paciente/reconectar_mando")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["conectado"] is False


# ------------------------ ejercicios ----------------------


def test_ejercicios_agrupa_y_cuenta(
    client, paciente_user, profesional_user, login_paciente, app
):
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
    # deben aparecer los nombres de los dos ejercicios
    assert b"Puente" in resp.data
    assert b"Estiramiento" in resp.data


# ------------------------- progreso -----------------------


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


def test_progreso_sin_evaluaciones(
    client, paciente_user, login_paciente
):
    resp = client.get("/paciente/progreso")
    assert resp.status_code == 200
    # stats sin evaluaciones
    assert b"0" in resp.data  # al menos algún cero de estadísticas


def test_progreso_con_evaluaciones(
    client, paciente_user, profesional_user, login_paciente, app
):
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

        # tres evaluaciones en sesiones diferentes
        _crear_evaluacion_completa(paciente_user.Id, profesional_user.Id, ej, 3, 1)
        _crear_evaluacion_completa(paciente_user.Id, profesional_user.Id, ej, 5, 2)
        _crear_evaluacion_completa(paciente_user.Id, profesional_user.Id, ej, 4, 3)

    resp = client.get("/paciente/progreso")
    assert resp.status_code == 200
    # comprobar que aparece el nombre del ejercicio
    assert b"Equilibrio" in resp.data
    # se puede asumir que el promedio 4.0 aparecerá en algún lado
    assert b"4.0" in resp.data or b"4," in resp.data  # según formato


# ---------------------- ayuda / session_info --------------


def test_ayuda(client, paciente_user, login_paciente):
    resp = client.get("/paciente/ayuda")
    assert resp.status_code == 200


def test_session_info(
    client, paciente_user, login_paciente, monkeypatch
):
    # asegurar valor conocido de snes_controller
    monkeypatch.setattr(paciente_controlador, "snes_controller", None)

    resp = client.get("/paciente/session_info")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["usuario"] == "Pac"
    assert data["rol"] == "Paciente"
    assert data["mando_conectado"] is False
