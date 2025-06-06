from extensiones import db
from datetime import date

class Evaluacion(db.Model):
    __tablename__ = 'Evaluacion'
    
    Ejercicio_Sesion_Id = db.Column(db.Integer, 
                                   db.ForeignKey('Ejercicio_Sesion.Id'), 
                                   primary_key=True)
    Puntuacion = db.Column(db.Integer, nullable=False)
    Comentarios = db.Column(db.Text)
    Fecha_Evaluacion = db.Column(db.Date, nullable=False, default=date.today)
    
    __table_args__ = (
        db.CheckConstraint(
            'Puntuacion >= 1 AND Puntuacion <= 5',
            name='check_puntuacion_rango'
        ),
    )
    
    # Relación 1:1 con EjercicioSesion
    ejercicio_sesion = db.relationship('EjercicioSesion', back_populates='evaluacion')
    
   