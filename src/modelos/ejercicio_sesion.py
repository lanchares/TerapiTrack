from extensiones import db

class Ejercicio_Sesion(db.Model):
    __tablename__ = 'Ejercicio_Sesion'
    
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Sesion_Id = db.Column(db.Integer, db.ForeignKey('Sesion.Id'), nullable=False)
    Ejercicio_Id = db.Column(db.Integer, db.ForeignKey('Ejercicio.Id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('Sesion_Id', 'Ejercicio_Id', name='unique_ejercicio_sesion'),
    )
    
    # Relación N:1 con Sesion
    sesion = db.relationship('Sesion', back_populates='ejercicios_sesion')
    
    # Relación N:1 con Ejercicio
    ejercicio = db.relationship('Ejercicio', back_populates='ejercicios_sesion')
    
    # Relación 1:1 con VideoRespuesta
    video_respuesta = db.relationship('VideoRespuesta', uselist=False, 
                                      cascade='all, delete-orphan')
    
    # Relación 1:1 con Evaluacion
    evaluacion = db.relationship('Evaluacion', uselist=False, 
                                 cascade='all, delete-orphan')
    

    def tiene_video_respuesta(self):
        return self.video_respuesta is not None

    def tiene_evaluacion(self):
        return self.evaluacion is not None

    def obtener_puntuacion(self):
        return self.evaluacion.Puntuacion if self.evaluacion else None

    def obtener_ruta_video(self):
        return self.video_respuesta.Ruta_Almacenamiento if self.video_respuesta else None

    def __repr__(self):
        return f"<Ejercicio_Sesion Id={self.Id} Sesion_Id={self.Sesion_Id} Ejercicio_Id={self.Ejercicio_Id}>"

    def to_dict(self):
        return {
            "Id": self.Id,
            "Sesion_Id": self.Sesion_Id,
            "Ejercicio_Id": self.Ejercicio_Id
        }