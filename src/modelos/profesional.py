from src.extensiones import db

class Profesional(db.Model):
    __tablename__ = 'Profesional'
    
    Usuario_Id = db.Column(db.Integer, db.ForeignKey('Usuario.Id'), primary_key=True)
    Especialidad = db.Column(db.String(100), nullable=False)
    Tipo_Profesional = db.Column(db.String(20), nullable=False)
    
    __table_args__ = (
        db.CheckConstraint(
            '"Tipo_Profesional" IN (\'MEDICO\', \'ENFERMERO\', \'TERAPEUTA\', \'PSICOLOGO\')',
            name='check_tipo_profesional'
        ),
    )

    
    # Relación 1:1 con Usuario 
    usuario = db.relationship('Usuario', back_populates='profesional')
    
    # Relación N:M con Pacientes 
    pacientes = db.relationship('Paciente', secondary='Paciente_Profesional',
                               back_populates='profesionales')
    
    # Relación N:M con Ejercicios 
    ejercicios = db.relationship('Ejercicio', secondary='Ejercicio_Profesional',
                                back_populates='profesionales')
    
    # Relación 1:N con Sesiones 
    sesiones = db.relationship('Sesion', cascade='all, delete-orphan',
                                back_populates='profesional')
    
    # Métodos propios del modelo Profesional
    def total_pacientes(self):
        return len(self.pacientes)


    def __repr__(self):
        """Representación legible para depuración."""
        return f"<Profesional Usuario_Id={self.Usuario_Id} Tipo_Profesional={self.Tipo_Profesional} Especialidad={self.Especialidad}>"

    def to_dict(self):
        """Serializa el profesional a un diccionario."""
        return {
            "Usuario_Id": self.Usuario_Id,
            "Especialidad": self.Especialidad,
            "Tipo_Profesional": self.Tipo_Profesional
        }
