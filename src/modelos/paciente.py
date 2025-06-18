from src.extensiones import db
from datetime import date

class Paciente(db.Model):
    __tablename__ = 'Paciente'
    
    Usuario_Id = db.Column(db.Integer, db.ForeignKey('Usuario.Id'), primary_key=True)
    Fecha_Nacimiento = db.Column(db.Date, nullable=False)
    Condicion_Medica = db.Column(db.String(450))
    Notas = db.Column(db.Text)
    
    # Relación 1:1 con Usuario 
    usuario = db.relationship('Usuario', back_populates='paciente')
    
    # Relación N:M con Profesionales 
    profesionales = db.relationship('Profesional', secondary='Paciente_Profesional', 
                                    back_populates='pacientes')
    
    # Relación 1:N con Sesiones 
    sesiones = db.relationship('Sesion', cascade='all, delete-orphan', 
                               back_populates='paciente')
    
    def edad(self):
        """Calcula la edad del paciente."""
        if self.Fecha_Nacimiento:
            hoy = date.today()
            return hoy.year - self.Fecha_Nacimiento.year - (
                (hoy.month, hoy.day) < (self.Fecha_Nacimiento.month, self.Fecha_Nacimiento.day)
            )
        return None

    def tiene_sesiones_futuras(self):
        return any(s.Fecha_Programada > date.today() for s in self.sesiones)

    def __repr__(self):
        return f"<Paciente Usuario_Id={self.Usuario_Id}>"

    def to_dict(self):
        return {
            "Usuario_Id": self.Usuario_Id,
            "Fecha_Nacimiento": str(self.Fecha_Nacimiento),
            "Condicion_Medica": self.Condicion_Medica,
            "Notas": self.Notas
        }
