"""
Tests del modelo Usuario.
Prueba CRUD, validación de contraseñas, roles, estados y restricciones.
"""

import pytest
from datetime import date
from src.modelos.usuario import Usuario
from src.extensiones import db

class TestUsuario:
    """Suite de tests para el modelo Usuario."""

    def test_usuario_crud(self, app):
        """Prueba operaciones CRUD básicas (crear, leer, actualizar, eliminar)."""
        with app.app_context():
            usuario = Usuario(
                Nombre="Alberto",
                Apellidos="Lanchares Diez",
                Email="alberto@demo.com",
                Contraseña="1234",
                Rol_Id=1
            )
            usuario.set_contraseña("1234")
            db.session.add(usuario)
            db.session.commit()
            assert Usuario.query.count() == 1
            usuario.Nombre = "Leire"
            usuario.Apellidos = "Garcia Rodriguez"
            db.session.commit()
            assert Usuario.query.first().Nombre == "Leire"
            db.session.delete(usuario)
            db.session.commit()
            assert Usuario.query.count() == 0

    def test_usuario_contraseña(self, app):
        """Prueba el cifrado y verificación de contraseñas con bcrypt."""
        with app.app_context():
            usuario = Usuario(
                Nombre="Alberto",
                Apellidos="Lanchares Diez",
                Email="alberto@demo.com",
                Contraseña="1234",
                Rol_Id=1
            )
            usuario.set_contraseña("1234")
            db.session.add(usuario)
            db.session.commit()
            assert usuario.check_contraseña("1234")
            assert not usuario.check_contraseña("otra")

    def test_usuario_roles_y_estado(self, app):
        """Prueba los métodos de verificación de roles y estados de usuario."""
        with app.app_context():
            admin = Usuario(Nombre="Admin", Apellidos="Root", Email="admin@demo.com", Contraseña="1234", Rol_Id=0, Estado=1)
            paciente = Usuario(Nombre="Leire", Apellidos="Garcia Rodriguez", Email="leire@demo.com", Contraseña="1234", Rol_Id=1, Estado=0)
            profesional = Usuario(Nombre="Alberto", Apellidos="Lanchares Diez", Email="alberto.prof@demo.com", Contraseña="1234", Rol_Id=2, Estado=1)
            db.session.add_all([admin, paciente, profesional])
            db.session.commit()
            assert admin.es_admin()
            assert paciente.es_paciente()
            assert profesional.es_profesional()
            assert admin.usuario_activo()
            assert not paciente.usuario_activo()

    def test_usuario_obtener_rol_desconocido(self, app):
        """Prueba que obtener_rol() devuelve 'Desconocido' para roles inválidos."""
        with app.app_context():
            usuario = Usuario(Nombre="Test", Apellidos="User", Email="test@demo.com", Contraseña="1234", Rol_Id=99)
            assert usuario.obtener_rol() == "Desconocido"

    def test_usuario_email_unico(self, app):
        """Prueba la restricción UNIQUE del campo Email."""
        with app.app_context():
            usuario1 = Usuario(Nombre="Alberto", Apellidos="Lanchares Diez", Email="alberto@demo.com", Contraseña="1234", Rol_Id=1)
            usuario1.set_contraseña("1234")
            db.session.add(usuario1)
            db.session.commit()
            usuario2 = Usuario(Nombre="Leire", Apellidos="Garcia Rodriguez", Email="alberto@demo.com", Contraseña="1234", Rol_Id=1)
            usuario2.set_contraseña("1234")
            db.session.add(usuario2)
            with pytest.raises(Exception):
                db.session.commit()
                db.session.rollback()

    def test_usuario_restricciones_check(self, app):
        """Prueba las restricciones CHECK de Rol_Id y Estado."""
        with app.app_context():
            usuario = Usuario(Nombre="Error", Apellidos="Rol", Email="error@demo.com", Contraseña="1234", Rol_Id=5)
            usuario.set_contraseña("1234")
            db.session.add(usuario)
            with pytest.raises(Exception):
                db.session.commit()
                db.session.rollback()
            usuario2 = Usuario(Nombre="Error", Apellidos="Estado", Email="error2@demo.com", Contraseña="1234", Rol_Id=1, Estado=3)
            usuario2.set_contraseña("1234")
            db.session.add(usuario2)
            with pytest.raises(Exception):
                db.session.commit()
                db.session.rollback()

    def test_usuario_to_dict_y_repr(self, app):
        """Prueba los métodos to_dict() y __repr__()."""
        with app.app_context():
            usuario = Usuario(
                Nombre="Leire",
                Apellidos="Garcia Rodriguez",
                Email="leire@demo.com",
                Contraseña="1234",
                Rol_Id=1
            )
            usuario.set_contraseña("1234")
            db.session.add(usuario)
            db.session.commit()
            data = usuario.to_dict()
            assert "Contraseña" not in data
            assert data["Nombre"] == "Leire"
            # Cobertura total de __repr__
            esperado = f"<Usuario {usuario.Nombre} {usuario.Apellidos}>"
            assert repr(usuario) == esperado

    def test_usuario_obtener_id(self, app):
        """Prueba el método get_id() requerido por Flask-Login."""
        with app.app_context():
            usuario = Usuario(
                Nombre="Alberto",
                Apellidos="Lanchares Diez",
                Email="alberto@demo.com",
                Contraseña="1234",
                Rol_Id=1
            )
            usuario.set_contraseña("1234")
            db.session.add(usuario)
            db.session.commit()
            assert usuario.get_id() == str(usuario.Id)
