from extensiones import db
from datetime import date

class Evaluacion(db.Model):
    __tablename__ = 'Evaluacion'
    
    Ejercicio_Sesion_Id = db.Column(db.Integer, db.ForeignKey('Ejercicio_Sesion.Id'), primary_key=True)
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
    ejercicio_sesion = db.relationship('Ejercicio_Sesion', back_populates='evaluacion')
    
    def es_aprobado(self, minimo=3):
        return self.Puntuacion >= minimo
   
    def resumen(self):
        return f"Puntuación: {self.Puntuacion} - {self.Comentarios or 'Sin comentarios'}"

    def __repr__(self):
        return f"<Evaluacion Ejercicio_Sesion_Id={self.Ejercicio_Sesion_Id} Puntuacion={self.Puntuacion}>"

    def to_dict(self):
        return {
            "Ejercicio_Sesion_Id": self.Ejercicio_Sesion_Id,
            "Puntuacion": self.Puntuacion,
            "Comentarios": self.Comentarios,
            "Fecha_Evaluacion": str(self.Fecha_Evaluacion)
        }
