import pytest
from datetime import date, timedelta
from src.modelos.paciente import Paciente
from src.modelos.usuario import Usuario
from src.modelos.sesion import Sesion
from src.extensiones import db

class TestPaciente:

    def test_edad_con_fecha(self, app):
        with app.app_context():
            # Fecha de nacimiento hace 20 años
            nacimiento = date.today().replace(year=date.today().year - 20)
            paciente = Paciente(
                Usuario_Id=1,
                Fecha_Nacimiento=nacimiento,
                Condicion_Medica="Asma",
                Notas="Notas"
            )
            assert paciente.edad() == 20

    def test_edad_sin_fecha(self, app):
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=2,
                Fecha_Nacimiento=None,
                Condicion_Medica="Alergias",
                Notas="Sin fecha"
            )
            assert paciente.edad() is None

    def test_tiene_sesiones_futuras_true(self, app):
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=3,
                Fecha_Nacimiento=date(2000, 1, 1),
                Condicion_Medica="Asma",
                Notas="Notas"
            )
            # Sesión en el futuro
            sesion = Sesion(
                Paciente_Id=3,
                Profesional_Id=1,
                Fecha_Asignacion=date.today(),
                Estado="PENDIENTE",
                Fecha_Programada=date.today() + timedelta(days=5)
            )
            paciente.sesiones.append(sesion)
            assert paciente.tiene_sesiones_futuras() is True

    def test_tiene_sesiones_futuras_false(self, app):
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=4,
                Fecha_Nacimiento=date(1990, 5, 5),
                Condicion_Medica="Sin",
                Notas="No hay futuras"
            )
            # Sesión en el pasado
            sesion = Sesion(
                Paciente_Id=4,
                Profesional_Id=1,
                Fecha_Asignacion=date.today(),
                Estado="COMPLETADA",
                Fecha_Programada=date.today() - timedelta(days=10)
            )
            paciente.sesiones.append(sesion)
            assert paciente.tiene_sesiones_futuras() is False

    def test_repr(self, app):
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=5,
                Fecha_Nacimiento=date(1995, 7, 20),
                Condicion_Medica="Otra",
                Notas="Notas"
            )
            esperado = f"<Paciente Usuario_Id={paciente.Usuario_Id}>"
            assert repr(paciente) == esperado

    def test_to_dict(self, app):
        with app.app_context():
            paciente = Paciente(
                Usuario_Id=6,
                Fecha_Nacimiento=date(1995, 7, 20),
                Condicion_Medica="Condición",
                Notas="Notas"
            )
            data = paciente.to_dict()
            assert data["Usuario_Id"] == 6
            assert data["Condicion_Medica"] == "Condición"
            assert data["Notas"] == "Notas"
            assert data["Fecha_Nacimiento"] == str(date(1995, 7, 20))

    def test_relacion_usuario_paciente(self, app):
        with app.app_context():
            usuario = Usuario(
                Nombre="Paciente",
                Apellidos="Test",
                Email="paciente@test.com",
                Contraseña="1234",
                Rol_Id=1
            )
            db.session.add(usuario)
            db.session.commit()
            paciente = Paciente(
                Usuario_Id=usuario.Id,
                Fecha_Nacimiento=date(2000, 1, 1),
                Condicion_Medica="Condición",
                Notas="Notas"
            )
            db.session.add(paciente)
            db.session.commit()
            # Relación usuario <-> paciente
            assert paciente.usuario.Id == usuario.Id


