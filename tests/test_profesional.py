import pytest
from src.modelos.profesional import Profesional
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.extensiones import db

class TestProfesional:

    def test_creacion_y_relacion_usuario(self, app):
        with app.app_context():
            usuario = Usuario(
                Nombre="Carlos",
                Apellidos="García",
                Email="carlos@demo.com",
                Contraseña="1234",
                Rol_Id=2
            )
            db.session.add(usuario)
            db.session.commit()
            profesional = Profesional(
                Usuario_Id=usuario.Id,
                Especialidad="Fisioterapia",
                Tipo_Profesional="TERAPEUTA"
            )
            db.session.add(profesional)
            db.session.commit()
            assert profesional.usuario.Id == usuario.Id
            assert profesional.Especialidad == "Fisioterapia"
            assert profesional.Tipo_Profesional == "TERAPEUTA"

    def test_total_pacientes(self, app):
        with app.app_context():
            profesional = Profesional(
                Usuario_Id=1,
                Especialidad="Psicología",
                Tipo_Profesional="PSICOLOGO"
            )
            paciente1 = Paciente(
                Usuario_Id=2,
                Fecha_Nacimiento="1990-01-01",
                Condicion_Medica="Condición1",
                Notas="Notas1"
            )
            paciente2 = Paciente(
                Usuario_Id=3,
                Fecha_Nacimiento="1992-02-02",
                Condicion_Medica="Condición2",
                Notas="Notas2"
            )
            profesional.pacientes.extend([paciente1, paciente2])
            assert profesional.total_pacientes() == 2

    def test_check_constraint_tipo_profesional(self, app):
        with app.app_context():
            profesional = Profesional(
                Usuario_Id=4,
                Especialidad="Medicina",
                Tipo_Profesional="INVALIDO"
            )
            db.session.add(profesional)
            with pytest.raises(Exception):
                db.session.commit()
                db.session.rollback()

    def test_repr(self, app):
        with app.app_context():
            profesional = Profesional(
                Usuario_Id=5,
                Especialidad="Enfermería",
                Tipo_Profesional="ENFERMERO"
            )
            esperado = f"<Profesional Usuario_Id={profesional.Usuario_Id} Tipo_Profesional={profesional.Tipo_Profesional} Especialidad={profesional.Especialidad}>"
            assert repr(profesional) == esperado

    def test_to_dict(self, app):
        with app.app_context():
            profesional = Profesional(
                Usuario_Id=6,
                Especialidad="Medicina",
                Tipo_Profesional="MEDICO"
            )
            data = profesional.to_dict()
            assert data["Usuario_Id"] == 6
            assert data["Especialidad"] == "Medicina"
            assert data["Tipo_Profesional"] == "MEDICO"
