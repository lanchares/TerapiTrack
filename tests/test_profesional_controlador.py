import io
import json
from datetime import datetime, timedelta

import pytest
import time
from sqlalchemy.exc import IntegrityError

from src.extensiones import db
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.sesion import Sesion
from src.modelos.ejercicio import Ejercicio
from src.modelos.ejercicio_sesion import Ejercicio_Sesion
from src.modelos.evaluacion import Evaluacion
from src.modelos.videoRespuesta import VideoRespuesta
from src.modelos.asociaciones import Paciente_Profesional, Ejercicio_Profesional
from src.controladores import profesional_controlador
from src.config import Config


# --------- helpers / fixtures específicos profesional ---------


@pytest.fixture
def profesional_user(user_factory):
    """Crea un usuario profesional + registro en Profesional."""
    user = user_factory(
        Rol_Id=2,
        Email="pro@example.com",
        Nombre="Pro",
        Apellidos="Fesional",
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
    """Loguea al profesional para tests de rutas protegidas."""
    return login_user_fixture(profesional_user)


@pytest.fixture
def paciente_user(user_factory):
    """Crea un usuario paciente + registro en Paciente."""
    user = user_factory(
        Rol_Id=1,
        Email="pac@example.com",
        Nombre="Pac",
        Apellidos="Test",
    )
    pac = Paciente(
        Usuario_Id=user.Id,
        Fecha_Nacimiento=datetime(2000, 1, 1),
        Condicion_Medica="Cond",
        Notas="Notas",
    )
    db.session.add(pac)
    db.session.commit()
    return user


# ---------------------- dashboard -------------------------


def test_dashboard_ok(client, profesional_user, login_profesional, paciente_user):
    # vincular un paciente y crear una sesión pendiente y una completada con video sin evaluar
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    sesion_pend = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=1),
        Estado="PENDIENTE",
    )
    db.session.add(sesion_pend)
    db.session.commit()

    sesion_comp = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() - timedelta(days=1),
        Estado="COMPLETADA",
    )
    db.session.add(sesion_comp)
    db.session.commit()

    ej = Ejercicio(
        Nombre="Puente",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()

    es = Ejercicio_Sesion(
        Sesion_Id=sesion_comp.Id,
        Ejercicio_Id=ej.Id,
    )
    db.session.add(es)
    db.session.commit()

    vr = VideoRespuesta(
        Ejercicio_Sesion_Id=es.Id,
        Ruta_Almacenamiento="resp.webm",
        Fecha_Expiracion=datetime.now() + timedelta(days=30),
    )
    db.session.add(vr)
    db.session.commit()

    resp = client.get("/profesional/dashboard")
    assert resp.status_code == 200


def test_dashboard_sin_profesional_redirige(client, user_factory, login_user_fixture):
    # usuario sin registro en Profesional
    user = user_factory(Rol_Id=2, Email="sinprof@example.com")
    login_user_fixture(user)
    resp = client.get("/profesional/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.location



# ------------------- gestión de pacientes -----------------


def test_listar_pacientes_filtrado_basico(
    client, profesional_user, paciente_user, login_profesional
):
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    resp = client.get("/profesional/pacientes")
    assert resp.status_code == 200
    assert b"Pac Test" in resp.data

    # filtro por search
    resp2 = client.get("/profesional/pacientes?search=Pac")
    assert resp2.status_code == 200
    assert b"Pac Test" in resp2.data

    # filtro por condición
    resp3 = client.get("/profesional/pacientes?condicion=Cond")
    assert resp3.status_code == 200
    assert b"Pac Test" in resp3.data

    # filtro por edad con rango inválido no debe romper
    resp4 = client.get("/profesional/pacientes?edad=x-y")
    assert resp4.status_code == 200


def test_listar_pacientes_filtrado_por_edad_valida(
    client, profesional_user, paciente_user, login_profesional
):
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    # Rango amplio que incluye la edad actual (~24-25 años según fecha de nacimiento)
    resp = client.get("/profesional/pacientes?edad=20-40")
    assert resp.status_code == 200
    assert b"Pac Test" in resp.data


# ----------------- biblioteca de ejercicios ---------------


def test_listar_ejercicios_filtros(
    client, profesional_user, login_profesional
):
    ej1 = Ejercicio(
        Nombre="Puente",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="v1.mp4",
        Duracion=10,
    )
    ej2 = Ejercicio(
        Nombre="Estiramiento hombro",
        Descripcion="Desc2",
        Tipo="Movilidad",
        Video="v2.mp4",
        Duracion=15,
    )
    db.session.add_all([ej1, ej2])
    db.session.commit()

    resp = client.get("/profesional/ejercicios")
    assert resp.status_code == 200
    assert b"Puente" in resp.data and b"Estiramiento" in resp.data

    resp_tipo = client.get("/profesional/ejercicios?tipo=Fuerza")
    assert resp_tipo.status_code == 200
    assert b"Puente" in resp_tipo.data and b"Estiramiento" not in resp_tipo.data

    resp_search = client.get("/profesional/ejercicios?search=hombro")
    assert resp_search.status_code == 200
    assert b"Estiramiento" in resp_search.data

def test_crear_ejercicio_get_muestra_form(
    client, profesional_user, login_profesional
):
    resp = client.get("/profesional/ejercicios/crear")
    assert resp.status_code == 200
    assert b"Crear" in resp.data or b"Nombre" in resp.data


def test_crear_ejercicio_ok(
    client, profesional_user, login_profesional, monkeypatch, tmp_path, app
):
    # configurar UPLOAD_FOLDER a un directorio temporal
    with app.app_context():
        app.config["UPLOAD_FOLDER"] = str(tmp_path)

    # simular archivo subido
    data = {
        "nombre": "NuevoEj",
        "descripcion": "Desc",
        "tipo": "Fuerza",
        "video": (io.BytesIO(b"fake video"), "test.mp4"),
    }

    resp = client.post(
        "/profesional/ejercicios/crear",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    ej = Ejercicio.query.filter_by(Nombre="NuevoEj").first()
    assert ej is not None
    assoc = Ejercicio_Profesional.query.filter_by(
        Profesional_Id=profesional_user.Id, Ejercicio_Id=ej.Id
    ).first()
    assert assoc is not None

# ------------------- creación de ejercicios -----------------

def test_crear_ejercicio_calcula_duracion(client, login_profesional, monkeypatch):
    # Simular VideoFileClip para controlar la duración
    class DummyClip:
        def __init__(self, path):
            self.duration = 12  # segundos

        def close(self):
            pass

    monkeypatch.setattr(
        profesional_controlador, "VideoFileClip", DummyClip, raising=True
    )

    # Fichero de vídeo “fake” en memoria
    video_bytes = io.BytesIO(b"fake-video-content")
    video_bytes.name = "test.mp4"

    data = {
        "nombre": "Ejercicio test",
        "descripcion": "Desc",
        "tipo": "MOVILIDAD",
        "video": (video_bytes, "test.mp4"),
    }

    resp = client.post(
        "/profesional/ejercicios/crear",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 302  # redirección tras crear

    ejercicio = Ejercicio.query.order_by(Ejercicio.Id.desc()).first()
    assert ejercicio is not None
    assert ejercicio.Duracion == 12

# ------------------- creación de sesiones -----------------


def _crear_ejercicios_para_profesional(profesional_id):
    ej1 = Ejercicio(
        Nombre="Puente",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="v1.mp4",
        Duracion=10,
    )
    ej2 = Ejercicio(
        Nombre="Estiramiento",
        Descripcion="Desc2",
        Tipo="Movilidad",
        Video="v2.mp4",
        Duracion=15,
    )
    db.session.add_all([ej1, ej2])
    db.session.commit()
    db.session.add_all(
        [
            Ejercicio_Profesional(Profesional_Id=profesional_id, Ejercicio_Id=ej1.Id),
            Ejercicio_Profesional(Profesional_Id=profesional_id, Ejercicio_Id=ej2.Id),
        ]
    )
    db.session.commit()
    return ej1, ej2


def test_crear_sesion_get_muestra_form(
    client, profesional_user, paciente_user, login_profesional
):
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    _crear_ejercicios_para_profesional(profesional_user.Id)

    resp = client.get("/profesional/sesiones/crear")
    assert resp.status_code == 200
    assert b"Crear Sesi" in resp.data


def test_crear_sesion_preseleccion_paciente(
    client, profesional_user, paciente_user, login_profesional
):
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    _crear_ejercicios_para_profesional(profesional_user.Id)

    resp = client.get(f"/profesional/sesiones/crear?paciente_id={paciente_user.Id}")
    assert resp.status_code == 200


def test_crear_sesion_post_ok(
    client, profesional_user, paciente_user, login_profesional
):
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    ej1, ej2 = _crear_ejercicios_para_profesional(profesional_user.Id)

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    data = {
        "paciente_id": str(paciente_user.Id),
        "fecha_programada": fecha,
        "ejercicios": [str(ej1.Id), str(ej2.Id)],
    }

    resp = client.post(
        "/profesional/sesiones/crear",
        data=data,
        follow_redirects=False,
    )
    assert resp.status_code == 302
    ses = Sesion.query.filter_by(Paciente_Id=paciente_user.Id).first()
    assert ses is not None
    es_rel = Ejercicio_Sesion.query.filter_by(Sesion_Id=ses.Id).all()
    assert len(es_rel) == 2


# ------------------- listar y ver sesiones ----------------


def test_listar_sesiones_con_estados(
    client, profesional_user, paciente_user, login_profesional
):
    # crear sesiones en distintos estados
    ses_pend = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=1),
        Estado="PENDIENTE",
    )
    ses_comp = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() - timedelta(days=1),
        Estado="COMPLETADA",
    )
    db.session.add_all([ses_pend, ses_comp])
    db.session.commit()

    # completar con ejercicios+video+evaluación solo en ses_comp
    ej = Ejercicio(
        Nombre="Puente",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="v1.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses_comp.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()
    vr = VideoRespuesta(
        Ejercicio_Sesion_Id=es.Id,
        Ruta_Almacenamiento="resp.webm",
        Fecha_Expiracion=datetime.now() + timedelta(days=30),
    )
    db.session.add(vr)
    db.session.commit()
    ev = Evaluacion(
        Ejercicio_Sesion_Id=es.Id,
        Puntuacion=4,
        Comentarios="Bien",
        Fecha_Evaluacion=datetime.now(),
    )
    db.session.add(ev)
    db.session.commit()

    resp = client.get("/profesional/sesiones")
    assert resp.status_code == 200

    # filtros de estado y paciente
    resp2 = client.get("/profesional/sesiones?estado=PENDIENTE")
    assert resp2.status_code == 200

    resp3 = client.get(f"/profesional/sesiones?paciente={paciente_user.Id}")
    assert resp3.status_code == 200

    # filtros de fechas (incluye manejo de formato inválido)
    hoy = datetime.now().strftime("%Y-%m-%d")
    resp4 = client.get(f"/profesional/sesiones?fecha_desde={hoy}")
    assert resp4.status_code == 200
    resp5 = client.get("/profesional/sesiones?fecha_desde=xxxx")
    assert resp5.status_code == 200


def test_listar_sesiones_estados_evaluacion_varios(
    client, profesional_user, paciente_user, login_profesional
):
    # 1) COMPLETADA sin videos -> NO_EVALUABLE
    ses_sin_video = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() - timedelta(days=1),
        Estado="COMPLETADA",
    )

    # 2) COMPLETADA con video pero sin evaluación -> SIN_EVALUAR
    ses_sin_eval = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() - timedelta(days=2),
        Estado="COMPLETADA",
    )

    # 3) COMPLETADA con dos videos y solo una evaluación -> PARCIALMENTE_EVALUADA
    ses_parcial = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() - timedelta(days=3),
        Estado="COMPLETADA",
    )

    db.session.add_all([ses_sin_video, ses_sin_eval, ses_parcial])
    db.session.commit()

    # ejercicios base
    ej1 = Ejercicio(
        Nombre="EvalTest1",
        Descripcion="Desc",
        Tipo="Test",
        Video="v1.mp4",
        Duracion=10,
    )
    ej2 = Ejercicio(
        Nombre="EvalTest2",
        Descripcion="Desc2",
        Tipo="Test",
        Video="v2.mp4",
        Duracion=15,
    )
    db.session.add_all([ej1, ej2])
    db.session.commit()

    # ses_sin_eval: 1 ejercicio + video, sin evaluación
    es1 = Ejercicio_Sesion(Sesion_Id=ses_sin_eval.Id, Ejercicio_Id=ej1.Id)
    db.session.add(es1)
    db.session.commit()
    vr1 = VideoRespuesta(
        Ejercicio_Sesion_Id=es1.Id,
        Ruta_Almacenamiento="v1.webm",
        Fecha_Expiracion=datetime.now() + timedelta(days=30),
    )
    db.session.add(vr1)

    # ses_parcial: 2 ejercicios con video, solo 1 evaluado
    es2 = Ejercicio_Sesion(Sesion_Id=ses_parcial.Id, Ejercicio_Id=ej1.Id)
    es3 = Ejercicio_Sesion(Sesion_Id=ses_parcial.Id, Ejercicio_Id=ej2.Id)
    db.session.add_all([es2, es3])
    db.session.commit()

    vr2 = VideoRespuesta(
        Ejercicio_Sesion_Id=es2.Id,
        Ruta_Almacenamiento="v2.webm",
        Fecha_Expiracion=datetime.now() + timedelta(days=30),
    )
    vr3 = VideoRespuesta(
        Ejercicio_Sesion_Id=es3.Id,
        Ruta_Almacenamiento="v3.webm",
        Fecha_Expiracion=datetime.now() + timedelta(days=30),
    )
    db.session.add_all([vr2, vr3])
    db.session.commit()

    # solo una evaluación (parcialmente evaluada)
    ev_parcial = Evaluacion(
        Ejercicio_Sesion_Id=es2.Id,
        Puntuacion=3,
        Comentarios="Parcial",
        Fecha_Evaluacion=datetime.now(),
    )
    db.session.add(ev_parcial)
    db.session.commit()

    resp = client.get("/profesional/sesiones")
    assert resp.status_code == 200

