from app import db
from datetime import date

class Usuario(db.Model):
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
    # Relaciones 1:1
    paciente = db.relationship('Paciente', uselist=False, cascade='all, delete-orphan')
    profesional = db.relationship('Profesional', uselist=False, cascade='all, delete-orphan')
