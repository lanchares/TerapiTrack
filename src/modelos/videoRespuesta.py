from src.extensiones import db
from datetime import date, datetime

class VideoRespuesta(db.Model):
    """
    Modelo de Video de Respuesta.
    Almacena videos grabados por pacientes durante sesiones terapéuticas.
    """
    __tablename__ = 'Video_Respuesta'
    
    Ejercicio_Sesion_Id = db.Column(db.Integer, db.ForeignKey('Ejercicio_Sesion.Id'), primary_key=True)
    Ruta_Almacenamiento = db.Column(db.String(255), nullable=False)
    Fecha_Expiracion = db.Column(db.Date)
    
    # Relación 1:1 con EjercicioSesion
    ejercicio_sesion = db.relationship('Ejercicio_Sesion', back_populates='video_respuesta')
    
    def nombre_archivo(self):
        import os
        return os.path.basename(self.Ruta_Almacenamiento)

    def __repr__(self):
        return f"<VideoRespuesta Ejercicio_Sesion_Id={self.Ejercicio_Sesion_Id}>"

    def to_dict(self):
        return {
            "Ejercicio_Sesion_Id": self.Ejercicio_Sesion_Id,
            "Ruta_Almacenamiento": self.Ruta_Almacenamiento,
            "Fecha_Expiracion": str(self.Fecha_Expiracion)
        }