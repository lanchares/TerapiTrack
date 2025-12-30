from src.extensiones import db
from datetime import datetime

class Sesion(db.Model):
    """
    Modelo de Sesión Terapéutica.
    Representa una sesión programada con ejercicios asignados a un paciente.
    """
    __tablename__ = 'Sesion'
    
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Paciente_Id = db.Column(db.Integer, db.ForeignKey('Paciente.Usuario_Id'), nullable=False)
    Profesional_Id = db.Column(db.Integer, db.ForeignKey('Profesional.Usuario_Id'), nullable=False)
    Fecha_Asignacion = db.Column(db.DateTime, nullable=False, default=datetime.now)
    Estado = db.Column(db.String(20), nullable=False)
    Fecha_Programada = db.Column(db.DateTime, nullable=False)
    
    __table_args__ = (
    db.CheckConstraint('"Estado" IN (\'PENDIENTE\', \'COMPLETADA\', \'CANCELADA\')', name='check_estado_sesion'),
)

    
    # Relación N:1 con Paciente (muchas sesiones de un paciente)
    paciente = db.relationship('Paciente', back_populates='sesiones')
    
    # Relación N:1 con Profesional (muchas sesiones de un profesional)
    profesional = db.relationship('Profesional', back_populates='sesiones')
    
    # Relación 1:N con Ejercicio_Sesion (una sesión puede tener muchos ejercicios)
    ejercicios_sesion = db.relationship('Ejercicio_Sesion', cascade='all, delete-orphan',
                                        back_populates='sesion')
    
    # Métodos propios del modelo Sesion
    def es_pendiente(self):
        return self.Estado == 'PENDIENTE'
    
    def es_completada(self):
        return self.Estado == 'COMPLETADA'

    def es_cancelada(self):
        return self.Estado == 'CANCELADA'

    def obtener_ejercicios(self):
        return len(self.ejercicios_sesion)
        
    def fecha_programada_legible(self):
        return self.Fecha_Programada.strftime('%d/%m/%Y') if self.Fecha_Programada else ""
    
    def hora_programada_legible(self):
        return self.Fecha_Programada.strftime('%H:%M') if self.Fecha_Programada else ""

    def __repr__(self):
        """Representación legible para depuración."""
        return f"<Sesion Id={self.Id} Estado={self.Estado} Fecha_Programada={self.Fecha_Programada}>"

    def to_dict(self):
        """Serializa la sesión a un diccionario."""
        return {
            "Id": self.Id,
            "Paciente_Id": self.Paciente_Id,
            "Profesional_Id": self.Profesional_Id,
            "Fecha_Asignacion": str(self.Fecha_Asignacion),
            "Estado": self.Estado,
            "Fecha_Programada": str(self.Fecha_Programada)
        }
