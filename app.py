from flask import Flask
from src.extensiones import init_extensions, db 
from src.config import Config


def create_app():
    app = Flask(__name__, template_folder='src/vistas')
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = 'src/uploads'
    
    # Inicializar extensiones
    init_extensions(app)
    

    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
