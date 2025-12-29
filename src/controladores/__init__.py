from flask import Blueprint

def register_blueprints(app):
    """Registra todos los blueprints de la aplicación"""
    from .auth_controlador import auth_bp
    from .admin_controlador import admin_bp
    from .paciente_controlador import paciente_bp  
    from .profesional_controlador import profesional_bp  
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(paciente_bp, url_prefix='/paciente')  
    app.register_blueprint(profesional_bp, url_prefix='/profesional')  