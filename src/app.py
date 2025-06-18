from flask import Flask
from src.extensiones import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///TerapiTrack.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = '1234'

    db.init_app(app)

    # Importar modelos para asegurar que se registran en SQLAlchemy
    from src.modelos.usuario import Usuario
    from src.modelos.paciente import Paciente
    from src.modelos.profesional import Profesional
    from src.modelos.ejercicio import Ejercicio
    from src.modelos.sesion import Sesion
    from src.modelos.ejercicio_sesion import Ejercicio_Sesion
    from src.modelos.evaluacion import Evaluacion
    from src.modelos.videoRespuesta import VideoRespuesta
    from src.modelos.asociaciones import Paciente_Profesional, Ejercicio_Profesional

    @app.route('/')
    def index():
        return "<h1>TerapiTrack - Backend funcionando</h1>"

    return app

def init_db():
    """Inicializa la base de datos creando todas las tablas"""
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_db()
    app = create_app()
    app.run(debug=True)
