from extensiones import db
from datetime import date

class Paciente_Profesional(db.Model):
    """Tabla intermedia N:M entre Paciente y Profesional"""
    __tablename__ = 'Paciente_Profesional'
    
    Paciente_Id = db.Column(db.Integer, db.ForeignKey('Paciente.Usuario_Id'), primary_key=True)
    Profesional_Id = db.Column(db.Integer, db.ForeignKey('Profesional.Usuario_Id'), primary_key=True)
    Fecha_Asignacion = db.Column(db.Date, nullable=False, default=date.today)
    
    def __repr__(self):
        return f"<PacienteProfesional Paciente_Id={self.Paciente_Id} Profesional_Id={self.Profesional_Id}>"

    def to_dict(self):
        return {
            "Paciente_Id": self.Paciente_Id,
            "Profesional_Id": self.Profesional_Id,
            "Fecha_Asignacion": str(self.Fecha_Asignacion)
        }


class Ejercicio_Profesional(db.Model):
    """Tabla intermedia N:M entre Ejercicio y Profesional"""
    __tablename__ = 'Ejercicio_Profesional'
    
    Profesional_Id = db.Column(db.Integer, db.ForeignKey('Profesional.Usuario_Id'), primary_key=True)
    Ejercicio_Id = db.Column(db.Integer, db.ForeignKey('Ejercicio.Id'), primary_key=True)
    
    def __repr__(self):
        return f"<EjercicioProfesional Usuario_Id={self.Usuario_Id} Ejercicio_Id={self.Ejercicio_Id}>"

    def to_dict(self):
        return {
            "Profesional_Id": self.Profesional_Id,
            "Ejercicio_Id": self.Ejercicio_Id
        }