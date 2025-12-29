from flask_wtf import FlaskForm
from wtforms import DateTimeField, FileField, SelectMultipleField, StringField, PasswordField, SelectField, DateField, TextAreaField, SubmitField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, NumberRange
from wtforms.fields import DateTimeLocalField

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

class CrearUsuarioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    
    # ← CORREGIR: Usar strings para evitar problema con 0
    rol_id = SelectField('Rol', 
                        choices=[
                            ('0', 'Administrador'),   # ← Strings en lugar de ints
                            ('1', 'Paciente'), 
                            ('2', 'Profesional')
                        ],
                        validators=[DataRequired()])
    # Sin coerce=int, maneja strings
    
    # Campos para Paciente (opcionales según rol)
    fecha_nacimiento = DateField('Fecha de Nacimiento', validators=[Optional()])
    condicion_medica = StringField('Condición Médica', validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional()])
    
    # Campos para Profesional (opcionales según rol)
    especialidad = StringField('Especialidad', validators=[Optional()])
    tipo_profesional = SelectField('Tipo de Profesional',
                                  choices=[
                                      ('', 'Selecciona tipo...'),
                                      ('MEDICO', 'Médico'),
                                      ('TERAPEUTA', 'Terapeuta'),
                                      ('PSICOLOGO', 'Psicólogo'),
                                      ('ENFERMERO', 'Enfermero')
                                  ],
                                  validators=[Optional()])
    
    submit = SubmitField('Guardar Usuario')

class VincularPacienteProfesionalForm(FlaskForm):
    paciente_id = SelectField('Paciente', 
                             choices=[],  # Se llenan dinámicamente
                             validators=[DataRequired()],
                             coerce=int)
    profesional_id = SelectField('Profesional', 
                                choices=[],  # Se llenan dinámicamente
                                validators=[DataRequired()],
                                coerce=int)
    submit = SubmitField('Crear Vinculación')

class CambiarContrasenaForm(FlaskForm):
    contrasena_actual = PasswordField('Contraseña Actual', validators=[DataRequired()])
    nueva_contrasena = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    confirmar_contrasena = PasswordField('Confirmar Contraseña', 
                                       validators=[DataRequired(), EqualTo('nueva_contrasena', message='Las contraseñas deben coincidir')])
    submit = SubmitField('Cambiar Contraseña')

class RecuperarContrasenaForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Recuperar Contraseña')

class EditarUsuarioForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Nueva Contraseña (opcional)', validators=[Optional(), Length(min=6)])
    
    # Campos condicionales
    condicion_medica = StringField('Condición Médica', validators=[Optional()])
    notas = TextAreaField('Notas', validators=[Optional()])
    especialidad = StringField('Especialidad', validators=[Optional()])
    tipo_profesional = SelectField('Tipo de Profesional',
                                  choices=[
                                      ('', 'Selecciona tipo...'),
                                      ('MEDICO', 'Médico'),
                                      ('TERAPEUTA', 'Terapeuta'),
                                      ('PSICOLOGO', 'Psicólogo'),
                                      ('ENFERMERO', 'Enfermero')
                                  ],
                                  validators=[Optional()])
    
    submit = SubmitField('Actualizar Usuario')

class ConfiguracionForm(FlaskForm):
    retencion_videos = SelectField('Política de Retención de Videos',
                                  choices=[
                                      ('30', '30 días'),
                                      ('60', '60 días'),
                                      ('90', '90 días'),
                                      ('180', '180 días'),
                                      ('365', '1 año')
                                  ],
                                  validators=[DataRequired()])
    
    limite_almacenamiento = SelectField('Límite de Almacenamiento por Usuario',
                                      choices=[
                                          ('1', '1 GB'),
                                          ('2', '2 GB'),
                                          ('5', '5 GB'),
                                          ('10', '10 GB'),
                                          ('unlimited', 'Sin límite')
                                      ],
                                      validators=[DataRequired()])
    
    notificaciones_email = SelectField('Notificaciones por Email',
                                     choices=[
                                         ('enabled', 'Habilitadas'),
                                         ('disabled', 'Deshabilitadas')
                                     ],
                                     validators=[DataRequired()])
    
    backup_automatico = SelectField('Backup Automático',
                                  choices=[
                                      ('daily', 'Diario'),
                                      ('weekly', 'Semanal'),
                                      ('monthly', 'Mensual'),
                                      ('disabled', 'Deshabilitado')
                                  ],
                                  validators=[DataRequired()])
    
    submit = SubmitField('Guardar Configuración')

# En forms.py:
class CrearEjercicioForm(FlaskForm):
    nombre = StringField('Nombre del ejercicio', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    tipo = StringField('Tipo de ejercicio', validators=[DataRequired()],  # ✅ Campo de texto libre
                      render_kw={"placeholder": "Ej: Movilidad, Fortalecimiento, Equilibrio..."})
    video = FileField('Video demostrativo', validators=[DataRequired()])
    submit = SubmitField('Crear Ejercicio')


class EvaluacionForm(FlaskForm):
    puntuacion = IntegerField('Puntuación (1-5)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=5)
    ])
    comentarios = TextAreaField('Comentarios')

class AsignarSesionForm(FlaskForm):
    paciente_id = SelectField('Paciente', coerce=int, validators=[DataRequired()])
    fecha_programada = DateTimeLocalField(
        'Fecha Programada',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )
    submit = SubmitField('Asignar Sesión')

class CrearSesionDirectaForm(FlaskForm):
    paciente_id = SelectField('Paciente', coerce=int, validators=[DataRequired()])
    ejercicios = SelectMultipleField('Ejercicios', coerce=int, validators=[DataRequired()])
    fecha_programada = DateTimeLocalField(
        'Fecha Programada',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )
    submit = SubmitField('Crear Sesión')


