from src.extensiones import db, login_manager
from src.modelos.usuario import Usuario


def test_load_user(app):
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

        user_loader = login_manager._user_callback

        # Debe devolver el usuario cuando existe
        loaded = user_loader(str(usuario.Id))
        assert loaded is not None
        assert loaded.Id == usuario.Id

        # Si no existe, devuelve None
        assert user_loader("999999") is None

