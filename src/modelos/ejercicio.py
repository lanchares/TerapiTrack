from src.extensiones import db

class Ejercicio(db.Model):
    """
    Modelo de Ejercicio Terapéutico.
    Representa ejercicios con video demostrativo para rehabilitación.
    """
    __tablename__ = 'Ejercicio'
    
    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Descripcion = db.Column(db.Text, nullable=False)
    Tipo = db.Column(db.String(50), nullable=False)  
    Video = db.Column(db.String(255), nullable=True)  
    Duracion = db.Column(db.Integer, nullable=False)  
    
    # Relación N:M con Profesionales (usando tabla intermedia)
    profesionales = db.relationship('Profesional', secondary='Ejercicio_Profesional',
                                   back_populates='ejercicios')
    
    # Relación N:M con Sesiones a través de Ejercicio_Sesion (tabla intermedia)
    ejercicios_sesion = db.relationship('Ejercicio_Sesion', cascade='all, delete-orphan',
                                         back_populates='ejercicio')
    
    # Métodos propios del modelo Ejercicio

    def duracion_legible(self):
        if self.Duracion is not None:
            minutos = self.Duracion // 60
            segundos = self.Duracion % 60
            return f"{minutos} min {segundos} seg"
        return "No especificada"

    def es_tipo(self, tipo):
        return self.Tipo.lower() == tipo.lower()


    def tiene_video(self):
        return bool(self.Video)

    def __repr__(self):
        """Representación legible para depuración."""
        return f"<Ejercicio Id={self.Id} Nombre={self.Nombre}>"

    def to_dict(self):
        """Serializa el ejercicio a un diccionario."""
        return {
            "Id": self.Id,
            "Nombre": self.Nombre,
            "Descripcion": self.Descripcion,
            "Tipo": self.Tipo,
            "Video": self.Video,
            "Duracion": self.Duracion
        }