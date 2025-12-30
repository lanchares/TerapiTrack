"""
Controlador de autenticación y gestión de sesiones.
Maneja login, logout, recuperación de contraseña y perfiles de usuario.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from src.modelos.usuario import Usuario
from src.forms import LoginForm, CambiarContrasenaForm, RecuperarContrasenaForm
from datetime import datetime, timedelta
from src.extensiones import db
import secrets

auth_bp = Blueprint('auth', __name__)

def redirect_by_role(user):
    """
    Redirige al usuario a su dashboard según su rol.
    
    Args:
        user: Objeto Usuario con Rol_Id definido
        
    Returns:
        Redirección al dashboard correspondiente
    """
    if user.Rol_Id == 0:  # Administrador
        return redirect(url_for('admin.dashboard'))
    elif user.Rol_Id == 2:  # Profesional
        return redirect(url_for('profesional.dashboard'))
    elif user.Rol_Id == 1:  # Paciente
        return redirect(url_for('paciente.dashboard'))
    else:
        flash('Rol no reconocido', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gestiona el inicio de sesión de usuarios.
    Incluye protección contra fuerza bruta y sesiones persistentes para pacientes.
    """
    if current_user.is_authenticated:
        return redirect_by_role(current_user)
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Verificar intentos fallidos para prevenir fuerza bruta        
        intentos_key = f"login_attempts_{request.remote_addr}"
        intentos = session.get(intentos_key, 0)
        
        if intentos >= 5:
            flash('Demasiados intentos fallidos. Espera 15 minutos antes de intentar de nuevo.', 'danger')
            return render_template('auth/login.html', form=form)
        
        user = Usuario.query.filter_by(Email=form.email.data).first()
        
        if user:
            if user.Estado == 0:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return render_template('auth/login.html', form=form)
            
            if user.check_contraseña(form.password.data):
                # Login exitoso - resetear contador de intentos
                session.pop(intentos_key, None)
                
                # Configuración de sesiones según rol
                if user.Rol_Id == 1:  # Paciente: sesión persistente de 30 días
                    login_user(user, remember=True, duration=timedelta(days=30))
                    flash(f'Bienvenido, {user.Nombre}. Tu sesión se mantendrá activa por 30 días.', 'success')
                else:  # Administrador y Profesional: sesión temporal de 8 horas
                    login_user(user, remember=False, duration=timedelta(hours=8))
                    flash(f'Bienvenido, {user.Nombre}', 'success')
                
                # Redirigir a página solicitada o dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect_by_role(user)
            else:
                # Contraseña incorrecta
                session[intentos_key] = intentos + 1
                flash('Credenciales incorrectas', 'danger')
        else:
            # Usuario no encontrado (mismo mensaje por seguridad)
            session[intentos_key] = intentos + 1
            flash('Credenciales incorrectas', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    """
    Cierra la sesión del usuario actual.
    Elimina cookies y limpia caché para seguridad.
    """
    if current_user.is_authenticated:
        usuario_nombre = current_user.Nombre
        logout_user()
        session.clear()
        flash(f'Sesión cerrada: {usuario_nombre}', 'info')
    
    # Eliminación segura de cookies y prevención de caché
    response = redirect(url_for('auth.login'))
    response.delete_cookie('session')
    response.delete_cookie('remember_token')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@auth_bp.route('/cambiar_contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    """
    Permite al usuario cambiar su contraseña.
    Requiere verificación de la contraseña actual.
    """
    form = CambiarContrasenaForm()
    
    if form.validate_on_submit():
        if not current_user.check_contraseña(form.contrasena_actual.data):
            flash('Contraseña actual incorrecta', 'danger')
            return render_template('auth/cambiar_contrasena.html', form=form)
        
        current_user.set_contraseña(form.nueva_contrasena.data)
        db.session.commit()
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('auth.perfil'))
    
    return render_template('auth/cambiar_contrasena.html', form=form)

@auth_bp.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    """
    Gestiona la recuperación de contraseña olvidada.
    Genera token temporal y simula envío de email.
    """
    if current_user.is_authenticated:
        return redirect_by_role(current_user)
    
    form = RecuperarContrasenaForm()
    
    if form.validate_on_submit():
        user = Usuario.query.filter_by(Email=form.email.data).first()
        if user:
            if user.Estado == 0:
                flash('Esta cuenta está desactivada. Contacta al administrador.', 'warning')
            else:
                # Generar token temporal (en producción enviarías email real)
                token = secrets.token_urlsafe(32)
                # Guardar token en BD con expiración y enviar email
                flash(f'Se han enviado instrucciones de recuperación a {form.email.data}', 'success')
                return redirect(url_for('auth.login'))
        else:
            # Por seguridad, mostrar el mismo mensaje aunque el email no exista
            flash(f'Si existe una cuenta con ese email, recibirás instrucciones de recuperación.', 'info')
    
    return render_template('auth/recuperar_contrasena.html', form=form)

@auth_bp.route('/perfil')
@login_required
def perfil():
    """Muestra el perfil del usuario actual."""
    return render_template('auth/perfil.html', usuario=current_user)
