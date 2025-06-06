from app import db
from datetime import date

class Sesion(db.Model):
    __tablename__ = 'Sesion'
    
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Paciente_Id = db.Column(db.Integer, db.ForeignKey('Paciente.Usuario_Id'), nullable=False)
    Profesional_Id = db.Column(db.Integer, db.ForeignKey('Profesional.Usuario_Id'), nullable=False)
    Fecha_Asignacion = db.Column(db.Date, default=date.today)
    Estado = db.Column(db.String(20), nullable=False, default='PENDIENTE')
    Fecha_Programada = db.Column(db.Date, nullable=False)
    
    __table_args__ = (
        db.CheckConstraint(
            "Estado IN ('PENDIENTE', 'COMPLETADA', 'CANCELADA')",
            name='check_estado_sesion'
        ),
    )
    
    # Relación N:1 con Paciente (muchas sesiones de un paciente)
    paciente = db.relationship('Paciente', back_populates='sesiones')
    
    # Relación N:1 con Profesional (muchas sesiones de un profesional)
    profesional = db.relationship('Profesional', back_populates='sesiones')
    
    # Relación 1:N con Ejercicio_Sesion (una sesión puede tener muchos ejercicios)
    ejercicios_sesion = db.relationship('EjercicioSesion', cascade='all, delete-orphan')
    
