import os
import json
import builtins
from datetime import date, datetime, timedelta
from io import StringIO

import pytest
from flask import url_for
from flask_login import login_user

from src.extensiones import db
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.asociaciones import Paciente_Profesional
from src.controladores import admin_controlador


# --------- helpers / fixtures específicos admin ---------


@pytest.fixture
def admin_user(user_factory):
    """Crea un usuario administrador activo."""
    return user_factory(
        Email="admin@example.com",
        Rol_Id=0,
        Estado=1,
        Nombre="Admin",
        Apellidos="User",
    )


@pytest.fixture
def login_admin(login_user_fixture, admin_user):
    """Loguea al admin para tests de rutas protegidas."""
    return login_user_fixture(admin_user)


# ----------------- configuración JSON --------------------


def test_cargar_configuracion_crea_por_defecto(tmp_path, monkeypatch):
    # Redefinir carpeta config a un directorio temporal
    config_dir = tmp_path / "config"
    monkeypatch.setattr(admin_controlador.os, "path", os.path)
    monkeypatch.setattr(admin_controlador.os, "makedirs", os.makedirs)
    monkeypatch.setattr(admin_controlador.os, "path", os.path)
    monkeypatch.chdir(tmp_path)

    config = admin_controlador.cargar_configuracion()
    assert "retencion_videos" in config
    assert os.path.exists(os.path.join("config", "sistema.json"))


