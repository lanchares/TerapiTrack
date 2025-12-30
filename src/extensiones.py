from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from datetime import timedelta

# Instancias globales de extensiones
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()  # <- instancia global

def init_extensions(app):
    """
    Inicializa todas las extensiones con la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app) 

    # Configuración de sesiones
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    @login_manager.user_loader
    def load_user(user_id):
        """Carga el usuario actual desde la base de datos por su ID."""
        from src.modelos.usuario import Usuario
        return db.session.get(Usuario, int(user_id))
