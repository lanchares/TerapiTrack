from extensiones import db

class EjercicioSesion(db.Model):
    __tablename__ = 'Ejercicio_Sesion'
    
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Sesion_Id = db.Column(db.Integer, db.ForeignKey('Sesion.Id'), nullable=False)
    Ejercicio_Id = db.Column(db.Integer, db.ForeignKey('Ejercicio.Id'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('Sesion_Id', 'Ejercicio_Id', name='unique_ejercicio_sesion'),
        db.UniqueConstraint('Sesion_Id', 'Orden', name='unique_orden_sesion'),
    )
    
    # Relación N:1 con Sesion
    sesion = db.relationship('Sesion', back_populates='ejercicios_sesion')
    
    # Relación N:1 con Ejercicio
    ejercicio = db.relationship('Ejercicio', back_populates='ejercicios_sesion')
    
    # Relación 1:1 con VideoRespuesta
    video_respuesta = db.relationship('VideoRespuesta', uselist=False, cascade='all, delete-orphan')
    
    # Relación 1:1 con Evaluacion
    evaluacion = db.relationship('Evaluacion', uselist=False, cascade='all, delete-orphan')
    