def test_guardar_configuracion_ok(tmp_path, monkeypatch, admin_user, login_admin, app):
    monkeypatch.chdir(tmp_path)

    # Partir de config por defecto
    config = admin_controlador.cargar_configuracion()
    config["retencion_videos"] = "60"

    with app.test_request_context():
        # current_user dentro de guardar_configuracion
        from flask_login import login_user

        login_user(admin_user)
        ok = admin_controlador.guardar_configuracion(config)

    assert ok is True
    with open(os.path.join("config", "sistema.json"), encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["retencion_videos"] == "60"
    assert loaded["modificado_por"] == admin_user.Id

def test_guardar_configuracion_error(monkeypatch, tmp_path, app, admin_user):
    # simulamos que open lanza una excepción
    def fake_open(*args, **kwargs):
        raise IOError("no se puede escribir")

    monkeypatch.chdir(tmp_path)
    # parchear la función open global que usa admin_controlador
    monkeypatch.setattr(builtins, "open", fake_open)

    with app.test_request_context():
        from flask_login import login_user
        login_user(admin_user)
        ok = admin_controlador.guardar_configuracion({"retencion_videos": "10"})

    assert ok is False

def test_cargar_configuracion_error_usa_default(monkeypatch, tmp_path):
    # forzar error al abrir el JSON
    def fake_open(*args, **kwargs):
        raise IOError("no se puede leer")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(builtins, "open", fake_open)

    config = admin_controlador.cargar_configuracion()
    assert config["retencion_videos"] == "30"

# ---------------------- dashboard ------------------------


def test_dashboard_admin(client, admin_user, login_admin):
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200
    assert b"dashboard" in resp.data.lower()


# ------------------- listar_usuarios ---------------------


def test_listar_usuarios_sin_filtros(client, admin_user, login_admin, user_factory):
    user_factory(Email="u1@example.com", Rol_Id=1)
    resp = client.get("/admin/usuarios")
    assert resp.status_code == 200
    assert b"u1@example.com" in resp.data


def test_listar_usuarios_con_filtros(client, admin_user, login_admin, user_factory):
    user1 = user_factory(Email="pac@example.com", Rol_Id=1)
    user2 = user_factory(Email="pro@example.com", Rol_Id=2)
    # filtro por texto y rol paciente activo
    resp = client.get(
        "/admin/usuarios?search=pac&rol=1&estado=1"
    )
    assert resp.status_code == 200
    assert user1.Email.encode() in resp.data
    assert user2.Email.encode() not in resp.data


# -------------------- ver_usuario ------------------------


def test_ver_usuario_no_admin_redirige_a_login(
    client, user_factory, login_user_fixture
):
    user = user_factory(Rol_Id=1, Email="p@example.com")
    login_user_fixture(user)
    resp = client.get(f"/admin/usuario/{user.Id}", follow_redirects=False)
    assert resp.status_code == 403



def test_ver_usuario_inactivo_redirige_lista(client, admin_user, login_admin, user_factory):
    u = user_factory(Email="inactivo@example.com", Estado=0)
    resp = client.get(f"/admin/usuario/{u.Id}", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/usuarios" in resp.location


def test_ver_usuario_paciente_muestra_detalle_y_vinculaciones(
    client, admin_user, login_admin, user_factory
):
    # crear paciente + profesional y vinculación
    pac = user_factory(Email="pacv@example.com", Rol_Id=1)
    prof = user_factory(Email="profv@example.com", Rol_Id=2)
    paciente = Paciente(
        Usuario_Id=pac.Id,
        Fecha_Nacimiento=date(2000, 1, 1),
        Condicion_Medica="Cond",
        Notas="Notas",
    )
    profesional = Profesional(
        Usuario_Id=prof.Id,
        Especialidad="Esp",
        Tipo_Profesional="MEDICO",
    )
    db.session.add_all([paciente, profesional])
    db.session.commit()
    vinculacion = Paciente_Profesional(
        Paciente_Id=pac.Id,
        Profesional_Id=prof.Id,
        Fecha_Asignacion=date.today(),
    )
    db.session.add(vinculacion)
    db.session.commit()

    resp = client.get(f"/admin/usuario/{pac.Id}")
    assert resp.status_code == 200
    assert pac.Email.encode() in resp.data
    assert b"Cond" in resp.data


def test_ver_usuario_profesional_muestra_detalle(
    client, admin_user, login_admin, user_factory
):
    prof = user_factory(Email="profd@example.com", Rol_Id=2)
    profesional = Profesional(
        Usuario_Id=prof.Id,
        Especialidad="Fisio",
        Tipo_Profesional="TERAPEUTA",
    )
    db.session.add(profesional)
    db.session.commit()

    resp = client.get(f"/admin/usuario/{prof.Id}")
    assert resp.status_code == 200
    assert b"Fisio" in resp.data


def test_editar_usuario_get_precarga_profesional(
    client, admin_user, login_admin, user_factory
):
    user = user_factory(Email="prof_pre@example.com", Rol_Id=2)
    prof = Profesional(
        Usuario_Id=user.Id,
        Especialidad="Cardio",
        Tipo_Profesional="MEDICO",
    )
    db.session.add(prof)
    db.session.commit()

    resp = client.get(f"/admin/editar_usuario/{user.Id}")
    assert resp.status_code == 200
    assert b"Cardio" in resp.data


# -------------------- editar_usuario ---------------------


def test_editar_usuario_get_precarga(
    client, admin_user, login_admin, user_factory
):
    user = user_factory(Email="edit@example.com", Rol_Id=1)
    pac = Paciente(
        Usuario_Id=user.Id,
        Fecha_Nacimiento=date(2000, 1, 1),
        Condicion_Medica="X",
        Notas="Y",
    )
    db.session.add(pac)
    db.session.commit()

    resp = client.get(f"/admin/editar_usuario/{user.Id}")
    assert resp.status_code == 200
    assert b"edit@example.com" in resp.data


def test_editar_usuario_inactivo_redirige(
    client, admin_user, login_admin, user_factory
):
    user = user_factory(Email="edit_inactivo@example.com", Estado=0)
    resp = client.get(f"/admin/editar_usuario/{user.Id}", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/usuarios" in resp.location


def test_editar_usuario_email_duplicado(
    client, admin_user, login_admin, user_factory
):
    user1 = user_factory(Email="orig@example.com")
    user2 = user_factory(Email="otro@example.com")

    resp = client.post(
        f"/admin/editar_usuario/{user2.Id}",
        data={
            "nombre": "Nuevo",
            "apellidos": "Ap",
            "email": "orig@example.com",  # email de otro
            "password": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"ya est\xc3\xa1 en uso" in resp.data  # mensaje de error


def test_editar_usuario_paciente_actualiza(
    client, admin_user, login_admin, user_factory
):
    user = user_factory(Email="pac_edit@example.com", Rol_Id=1)
    pac = Paciente(
        Usuario_Id=user.Id,
        Fecha_Nacimiento=date(2000, 1, 1),
        Condicion_Medica="Old",
        Notas="Old",
    )
    db.session.add(pac)
    db.session.commit()

    resp = client.post(
        f"/admin/editar_usuario/{user.Id}",
        data={
            "nombre": "NuevoNombre",
            "apellidos": "NuevoAp",
            "email": "pac_edit@example.com",
            "password": "newpass123",
            "condicion_medica": "NewCond",
            "notas": "NewNotas",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/admin/usuario/{user.Id}" in resp.location

    db.session.refresh(user)
    assert user.Nombre == "NuevoNombre"


def test_editar_usuario_profesional_actualiza(
    client, admin_user, login_admin, user_factory
):
    user = user_factory(Email="prof_edit@example.com", Rol_Id=2)
    prof = Profesional(
        Usuario_Id=user.Id,
        Especialidad="Old",
        Tipo_Profesional="MEDICO",
    )
    db.session.add(prof)
    db.session.commit()

    resp = client.post(
        f"/admin/editar_usuario/{user.Id}",
        data={
            "nombre": "NuevoProf",
            "apellidos": "Ap",
            "email": "prof_edit@example.com",
            "password": "",
            "especialidad": "NuevaEsp",
            "tipo_profesional": "TERAPEUTA",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    db.session.refresh(prof)
    assert prof.Especialidad == "NuevaEsp"

def test_editar_usuario_error_lanza_flash(
    client, admin_user, login_admin, user_factory, monkeypatch
):
    user = user_factory(Email="edit_err@example.com", Rol_Id=1)
    pac = Paciente(
        Usuario_Id=user.Id,
        Fecha_Nacimiento=date(2000, 1, 1),
        Condicion_Medica="X",
        Notas="Y",
    )
    db.session.add(pac)
    db.session.commit()

    def fake_commit():
        raise Exception("fallo commit")

    monkeypatch.setattr(db.session, "commit", fake_commit)

    resp = client.post(
        f"/admin/editar_usuario/{user.Id}",
        data={
            "nombre": "Nuevo",
            "apellidos": "Ap",
            "email": "edit_err@example.com",
            "password": "",
            "condicion_medica": "Z",
            "notas": "N",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Error al actualizar usuario" in resp.data


# ---------------- cambiar_estado_usuario ------------------


def test_cambiar_estado_usuario_no_puede_su_cuenta(
    client, admin_user, login_admin
):
    resp = client.get(f"/admin/cambiar_estado/{admin_user.Id}", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/usuarios" in resp.location


def test_cambiar_estado_usuario_otro(
    client, admin_user, login_admin, user_factory
):
    user = user_factory(Email="estado@example.com", Estado=1)
    resp = client.get(f"/admin/cambiar_estado/{user.Id}", follow_redirects=False)
    assert resp.status_code == 302
    db.session.refresh(user)
    assert user.Estado == 0  # cambiado a inactivo


# -------------------- crear_usuario ----------------------


def test_crear_usuario_get(client, admin_user, login_admin):
    resp = client.get("/admin/crear_usuario")
    assert resp.status_code == 200


def test_crear_usuario_email_duplicado(
    client, admin_user, login_admin, user_factory
):
    # Usuario ya existente con ese email
    user_factory(Email="dup@example.com")

    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "NombreValido",
            "apellidos": "ApellidosValidos",
            "email": "dup@example.com",  # mismo email
            "password": "pass123",
            "rol_id": "0",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert Usuario.query.filter_by(Email="dup@example.com").count() == 1




def test_crear_usuario_admin(
    client, admin_user, login_admin
):
    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "Admin2",
            "apellidos": "A2",
            "email": "adm2@example.com",
            "password": "pass123",
            "rol_id": "0",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    u = Usuario.query.filter_by(Email="adm2@example.com").first()
    assert u is not None and u.Rol_Id == 0



def test_crear_paciente_sin_fecha_error(client, admin_user, login_admin):
    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "Paciente",
            "apellidos": "Prueba",
            "email": "pac_sin_fecha@example.com",
            "password": "pass123",
            "rol_id": "1",
            # sin fecha_nacimiento
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # no se crea usuario con ese email
    assert Usuario.query.filter_by(Email="pac_sin_fecha@example.com").first() is None





def test_crear_paciente_ok(client, admin_user, login_admin):
    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "Pac",
            "apellidos": "Lanchares",
            "email": "pac_ok@example.com",
            "password": "pass123",
            "rol_id": "1",
            "fecha_nacimiento": "2000-01-01",
            "condicion_medica": "Cond",
            "notas": "Notas",
        },
        follow_redirects=True,
    )
    assert resp.status_code in (200, 302)

    u = Usuario.query.filter_by(Email="pac_ok@example.com").first()
    assert u is not None
    pac = Paciente.query.filter_by(Usuario_Id=u.Id).first()
    assert pac is not None
    assert pac.Condicion_Medica == "Cond"




def test_crear_profesional_sin_datos_error(client, admin_user, login_admin):
    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "Profesional",
            "apellidos": "Prueba",
            "email": "prof_err@example.com",
            "password": "pass123",
            "rol_id": "2",
            # sin especialidad ni tipo_profesional
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert Usuario.query.filter_by(Email="prof_err@example.com").first() is None




def test_crear_profesional_ok(client, admin_user, login_admin):
    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "Prof",
            "apellidos": "Lanchares",
            "email": "prof_ok@example.com",
            "password": "pass123",
            "rol_id": "2",
            "especialidad": "Fisio",
            "tipo_profesional": "TERAPEUTA",
        },
        follow_redirects=True,
    )
    assert resp.status_code in (200, 302)

    u = Usuario.query.filter_by(Email="prof_ok@example.com").first()
    assert u is not None
    prof = Profesional.query.filter_by(Usuario_Id=u.Id).first()
    assert prof is not None
    assert prof.Especialidad == "Fisio"
    assert prof.Tipo_Profesional == "TERAPEUTA"



def test_crear_usuario_error_general_muestra_flash(
    client, admin_user, login_admin, monkeypatch
):
    def fake_commit():
        raise Exception("fallo al crear")

    monkeypatch.setattr(db.session, "commit", fake_commit)

    resp = client.post(
        "/admin/crear_usuario",
        data={
            "nombre": "Err",
            "apellidos": "User",
            "email": "err@example.com",
            "password": "pass123",
            "rol_id": "0",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Error al crear usuario" in resp.data


# ---------------- vincular / vinculaciones ----------------


def test_vincular_get_muestra_choices(client, admin_user, login_admin, user_factory):
    pac = user_factory(Email="v_pac@example.com", Rol_Id=1, Nombre="Pac", Apellidos="Uno")
    prof = user_factory(Email="v_prof@example.com", Rol_Id=2, Nombre="Prof", Apellidos="Dos")
    paciente = Paciente(
        Usuario_Id=pac.Id,
        Fecha_Nacimiento=date(2000, 1, 1),
        Condicion_Medica="",
        Notas="",
    )
    profesional = Profesional(
        Usuario_Id=prof.Id,
        Especialidad="Esp",
        Tipo_Profesional="MEDICO",
    )
    db.session.add_all([paciente, profesional])
    db.session.commit()

    resp = client.get("/admin/vincular")
    assert resp.status_code == 200
    # en la plantilla se muestran nombres/apellidos, no emails
    assert b"Pac Uno" in resp.data or b"Prof Dos" in resp.data




def test_vincular_existente_muestra_error(
    client, admin_user, login_admin, user_factory
):
    pac = user_factory(Email="v2_pac@example.com", Rol_Id=1)
    prof = user_factory(Email="v2_prof@example.com", Rol_Id=2)
    db.session.add_all([
        Paciente(
            Usuario_Id=pac.Id,
            Fecha_Nacimiento=date(2000, 1, 1),
            Condicion_Medica="",
            Notas="",
        ),
        Profesional(
            Usuario_Id=prof.Id,
            Especialidad="Esp",
            Tipo_Profesional="MEDICO",
        ),
    ])
    db.session.commit()
    vinc = Paciente_Profesional(
        Paciente_Id=pac.Id,
        Profesional_Id=prof.Id,
        Fecha_Asignacion=date.today(),
    )
    db.session.add(vinc)
    db.session.commit()

    resp = client.post(
        "/admin/vincular",
        data={"paciente_id": pac.Id, "profesional_id": prof.Id},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"ya existe" in resp.data


def test_vincular_crea_nueva(
    client, admin_user, login_admin, user_factory
):
    pac = user_factory(Email="v3_pac@example.com", Rol_Id=1)
    prof = user_factory(Email="v3_prof@example.com", Rol_Id=2)
    db.session.add_all([
        Paciente(
            Usuario_Id=pac.Id,
            Fecha_Nacimiento=date(2000, 1, 1),
            Condicion_Medica="",
            Notas="",
        ),
        Profesional(
            Usuario_Id=prof.Id,
            Especialidad="Esp",
            Tipo_Profesional="MEDICO",
        ),
    ])
    db.session.commit()

    resp = client.post(
        "/admin/vincular",
        data={"paciente_id": pac.Id, "profesional_id": prof.Id},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    vinc = Paciente_Profesional.query.filter_by(
        Paciente_Id=pac.Id, Profesional_Id=prof.Id
    ).first()
    assert vinc is not None


def test_ver_vinculaciones_sin_filtros(
    client, admin_user, login_admin, user_factory
):
    pac = user_factory(Email="vv_pac@example.com", Rol_Id=1)
    prof = user_factory(Email="vv_prof@example.com", Rol_Id=2)
    db.session.add_all([
        Paciente(
            Usuario_Id=pac.Id,
            Fecha_Nacimiento=date(2000, 1, 1),
            Condicion_Medica="Cond",
            Notas="",
        ),
        Profesional(
            Usuario_Id=prof.Id,
            Especialidad="Esp",
            Tipo_Profesional="MEDICO",
        ),
    ])
    db.session.commit()
    vinc = Paciente_Profesional(
        Paciente_Id=pac.Id,
        Profesional_Id=prof.Id,
        Fecha_Asignacion=date.today(),
    )
    db.session.add(vinc)
    db.session.commit()

    resp = client.get("/admin/vinculaciones")
    assert resp.status_code == 200
    assert b"Cond" in resp.data


def test_desvincular_existente(
    client, admin_user, login_admin, user_factory
):
    pac = user_factory(Email="dv_pac@example.com", Rol_Id=1)
    prof = user_factory(Email="dv_prof@example.com", Rol_Id=2)
    db.session.add_all([
        Paciente(
            Usuario_Id=pac.Id,
            Fecha_Nacimiento=date(2000, 1, 1),
            Condicion_Medica="",
            Notas="",
        ),
        Profesional(
            Usuario_Id=prof.Id,
            Especialidad="Esp",
            Tipo_Profesional="MEDICO",
        ),
    ])
    db.session.commit()
    vinc = Paciente_Profesional(
        Paciente_Id=pac.Id,
        Profesional_Id=prof.Id,
        Fecha_Asignacion=date.today(),
    )
    db.session.add(vinc)
    db.session.commit()

    resp = client.post(f"/admin/desvincular/{pac.Id}/{prof.Id}", follow_redirects=False)
    assert resp.status_code == 302
    assert (
        Paciente_Profesional.query.filter_by(
            Paciente_Id=pac.Id, Profesional_Id=prof.Id
        ).first()
        is None
    )


def test_desvincular_no_existente(
    client, admin_user, login_admin, user_factory
):
    pac = user_factory(Email="dv2_pac@example.com", Rol_Id=1)
    prof = user_factory(Email="dv2_prof@example.com", Rol_Id=2)
    resp = client.post(f"/admin/desvincular/{pac.Id}/{prof.Id}", follow_redirects=True)
    assert resp.status_code == 200  # se mantiene en la vista con flash


def test_desvincular_lanza_error_bd(
    client, admin_user, login_admin, user_factory, monkeypatch
):
    pac = user_factory(Email="err_pac@example.com", Rol_Id=1)
    prof = user_factory(Email="err_prof@example.com", Rol_Id=2)
    db.session.add_all([
        Paciente(
            Usuario_Id=pac.Id,
            Fecha_Nacimiento=date(2000, 1, 1),
            Condicion_Medica="",
            Notas="",
        ),
        Profesional(
            Usuario_Id=prof.Id,
            Especialidad="Esp",
            Tipo_Profesional="MEDICO",
        ),
    ])
    db.session.commit()
    vinc = Paciente_Profesional(
        Paciente_Id=pac.Id,
        Profesional_Id=prof.Id,
        Fecha_Asignacion=date.today(),
    )
    db.session.add(vinc)
    db.session.commit()

    # hacer que commit falle
    def fake_commit():
        raise Exception("fallo en BD")

    monkeypatch.setattr(db.session, "commit", fake_commit)

    resp = client.post(f"/admin/desvincular/{pac.Id}/{prof.Id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Error al desvincular" in resp.data


def test_ver_vinculaciones_con_filtros(
    client, admin_user, login_admin, user_factory
):
    pac = user_factory(Email="busc_pac@example.com", Rol_Id=1, Nombre="Ana", Apellidos="Gomez")
    prof = user_factory(Email="busc_prof@example.com", Rol_Id=2, Nombre="Luis", Apellidos="Lopez")
    db.session.add_all([
        Paciente(
            Usuario_Id=pac.Id,
            Fecha_Nacimiento=date(2000, 1, 1),
            Condicion_Medica="Dolor espalda",
            Notas="",
        ),
        Profesional(
            Usuario_Id=prof.Id,
            Especialidad="Esp",
            Tipo_Profesional="MEDICO",
        ),
    ])
    db.session.commit()
    vinc = Paciente_Profesional(
        Paciente_Id=pac.Id,
        Profesional_Id=prof.Id,
        Fecha_Asignacion=date.today(),
    )
    db.session.add(vinc)
    db.session.commit()

    hoy = date.today().strftime("%Y-%m-%d")
    params = {
        "search": "espalda",             # coincide con Condicion_Medica
        "profesional": str(prof.Id),     # activa profesional_filter
        "fecha_desde": hoy,
        "fecha_hasta": hoy,
    }
    resp = client.get("/admin/vinculaciones", query_string=params)
    assert resp.status_code == 200
    assert b"Dolor espalda" in resp.data


# ----------------- estadisticas / exportar ---------------


def test_estadisticas(client, admin_user, login_admin):
    resp = client.get("/admin/estadisticas")
    assert resp.status_code == 200


def test_exportar_usuarios(client, admin_user, login_admin, user_factory):
    user_factory(Email="csv@example.com")
    resp = client.get("/admin/exportar_usuarios")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert b"csv@example.com" in resp.data


# ---------------------- configuracion ---------------------


def test_configuracion_get_usa_config_actual(
    client, admin_user, login_admin, tmp_path, monkeypatch
):
    # Trabajar en directorio temporal para el JSON
    monkeypatch.chdir(tmp_path)
    # Crear config previa
    conf = {
        "retencion_videos": "90",
        "limite_almacenamiento": "5",
        "notificaciones_email": "disabled",
        "backup_automatico": "monthly",
        "ultima_modificacion": datetime.now().isoformat(),
        "modificado_por": None,
    }
    os.makedirs("config", exist_ok=True)
    with open("config/sistema.json", "w", encoding="utf-8") as f:
        json.dump(conf, f)

    resp = client.get("/admin/configuracion")
    assert resp.status_code == 200
    assert b"90" in resp.data or b"5 GB" in resp.data  # según cómo se renderice


def test_configuracion_post_actualiza_json(
    client, admin_user, login_admin, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    # config inicial
    admin_controlador.cargar_configuracion()

    resp = client.post(
        "/admin/configuracion",
        data={
            "retencion_videos": "60",
            "limite_almacenamiento": "2",
            "notificaciones_email": "enabled",
            "backup_automatico": "weekly",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302

    with open("config/sistema.json", encoding="utf-8") as f:
        nueva = json.load(f)
    assert nueva["retencion_videos"] == "60"

def test_configuracion_error_guardar_muestra_flash(
    client, admin_user, login_admin, monkeypatch
):
    def fake_guardar(conf):
        return False

    monkeypatch.setattr(admin_controlador, "guardar_configuracion", fake_guardar)

    resp = client.post(
        "/admin/configuracion",
        data={
            "retencion_videos": "60",
            "limite_almacenamiento": "2",
            "notificaciones_email": "enabled",
            "backup_automatico": "weekly",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Error al guardar la configuraci" in resp.data

def test_configuracion_excepcion_muestra_flash(
    client, admin_user, login_admin, monkeypatch
):
    def fake_guardar_raise(conf):
        raise Exception("fallo inesperado")

    monkeypatch.setattr(admin_controlador, "guardar_configuracion", fake_guardar_raise)

    resp = client.post(
        "/admin/configuracion",
        data={
            "retencion_videos": "60",
            "limite_almacenamiento": "2",
            "notificaciones_email": "enabled",
            "backup_automatico": "weekly",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Error al procesar configuraci" in resp.data



