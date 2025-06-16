from app import create_app
from extensiones import db
from modelos.ejercicio import Ejercicio
from modelos.paciente import Paciente
from modelos.profesional import Profesional
from modelos.sesion import Sesion
from modelos.usuario import Usuario

def test_database_connection():
    """Prueba la conexión a la base de datos y los modelos"""
    app = create_app()
    
    with app.app_context():
        try:
            
            # Probar conexión básica
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            print("Conexión a base de datos exitosa")
            
            # Probar consultas
            usuarios = Usuario.query.all()
            print(f"Usuarios encontrados: {len(usuarios)}")
            
            pacientes = Paciente.query.all()
            print(f"Pacientes encontrados: {len(pacientes)}")
            
            profesionales = Profesional.query.all()
            print(f"Profesionales encontrados: {len(profesionales)}")
            
            ejercicios = Ejercicio.query.all()
            print(f"Ejercicios encontrados: {len(ejercicios)}")
            
            sesiones = Sesion.query.all()
            print(f"Sesiones encontradas: {len(sesiones)}")
            
            # Verificar integridad
            integrity_check = db.session.execute(db.text("PRAGMA integrity_check")).fetchone()
            print(f"Integridad de BD: {integrity_check[0]}")
            
            return True
            
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False

if __name__ == '__main__':
    test_database_connection()
