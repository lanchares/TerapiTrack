from app import db

class Ejercicio(db.Model):
    __tablename__ = 'Ejercicio'
    
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text)
    Tipo = db.Column(db.String(50))
    Video = db.Column(db.String(255))
    Duracion = db.Column(db.Integer)  # En segundos
    
    # Relación N:M con Profesionales (usando tabla intermedia)
    profesionales = db.relationship('Profesional',
                                   secondary='Ejercicio_Profesional',
                                   back_populates='ejercicios')
    
    # Relación N:M con Sesiones a través de Ejercicio_Sesion (tabla intermedia)
    ejercicios_sesion = db.relationship('EjercicioSesion', cascade='all, delete-orphan')
    
   