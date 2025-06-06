from app import db
from datetime import date

class PacienteProfesional(db.Model):
    """Tabla intermedia N:M entre Paciente y Profesional"""
    __tablename__ = 'Paciente_Profesional'
    
    Paciente_Id = db.Column(db.Integer, db.ForeignKey('Paciente.Usuario_Id'), primary_key=True)
    Profesional_Id = db.Column(db.Integer, db.ForeignKey('Profesional.Usuario_Id'), primary_key=True)
    Fecha_Asignacion = db.Column(db.Date, default=date.today)
    


class EjercicioProfesional(db.Model):
    """Tabla intermedia N:M entre Ejercicio y Profesional"""
    __tablename__ = 'Ejercicio_Profesional'
    
    Usuario_Id = db.Column(db.Integer, db.ForeignKey('Profesional.Usuario_Id'), primary_key=True)
    Ejercicio_Id = db.Column(db.Integer, db.ForeignKey('Ejercicio.Id'), primary_key=True)
    
