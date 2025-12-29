from datetime import datetime
from flask import Flask
from src.extensiones import init_extensions, db
from src.config import Config
from flask_wtf.csrf import CSRFProtect


def create_app():
    app = Flask(__name__, template_folder='src/vistas', static_folder='src/static')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = 'src/static/uploads'
    
    # Inicializar protección CSRF
    csrf = CSRFProtect(app)
    
    # Inicializar extensiones
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
    
    # Registrar filtro de fecha
    @app.template_filter('datetimeformat')
    def datetimeformat_filter(value, format='%d/%m/%Y %H:%M'):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
        return value.strftime(format)

    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    return app

# Crear la aplicación para que Gunicorn pueda importarla
app = create_app()

if __name__ == '__main__':
    # Solo en desarrollo local
    app.run(debug=True)
