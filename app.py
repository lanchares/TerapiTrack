"""
Punto de entrada principal de la aplicación TerapiTrack.

Este módulo inicializa la aplicación Flask, configura extensiones,
registra blueprints y define filtros personalizados de Jinja2.
"""
from datetime import datetime
from flask import Flask
from src.extensiones import init_extensions, db
from src.config import Config


def create_app():
    """
    Factory para crear y configurar la aplicación Flask.
    
    Configura:
        - Extensiones (SQLAlchemy, Flask-Login, CSRF, Bcrypt)
        - Blueprints (auth, admin, profesional, paciente)
        - Filtros de plantilla personalizados
        - Base de datos
    
    Returns:
        Flask: Instancia de la aplicación configurada
    """
    app = Flask(__name__, template_folder='src/vistas', static_folder='src/static')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = 'src/static/uploads'

    # Inicializar extensiones (incluye CSRF desde extensiones)
    init_extensions(app)

    # Registrar blueprints
    from src.controladores.auth_controlador import auth_bp
    from src.controladores.admin_controlador import admin_bp
    from src.controladores.profesional_controlador import profesional_bp
    from src.controladores.paciente_controlador import paciente_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(profesional_bp, url_prefix='/profesional')
    app.register_blueprint(paciente_bp, url_prefix='/paciente')

    # Filtro para formatear fechas
    @app.template_filter('datetimeformat')
    def datetimeformat_filter(value, format='%d/%m/%Y %H:%M'):
        """
        Filtro Jinja2 para formatear fechas.
        
        Args:
            value: Fecha (datetime, str o None)
            format: Formato de salida (por defecto: día/mes/año hora:minuto)
            
        Returns:
            str: Fecha formateada o cadena vacía si es None
        """
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
        return value.strftime(format)

    # Filtro para formatear duración de ejercicios (segundos -> Xm Ys)
    @app.template_filter('formatear_duracion')
    def formatear_duracion(segundos):
        """
        Filtro Jinja2 para convertir segundos a formato legible.
        
        Args:
            segundos: Duración en segundos (int)
            
        Returns:
            str: Duración formateada (ej. "3m 45s" o "30s")
        """
        try:
            segundos = int(segundos or 0)
        except (TypeError, ValueError):
            segundos = 0
        minutos = segundos // 60
        resto = segundos % 60
        if minutos > 0:
            return f"{minutos}m {resto}s"
        return f"{resto}s"
    

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
