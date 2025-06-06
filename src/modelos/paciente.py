from extensiones import db
from datetime import date

class Paciente(db.Model):
    __tablename__ = 'Paciente'
    
    Usuario_Id = db.Column(db.Integer, db.ForeignKey('Usuario.Id'), primary_key=True)
    Fecha_Nacimiento = db.Column(db.Date, nullable=False)
    Condicion_Medica = db.Column(db.String(255))
    Notas = db.Column(db.Text)
    
    # Relación 1:1 con Usuario 
    usuario = db.relationship('Usuario', back_populates='paciente')
    
    # Relación N:M con Profesionales 
    profesionales = db.relationship('Profesional', 
                                  secondary='Paciente_Profesional',
                                  back_populates='pacientes')
    
    # Relación 1:N con Sesiones 
    sesiones = db.relationship('Sesion', cascade='all, delete-orphan')
    
