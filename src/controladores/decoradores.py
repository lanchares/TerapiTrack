"""
Decoradores de autorización para controlar acceso por roles.
Define decoradores para rutas que requieren permisos específicos.
"""

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def admin_required(f):
    """
    Decorador que restringe el acceso solo a administradores (Rol_Id = 0).
    
    Args:
        f: Función de vista a decorar
        
    Returns:
        Función decorada con validación de rol administrador
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.Rol_Id != 0:
            flash('Acceso restringido a administradores', 'error')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def profesional_required(f):
    """
    Decorador que restringe el acceso solo a profesionales sanitarios (Rol_Id = 2).
    
    Args:
        f: Función de vista a decorar
        
    Returns:
        Función decorada con validación de rol profesional
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('auth.login'))
            
        if current_user.Rol_Id != 2:
            flash('Acceso restringido a profesionales', 'error')
            abort(403)  
        return f(*args, **kwargs)
    return decorated_function

def paciente_required(f):
    """
    Decorador que restringe el acceso solo a pacientes (Rol_Id = 1).
    
    Args:
        f: Función de vista a decorar
        
    Returns:
        Función decorada con validación de rol paciente
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('auth.login'))
            
        if current_user.Rol_Id != 1:
            flash('Acceso restringido a pacientes', 'error')
            abort(403) 
        return f(*args, **kwargs)
    return decorated_function

