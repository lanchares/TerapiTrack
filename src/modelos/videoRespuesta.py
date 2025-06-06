from app import db
from datetime import date, datetime

class VideoRespuesta(db.Model):
    __tablename__ = 'Video_Respuesta'
    
    Ejercicio_Sesion_Id = db.Column(db.Integer, 
                                   db.ForeignKey('Ejercicio_Sesion.Id'), 
                                   primary_key=True)
    Ruta_Almacenamiento = db.Column(db.String(255), nullable=False)
    Fecha_Expiracion = db.Column(db.Date)
    
    # Relación 1:1 con EjercicioSesion
    ejercicio_sesion = db.relationship('EjercicioSesion', back_populates='video_respuesta')
    