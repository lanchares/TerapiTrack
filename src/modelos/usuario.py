from extensiones import db
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Usuario(db.Model, UserMixin):
    __tablename__ = 'Usuario'

    Id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Apellidos = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Contraseña = db.Column(db.String(255), nullable=False)
    Rol_Id = db.Column(db.Integer, nullable=False)
    Fecha_Registro = db.Column(db.Date, nullable=False, default=date.today)
    Estado = db.Column(db.Integer, nullable=False, default=1)

    __table_args__ = (
        db.CheckConstraint('Rol_Id IN (0, 1, 2)', name='check_rol_id'),
        db.CheckConstraint('Estado IN (0, 1)', name='check_estado'),
    )
    # Relaciones 1:1 con Paciente
    paciente = db.relationship('Paciente', uselist=False, 
                               back_populates='usuario', 
                               cascade='all, delete-orphan')
    
    # Relaciones 1:1 con Profesional
    profesional = db.relationship('Profesional', uselist=False, 
                                  back_populates='usuario', 
                                  cascade='all, delete-orphan')

    def set_password(self, password):
        """Cifra y almacena la contraseña del usuario."""
        self.Contraseña = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña proporcionada coincide con la almacenada."""
        return check_password_hash(self.Contraseña, password)

    def es_admin(self):
        return self.Rol_Id == 0

    def es_paciente(self):
        return self.Rol_Id == 1

    def es_profesional(self):
        return self.Rol_Id == 2
    
    def obtener_id(self):
        """Devuelve el identificador único del usuario (para Flask-Login)."""
        return str(self.Id)

    def obtener_rol(self):
        """Devuelve el nombre del rol a partir de Rol_Id."""
        roles = {0: 'Administrador', 1: 'Paciente', 2: 'Profesional'}
        return roles.get(self.Rol_Id, 'Desconocido')

    def usuario_activo(self):
        """Indica si el usuario está activo."""
        return self.Estado == 1

    def __repr__(self):
        """Representación legible para depuración."""
        return f"<Usuario {self.Nombre} {self.Apellidos}>"

    def to_dict(self):
        """Serializa el usuario a un diccionario (sin exponer la contraseña)."""
        return {
            "Id": self.Id,
            "Nombre": self.Nombre,
            "Apellidos": self.Apellidos,
            "Email": self.Email,
            "Rol_Id": self.Rol_Id,
            "Fecha_Registro": str(self.Fecha_Registro),
            "Estado": self.Estado
        }