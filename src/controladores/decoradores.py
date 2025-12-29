from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.Rol_Id != 0:
            flash('Acceso restringido a administradores', 'error')
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def profesional_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('auth.login'))
            
        if current_user.Rol_Id != 2:
            flash('Acceso restringido a profesionales', 'error')
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def paciente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('auth.login'))
            
        if current_user.Rol_Id != 1:
            flash('Acceso restringido a pacientes', 'error')
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