def test_listar_sesiones_filtra_fecha_hasta(
    client, profesional_user, paciente_user, login_profesional
):
    # Una sesión dentro del rango y otra fuera por fecha_hasta
    ses_in = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),  # hoy
        Estado="PENDIENTE",
    )
    ses_out = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now() + timedelta(days=10),
        Estado="PENDIENTE",
    )
    db.session.add_all([ses_in, ses_out])
    db.session.commit()

    hoy = datetime.now().strftime("%Y-%m-%d")
    resp = client.get(f"/profesional/sesiones?fecha_hasta={hoy}")
    assert resp.status_code == 200
    assert ses_in.Fecha_Programada.strftime("%Y-%m-%d").encode() in resp.data
    assert ses_out.Fecha_Programada.strftime("%Y-%m-%d").encode() not in resp.data


def test_listar_sesiones_fecha_hasta_invalida_no_revienta(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    resp = client.get("/profesional/sesiones?fecha_hasta=xxxx")
    assert resp.status_code == 200



def test_ver_sesion_permisos_y_detalle(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    ej = Ejercicio(
        Nombre="Puente",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="v1.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    ev = Evaluacion(
        Ejercicio_Sesion_Id=es.Id,
        Puntuacion=5,
        Comentarios="OK",
        Fecha_Evaluacion=datetime.now(),
    )
    db.session.add(ev)
    db.session.commit()

    resp = client.get(f"/profesional/sesion/{ses.Id}")
    assert resp.status_code == 200
    assert b"Puente" in resp.data

    # sesión de otro profesional
    otro_user = Usuario(
        Nombre="X",
        Apellidos="Y",
        Email="otropro@example.com",
        Rol_Id=2,
        Estado=1,
    )
    otro_user.set_contraseña("password123")
    db.session.add(otro_user)
    db.session.commit()
    otro_pro = Profesional(Usuario_Id=otro_user.Id, Especialidad="Esp", Tipo_Profesional="TERAPEUTA")
    db.session.add(otro_pro)
    db.session.commit()

    ses_otro = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=otro_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses_otro)
    db.session.commit()

    resp2 = client.get(f"/profesional/sesion/{ses_otro.Id}", follow_redirects=True)
    assert resp2.status_code == 200
    assert b"No tienes permisos para ver esta sesi" in resp2.data


def test_ejecutar_sesion_sin_ejercicios_redirige(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    resp = client.get(f"/profesional/sesion/ejecutar/{ses.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"no tiene ejercicios" in resp.data.lower()


def test_ejecutar_sesion_con_ejercicios(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    ej = Ejercicio(
        Nombre="Puente",
        Descripcion="Desc",
        Tipo="Fuerza",
        Video="v1.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    resp = client.get(f"/profesional/sesion/ejecutar/{ses.Id}")
    assert resp.status_code == 200
    assert b"Puente" in resp.data


def test_ejecutar_sesion_sin_permiso_redirige(
    client, profesional_user, paciente_user, user_factory, login_profesional
):
    otro = user_factory(Rol_Id=2, Email="otropro_ejecutar@example.com")
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=otro.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    resp = client.get(
        f"/profesional/sesion/ejecutar/{ses.Id}", follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"No tienes permisos para ejecutar esta sesi" in resp.data



def test_finalizar_sesion_ok(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    resp = client.post(f"/profesional/sesion/finalizar/{ses.Id}")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True


def test_finalizar_sesion_sin_permiso(
    client, profesional_user, paciente_user, user_factory, login_profesional
):
    otro = user_factory(Rol_Id=2, Email="otropro2@example.com")
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=otro.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    resp = client.post(f"/profesional/sesion/finalizar/{ses.Id}")
    data = json.loads(resp.data)
    assert data["success"] is False


# ------------- API estado de sesión tiempo real ----------


def test_obtener_estado_sesion(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    # setear estado global
    profesional_controlador.estado_sesiones_tiempo_real[ses.Id] = 5
    profesional_controlador.estado_sesion_terminada.add(ses.Id)

    resp = client.get(f"/profesional/api/sesion/{ses.Id}/estado")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["ejercicio_activo_id"] == 5
    assert data["terminada"] is True


def test_actualizar_estado_sesion_ok(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    payload = {"ejercicio_activo_id": 10}
    resp = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["ok"] is True
    assert profesional_controlador.estado_sesiones_tiempo_real[ses.Id] == 10


def test_actualizar_estado_sesion_sin_permiso(
    client, profesional_user, paciente_user, user_factory, login_profesional
):
    otro = user_factory(Rol_Id=2, Email="otropro3@example.com")
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=otro.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    payload = {"ejercicio_activo_id": 10}
    resp = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 403


def test_actualizar_estado_sesion_sin_ejercicio_id(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    # primero fijamos un estado conocido
    payload = {"ejercicio_activo_id": 10}
    resp1 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp1.status_code == 200
    data1 = json.loads(resp1.data)
    assert data1["ok"] is True
    assert data1["ejercicio_activo_id"] == 10

    # luego mandamos un POST vacío: no debería romper ni cambiar nada
    resp2 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    data2 = json.loads(resp2.data)
    assert data2["ok"] is True
    # se mantiene el último ejercicio activo
    assert data2["ejercicio_activo_id"] == 10
    # assert data2["terminada"] is False


def test_estado_sesion_reset_a_none(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    payload1 = {"ejercicio_activo_id": 10}
    resp1 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload1),
        content_type="application/json",
    )
    assert resp1.status_code == 200

    payload2 = {"ejercicio_activo_id": None}
    resp2 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload2),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    data2 = json.loads(resp2.data)
    assert data2["ok"] is True
    assert data2["ejercicio_activo_id"] is None


def test_estado_sesion_antirebote(
    client, profesional_user, paciente_user, login_profesional, monkeypatch
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    payload1 = {"ejercicio_activo_id": 10}
    resp1 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload1),
        content_type="application/json",
    )
    assert resp1.status_code == 200

    profesional_controlador.ultimo_cambio_sesion[ses.Id] = time.time()

    payload2 = {"ejercicio_activo_id": 20}
    resp2 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload2),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    data2 = json.loads(resp2.data)
    assert data2["ok"] is False
    assert data2["ejercicio_activo_id"] == 10


def test_estado_sesion_terminada_flag_varias_veces(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    payload = {"terminada": True}
    resp1 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp1.status_code == 200
    data1 = json.loads(resp1.data)
    assert data1["ok"] is True
    assert data1["terminada"] is True

    resp2 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    data2 = json.loads(resp2.data)
    assert data2["ok"] is True
    assert data2["terminada"] is True


def test_estado_sesion_marcar_y_desmarcar_terminada(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    # marcar terminada
    resp1 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps({"terminada": True}),
        content_type="application/json",
    )
    assert resp1.status_code == 200
    assert ses.Id in profesional_controlador.estado_sesion_terminada

    # desmarcar terminada
    resp2 = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps({"terminada": False}),
        content_type="application/json",
    )
    assert resp2.status_code == 200
    assert ses.Id not in profesional_controlador.estado_sesion_terminada


def test_estado_sesion_marcar_terminada_desde_api(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    # llamamos al endpoint solo con terminada=True
    resp = client.post(
        f"/profesional/api/sesion/{ses.Id}/estado",
        data=json.dumps({"terminada": True}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["ok"] is True
    assert data["terminada"] is True
    # comprueba que se ha añadido en la caché
    assert ses.Id in profesional_controlador.estado_sesion_terminada


# ----------------- evaluación de ejercicios ---------------


def _crear_sesion_completada_con_video(
    paciente_id, profesional_id, puntuacion=None
):
    ses = Sesion(
        Paciente_Id=paciente_id,
        Profesional_Id=profesional_id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="COMPLETADA",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="EjPrueba",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()
    vr = VideoRespuesta(
        Ejercicio_Sesion_Id=es.Id,
        Ruta_Almacenamiento="resp.webm",
        Fecha_Expiracion=datetime.now() + timedelta(days=30),
    )
    db.session.add(vr)
    db.session.commit()
    ev = None
    if puntuacion is not None:
        ev = Evaluacion(
            Ejercicio_Sesion_Id=es.Id,
            Puntuacion=puntuacion,
            Comentarios="OK",
            Fecha_Evaluacion=datetime.now(),
        )
        db.session.add(ev)
        db.session.commit()
    return ses, es, ev


def test_evaluar_sesion_ok(
    client, profesional_user, paciente_user, login_profesional
):
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, profesional_user.Id, puntuacion=4
    )
    resp = client.get(f"/profesional/evaluar_sesion/{ses.Id}")
    assert resp.status_code == 200
    assert b"EjPrueba" in resp.data


def test_evaluar_sesion_sin_permiso(
    client, profesional_user, paciente_user, user_factory, login_profesional
):
    otro = user_factory(Rol_Id=2, Email="otropro4@example.com")
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, otro.Id, puntuacion=4
    )
    resp = client.get(f"/profesional/evaluar_sesion/{ses.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"No tienes permisos para evaluar esta sesi" in resp.data


def test_evaluar_sesion_no_completada(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    resp = client.get(f"/profesional/evaluar_sesion/{ses.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Solo se pueden evaluar sesiones completadas" in resp.data


def test_evaluar_ejercicio_get_y_post(
    client, profesional_user, paciente_user, login_profesional
):
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, profesional_user.Id
    )
    # GET
    resp = client.get(f"/profesional/evaluar/{es.Id}")
    assert resp.status_code == 200

    # POST con datos válidos
    data = {"puntuacion": "5", "comentarios": "Muy bien"}
    resp2 = client.post(
        f"/profesional/evaluar/{es.Id}",
        data=data,
        follow_redirects=False,
    )
    assert resp2.status_code == 302
    ev = Evaluacion.query.filter_by(Ejercicio_Sesion_Id=es.Id).first()
    assert ev is not None and ev.Puntuacion == 5


def test_evaluar_ejercicio_sin_permiso(
    client, profesional_user, paciente_user, user_factory, login_profesional
):
    otro = user_factory(Rol_Id=2, Email="otropro5@example.com")
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, otro.Id
    )
    resp = client.get(f"/profesional/evaluar/{es.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"No tienes permisos para evaluar este ejercicio" in resp.data


# ----------------- progreso de paciente -------------------


def test_ver_progreso_paciente_ok(
    client, profesional_user, paciente_user, login_profesional
):
    vinc = Paciente_Profesional(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now().date(),
    )
    db.session.add(vinc)
    db.session.commit()

    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, profesional_user.Id, puntuacion=4
    )

    resp = client.get(f"/profesional/progreso/{paciente_user.Id}")
    assert resp.status_code == 200
    assert b"EjPrueba" in resp.data


def test_ver_progreso_sin_vinculacion(
    client, profesional_user, paciente_user, login_profesional
):
    # sin Paciente_Profesional
    resp = client.get(f"/profesional/progreso/{paciente_user.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"No tienes permisos para ver este paciente" in resp.data


# ----------------- gestión de videos y ver evaluación -----


def test_guardar_video_ok(
    client, profesional_user, paciente_user, login_user_fixture, tmp_path, monkeypatch
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()

    ej = Ejercicio(
        Nombre="VideoEj",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    # login como paciente (dueño del ejercicio_sesion)
    login_user_fixture(paciente_user)

    # opcional: mock de cloudinary para que no haga llamadas reales
    monkeypatch.setattr(
        "src.controladores.profesional_controlador.cloudinary.uploader.upload",
        lambda *args, **kwargs: {"secure_url": "https://example.com/video.mp4"},
    )

    data = {
        "video": (io.BytesIO(b"fake webm"), "test.webm"),
    }
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data_json = json.loads(resp.data)
    assert data_json["success"] is True
    vr = VideoRespuesta.query.filter_by(Ejercicio_Sesion_Id=es.Id).first()
    assert vr is not None


def test_guardar_video_sin_archivo(
    client, profesional_user, paciente_user, login_user_fixture
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="VideoEj",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    # login como paciente, que es quien podría subir
    login_user_fixture(paciente_user)

    resp = client.post(f"/profesional/guardar_video/{es.Id}", data={})
    assert resp.status_code == 400
    data_json = json.loads(resp.data)
    assert data_json["success"] is False


def test_guardar_video_archivo_vacio(
    client, profesional_user, paciente_user, login_user_fixture
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="VideoEj",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    login_user_fixture(paciente_user)

    data = {"video": (io.BytesIO(b""), "")}
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    data_json = json.loads(resp.data)
    assert data_json["success"] is False
    assert "Archivo vacío" in data_json["error"]



def test_guardar_video_sin_permiso_devuelve_403(
    client, profesional_user, paciente_user, login_profesional
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="VideoEj",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    resp = client.post(f"/profesional/guardar_video/{es.Id}", data={})
    assert resp.status_code == 403
    data = json.loads(resp.data)
    assert data["success"] is False


def test_guardar_video_ya_existente(
    client, profesional_user, paciente_user, login_user_fixture
):
    # ya crea un VideoRespuesta, no añadas otro
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, profesional_user.Id
    )

    login_user_fixture(paciente_user)

    data = {"video": (io.BytesIO(b"fake"), "test.webm")}
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data_json = json.loads(resp.data)
    assert data_json["success"] is True
    assert "ya existente" in data_json["mensaje"]



def test_guardar_video_sin_url_cloudinary(
    client, profesional_user, paciente_user, login_user_fixture, monkeypatch
):
    # crear sesion y ejercicio_sesion, pero sin VideoRespuesta
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="VideoEj",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    login_user_fixture(paciente_user)

    monkeypatch.setattr(
        "src.controladores.profesional_controlador.cloudinary.uploader.upload",
        lambda *args, **kwargs: {},
    )

    data = {"video": (io.BytesIO(b"fake"), "test.webm")}
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 500
    data_json = json.loads(resp.data)
    assert data_json["success"] is False
    assert "No se obtuvo URL del video" in data_json["error"]



def test_guardar_video_integrity_error(
    client, profesional_user, paciente_user, login_user_fixture, monkeypatch
):
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, profesional_user.Id
    )
    login_user_fixture(paciente_user)

    monkeypatch.setattr(
        "src.controladores.profesional_controlador.cloudinary.uploader.upload",
        lambda *args, **kwargs: {"secure_url": "https://example.com/video.mp4"},
    )

    def fake_commit():
        raise IntegrityError("dummy", None, None)

    monkeypatch.setattr(
        "src.controladores.profesional_controlador.db.session.commit", fake_commit
    )

    data = {"video": (io.BytesIO(b"fake"), "test.webm")}
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data_json = json.loads(resp.data)
    assert data_json["success"] is True
    assert "Video ya existente" in data_json["mensaje"]

from sqlalchemy.exc import IntegrityError

def test_guardar_video_integrity_error_race(
    client, profesional_user, paciente_user, login_user_fixture, monkeypatch
):
    # sesión + ejercicio_sesion sin VideoRespuesta previo
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="VideoEjRace",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    login_user_fixture(paciente_user)

    monkeypatch.setattr(
        "src.controladores.profesional_controlador.cloudinary.uploader.upload",
        lambda *args, **kwargs: {"secure_url": "https://example.com/video.mp4"},
    )

    # hacer que el commit de ese bloque concreto lance IntegrityError
    original_commit = db.session.commit

    def fake_commit():
        raise IntegrityError("dummy", None, None)

    monkeypatch.setattr(
        "src.controladores.profesional_controlador.db.session.commit", fake_commit
    )

    data = {"video": (io.BytesIO(b"fake"), "test.webm")}
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )

    # restaurar commit por si acaso
    monkeypatch.setattr(
        "src.controladores.profesional_controlador.db.session.commit", original_commit
    )

    assert resp.status_code == 200
    data_json = json.loads(resp.data)
    assert data_json["success"] is True
    assert "ya existente" in data_json["mensaje"]



def test_guardar_video_excepcion_generica(
    client, profesional_user, paciente_user, login_user_fixture, monkeypatch
):
    ses = Sesion(
        Paciente_Id=paciente_user.Id,
        Profesional_Id=profesional_user.Id,
        Fecha_Asignacion=datetime.now(),
        Fecha_Programada=datetime.now(),
        Estado="PENDIENTE",
    )
    db.session.add(ses)
    db.session.commit()
    ej = Ejercicio(
        Nombre="VideoEj",
        Descripcion="Desc",
        Tipo="Test",
        Video="v.mp4",
        Duracion=10,
    )
    db.session.add(ej)
    db.session.commit()
    es = Ejercicio_Sesion(Sesion_Id=ses.Id, Ejercicio_Id=ej.Id)
    db.session.add(es)
    db.session.commit()

    login_user_fixture(paciente_user)

    def fake_upload(*args, **kwargs):
        raise RuntimeError("fallo cloudinary")

    monkeypatch.setattr(
        "src.controladores.profesional_controlador.cloudinary.uploader.upload",
        fake_upload,
    )

    data = {"video": (io.BytesIO(b"fake"), "test.webm")}
    resp = client.post(
        f"/profesional/guardar_video/{es.Id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 500
    data_json = json.loads(resp.data)
    assert data_json["success"] is False
    assert "fallo cloudinary" in data_json["error"]



def test_ver_evaluacion_ok(
    client, profesional_user, paciente_user, login_profesional
):
    ses, es, ev = _crear_sesion_completada_con_video(
        paciente_user.Id, profesional_user.Id, puntuacion=3
    )

    resp = client.get(f"/profesional/ver_evaluacion/{es.Id}")
    assert resp.status_code == 200
    # comprueba que aparece el comentario de la evaluación creada en el helper
    assert b"OK" in resp.data



def test_ver_evaluacion_sin_permiso(
    client, profesional_user, paciente_user, user_factory, login_profesional
):
    otro = user_factory(Rol_Id=2, Email="otropro6@example.com")
    ses, es, _ = _crear_sesion_completada_con_video(
        paciente_user.Id, otro.Id, puntuacion=3
    )

    resp = client.get(f"/profesional/ver_evaluacion/{es.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"No tienes permisos para ver esta evaluaci" in resp.data
