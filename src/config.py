import os
from datetime import timedelta

class Config:
    """
    Configuración principal de la aplicación Flask.
    Gestiona la conexión a base de datos, uploads, sesiones y seguridad.
    """
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or '1234albertolancharesdiez'
    
    # Ajuste para Heroku: convierte postgres:// a postgresql://
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Si no hay DATABASE_URL en Heroku, usa SQLite local
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///TerapiTrack.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración para uploads de archivos
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'src/static/uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    
    # Configuración de sesiones persistentes
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_REFRESH_EACH_REQUEST = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # En producción (Heroku), activa cookies seguras con HTTPS
    REMEMBER_COOKIE_SECURE = True if os.environ.get('HEROKU') else False
    SESSION_COOKIE_SECURE = True if os.environ.get('HEROKU') else False
    SESSION_COOKIE_HTTPONLY = True
