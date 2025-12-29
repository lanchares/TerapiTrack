from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import timedelta

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def init_extensions(app):
    """Inicializa todas las extensiones con la app Flask"""
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # ✅ CONFIGURACIÓN DE SESIONES PERSISTENTES
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # Solo True en HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from src.modelos.usuario import Usuario
        return db.session.get(Usuario, int(user_id))
