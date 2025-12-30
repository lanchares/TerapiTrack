"""
Controlador del administrador del sistema.
Gestiona usuarios, vinculaciones, configuración y estadísticas.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from src.controladores.decoradores import admin_required
from src.forms import CrearUsuarioForm, VincularPacienteProfesionalForm, EditarUsuarioForm, ConfiguracionForm
from src.modelos.usuario import Usuario
from src.modelos.paciente import Paciente
from src.modelos.profesional import Profesional
from src.modelos.asociaciones import Paciente_Profesional
from src.extensiones import db
from datetime import date, datetime, timedelta
import csv
from io import StringIO
import json
import os

admin_bp = Blueprint('admin', __name__)

def cargar_configuracion():
    """
    Carga la configuración del sistema desde archivo JSON.
    Si no existe, crea uno con valores por defecto.
    
    Returns:
        dict: Configuración del sistema
    """
    config_path = os.path.join('config', 'sistema.json')
        
    config_default = {
        'retencion_videos': '30',
        'limite_almacenamiento': '2',
        'notificaciones_email': 'enabled',
        'backup_automatico': 'weekly',
        'ultima_modificacion': datetime.now().isoformat(),
        'modificado_por': None
    }
    
    try:
        os.makedirs('config', exist_ok=True)
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_default, f, indent=2, ensure_ascii=False)
            return config_default
            
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return config_default

def guardar_configuracion(nueva_config):
    """
    Guarda la configuración del sistema en archivo JSON.
    
    Args:
        nueva_config: Diccionario con la nueva configuración
        
    Returns:
        bool: True si se guardó correctamente, False en caso de error
    """
    config_path = os.path.join('config', 'sistema.json')
    
    try:
        nueva_config['ultima_modificacion'] = datetime.now().isoformat()
        nueva_config['modificado_por'] = current_user.Id
        
        os.makedirs('config', exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(nueva_config, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error guardando configuración: {e}")
        return False

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal del administrador con estadísticas generales."""
    stats = {
        'total_usuarios': Usuario.query.count(),
        'total_pacientes': Usuario.query.filter_by(Rol_Id=1, Estado=1).count(),
        'total_profesionales': Usuario.query.filter_by(Rol_Id=2, Estado=1).count(),
        'usuarios_inactivos': Usuario.query.filter_by(Estado=0).count(),
        'nuevos_usuarios_mes': Usuario.query.filter(
            Usuario.Fecha_Registro >= datetime.now() - timedelta(days=30)
        ).count(),
        'usuarios_activos_24h': 0,
        'total_vinculaciones': Paciente_Profesional.query.count()
    }
    
    usuarios_recientes = Usuario.query.order_by(
        Usuario.Fecha_Registro.desc()
    ).limit(5).all()
    
    actividad_reciente = []
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         usuarios_recientes=usuarios_recientes,
                         actividad_reciente=actividad_reciente)

@admin_bp.route('/usuarios')
@login_required
@admin_required
def listar_usuarios():
    """Lista todos los usuarios con filtros de búsqueda, rol y estado."""
    search = request.args.get('search', '')
    rol_filter = request.args.get('rol', '')
    estado_filter = request.args.get('estado', '')
    
    query = Usuario.query
    
    if search:
        query = query.filter(
            db.or_(
                Usuario.Nombre.contains(search),
                Usuario.Apellidos.contains(search),
                Usuario.Email.contains(search)
            )  
        )
    
    if rol_filter:
        query = query.filter(Usuario.Rol_Id == int(rol_filter))
    
    if estado_filter:
        query = query.filter(Usuario.Estado == int(estado_filter))
    
    usuarios = query.order_by(Usuario.Fecha_Registro.desc()).all()
    
    return render_template('admin/usuarios.html',
                         usuarios=usuarios,
                         search=search,
                         rol_filter=rol_filter,
                         estado_filter=estado_filter)

@admin_bp.route('/usuario/<int:user_id>')
@login_required
@admin_required
def ver_usuario(user_id):
    """
    Muestra los detalles completos de un usuario específico.
    Incluye información adicional según rol (paciente o profesional).
    """
    if current_user.Rol_Id != 0:
        flash('Acceso denegado', 'error')
        return redirect(url_for('auth.login'))
    
    usuario = Usuario.query.get_or_404(user_id)
    
    if usuario.Estado == 0:
        flash('No se pueden ver los detalles de usuarios inactivos', 'warning')
        return redirect(url_for('admin.listar_usuarios'))
    
    info_adicional = None
    vinculaciones = []
    
    if usuario.Rol_Id == 1:  # Paciente
        info_adicional = Paciente.query.filter_by(Usuario_Id=user_id).first()
        vinculaciones = db.session.query(Usuario, Profesional).join(
            Profesional
        ).join(
            Paciente_Profesional, Paciente_Profesional.Profesional_Id == Usuario.Id
        ).filter(
            Paciente_Profesional.Paciente_Id == user_id
        ).all()
        
    elif usuario.Rol_Id == 2:  # Profesional
        info_adicional = Profesional.query.filter_by(Usuario_Id=user_id).first()
        vinculaciones = db.session.query(Usuario, Paciente).join(
            Paciente
        ).join(
            Paciente_Profesional, Paciente_Profesional.Paciente_Id == Usuario.Id
        ).filter(
            Paciente_Profesional.Profesional_Id == user_id
        ).all()
    
    return render_template('admin/ver_usuario.html',
                         usuario=usuario,
                         info_adicional=info_adicional,
                         vinculaciones=vinculaciones)

@admin_bp.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(user_id):
    """
    Permite editar los datos de un usuario existente.
    Actualiza información según el rol (paciente o profesional).
    """
    usuario = Usuario.query.get_or_404(user_id)
    
    if usuario.Estado == 0:
        flash('No se pueden editar usuarios inactivos. Activa la cuenta primero.', 'warning')
        return redirect(url_for('admin.listar_usuarios'))
    
    form = EditarUsuarioForm()
    
    if request.method == 'GET':
        form.nombre.data = usuario.Nombre
        form.apellidos.data = usuario.Apellidos
        form.email.data = usuario.Email
        
        if usuario.Rol_Id == 1:  # Paciente
            paciente = Paciente.query.filter_by(Usuario_Id=user_id).first()
            if paciente:
                form.condicion_medica.data = paciente.Condicion_Medica
                form.notas.data = paciente.Notas
                
        elif usuario.Rol_Id == 2:  # Profesional
            profesional = Profesional.query.filter_by(Usuario_Id=user_id).first()
            if profesional:
                form.especialidad.data = profesional.Especialidad
                form.tipo_profesional.data = profesional.Tipo_Profesional
    
    if form.validate_on_submit():
        try:
            email_existente = Usuario.query.filter(
                Usuario.Email == form.email.data,
                Usuario.Id != user_id
            ).first()
            
            if email_existente:
                flash('El email ya está en uso por otro usuario', 'error')
                return render_template('admin/editar_usuario.html', form=form, usuario=usuario)
            
            usuario.Nombre = form.nombre.data
            usuario.Apellidos = form.apellidos.data
            usuario.Email = form.email.data
            
            if form.password.data:
                usuario.set_contraseña(form.password.data)
            
            if usuario.Rol_Id == 1:  # Paciente
                paciente = Paciente.query.filter_by(Usuario_Id=user_id).first()
                if paciente:
                    paciente.Condicion_Medica = form.condicion_medica.data or ''
                    paciente.Notas = form.notas.data or ''
            
            elif usuario.Rol_Id == 2:  # Profesional
                profesional = Profesional.query.filter_by(Usuario_Id=user_id).first()
                if profesional:
                    profesional.Especialidad = form.especialidad.data
                    profesional.Tipo_Profesional = form.tipo_profesional.data
            
            db.session.commit()
            flash('Usuario actualizado correctamente', 'success')
            return redirect(url_for('admin.ver_usuario', user_id=user_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'error')
    
    return render_template('admin/editar_usuario.html', form=form, usuario=usuario)

@admin_bp.route('/cambiar_estado/<int:user_id>')
@login_required
@admin_required
def cambiar_estado_usuario(user_id):
    """Activa o desactiva la cuenta de un usuario."""
    if user_id == current_user.Id:
        flash('No puedes cambiar el estado de tu propia cuenta', 'error')
        return redirect(url_for('admin.listar_usuarios'))
    
    usuario = Usuario.query.get_or_404(user_id)
    nuevo_estado = 1 - usuario.Estado
    usuario.Estado = nuevo_estado
    db.session.commit()
    
    estado_texto = "activada" if nuevo_estado == 1 else "desactivada"
    flash(f'Cuenta de {usuario.Nombre} {usuario.Apellidos} {estado_texto} correctamente', 'success')
    return redirect(url_for('admin.listar_usuarios'))

@admin_bp.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    """
    Crea un nuevo usuario en el sistema.
    Gestiona roles de administrador, paciente y profesional.
    """
    form = CrearUsuarioForm()
    
    if form.validate_on_submit():
        try:
            rol_id_str = form.rol_id.data
            rol_id_int = int(rol_id_str)
            
            if Usuario.query.filter_by(Email=form.email.data).first():
                flash('El email ya está registrado', 'error')
                return render_template('admin/crear_usuario.html', form=form)
            
            nuevo_usuario = Usuario(
                Nombre=form.nombre.data,
                Apellidos=form.apellidos.data,
                Email=form.email.data,
                Rol_Id=rol_id_int,
                Estado=1
            ) 
            
            nuevo_usuario.set_contraseña(form.password.data)
            db.session.add(nuevo_usuario)
            db.session.flush()
            
            if rol_id_int == 1:  # Paciente
                if not form.fecha_nacimiento.data:
                    flash('La fecha de nacimiento es obligatoria para pacientes', 'error')
                    db.session.rollback()
                    return render_template('admin/crear_usuario.html', form=form)
                
                paciente = Paciente(
                    Usuario_Id=nuevo_usuario.Id,
                    Fecha_Nacimiento=form.fecha_nacimiento.data,
                    Condicion_Medica=form.condicion_medica.data or '',
                    Notas=form.notas.data or ''
                )  
                db.session.add(paciente)
                
            elif rol_id_int == 2:  # Profesional
                if not form.especialidad.data or not form.tipo_profesional.data:
                    flash('Especialidad y tipo son obligatorios para profesionales', 'error')
                    db.session.rollback()
                    return render_template('admin/crear_usuario.html', form=form)
                
                profesional = Profesional(
                    Usuario_Id=nuevo_usuario.Id,
                    Especialidad=form.especialidad.data,
                    Tipo_Profesional=form.tipo_profesional.data
                ) 
                db.session.add(profesional)
            
            db.session.commit()
            
            rol_texto = {0: 'Administrador', 1: 'Paciente', 2: 'Profesional'}
            flash(f'{rol_texto[rol_id_int]} {form.nombre.data} {form.apellidos.data} creado correctamente', 'success')
            return redirect(url_for('admin.listar_usuarios'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'error')
    
    return render_template('admin/crear_usuario.html', form=form)

@admin_bp.route('/vincular', methods=['GET', 'POST'])
@login_required
@admin_required
def vincular_paciente_profesional():
    """
    Crea vinculaciones entre pacientes y profesionales.
    Establece relaciones terapéuticas directas.
    """
    form = VincularPacienteProfesionalForm()
    
    pacientes = db.session.query(Usuario, Paciente).join(Paciente).filter(Usuario.Estado == 1).all()
    profesionales = db.session.query(Usuario, Profesional).join(Profesional).filter(Usuario.Estado == 1).all()
    
    form.paciente_id.choices = [(p[0].Id, f"{p[0].Nombre} {p[0].Apellidos}") for p in pacientes]
    form.profesional_id.choices = [(p[0].Id, f"{p[0].Nombre} {p[0].Apellidos} - {p[1].Tipo_Profesional}") for p in profesionales]
    
    if form.validate_on_submit():
        existe = Paciente_Profesional.query.filter_by(
            Paciente_Id=form.paciente_id.data,
            Profesional_Id=form.profesional_id.data
        ).first()
        
        if existe:
            flash('Esta vinculación ya existe', 'error')
        else:
            vinculacion = Paciente_Profesional(
                Paciente_Id=form.paciente_id.data,
                Profesional_Id=form.profesional_id.data,
                Fecha_Asignacion=date.today()
            ) 
            db.session.add(vinculacion)
            db.session.commit()
            flash('Vinculación creada correctamente', 'success')
            return redirect(url_for('admin.ver_vinculaciones'))
    
    return render_template('admin/vincular.html', form=form)

@admin_bp.route('/vinculaciones')
@login_required
@admin_required
def ver_vinculaciones():
    """
    Muestra todas las vinculaciones entre pacientes y profesionales.
    Incluye filtros por búsqueda, profesional y rango de fechas.
    """
    search = request.args.get('search', '')
    profesional_filter = request.args.get('profesional', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')

    # Consulta base
    query = db.session.query(Paciente_Profesional)

    # Aplicar filtros de busqueda
    if search:
        query = query.join(Usuario, Usuario.Id == Paciente_Profesional.Paciente_Id) \
                     .join(Paciente, Paciente.Usuario_Id == Paciente_Profesional.Paciente_Id) \
                     .filter(
                         db.or_(
                             Usuario.Nombre.contains(search),
                             Usuario.Apellidos.contains(search),
                             Paciente.Condicion_Medica.contains(search)
                         )
                     )

    if profesional_filter:
        query = query.filter(Paciente_Profesional.Profesional_Id == int(profesional_filter))

    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        query = query.filter(Paciente_Profesional.Fecha_Asignacion >= fecha_desde_obj)

    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        query = query.filter(Paciente_Profesional.Fecha_Asignacion <= fecha_hasta_obj)

    vinculaciones = query.order_by(Paciente_Profesional.Fecha_Asignacion.desc()).all()

    # Preparar datos para la vista
    relaciones = []
    for vinculacion in vinculaciones:
        # Obtener datos del paciente
        paciente_usuario = db.session.get(Usuario, vinculacion.Paciente_Id)
        paciente = Paciente.query.filter_by(Usuario_Id=vinculacion.Paciente_Id).first()
        
        # Obtener datos del profesional
        profesional_usuario = db.session.get(Usuario, vinculacion.Profesional_Id)
        profesional = Profesional.query.filter_by(Usuario_Id=vinculacion.Profesional_Id).first()


        # Verificar que todos los datos existan
        if paciente_usuario and paciente and profesional_usuario and profesional:
            relaciones.append({
                'vinculacion': vinculacion,
                'paciente_usuario': paciente_usuario,
                'paciente': paciente,
                'profesional_usuario': profesional_usuario,
                'profesional': profesional
            })

    # Profesionales para el filtro
    profesionales = db.session.query(Usuario, Profesional).join(Profesional).filter(Usuario.Estado == 1).all()

    return render_template('admin/vinculaciones.html',
                         relaciones=relaciones,
                         profesionales=profesionales,
                         search=search,
                         profesional_filter=profesional_filter,
                         fecha_desde=fecha_desde,
                         fecha_hasta=fecha_hasta)


@admin_bp.route('/desvincular/<int:paciente_id>/<int:profesional_id>', methods=['POST'])
@login_required
@admin_required
def desvincular_paciente_profesional(paciente_id, profesional_id):
    """
    Elimina la vinculación entre un paciente y un profesional.
    
    Args:
        paciente_id: ID del paciente
        profesional_id: ID del profesional
    """
    try:
        vinculacion = Paciente_Profesional.query.filter_by(
            Paciente_Id=paciente_id,
            Profesional_Id=profesional_id
        ).first()

        if vinculacion:
            db.session.delete(vinculacion)
            db.session.commit()
            flash('Vinculación eliminada correctamente', 'success')
        else:
            flash('Vinculación no encontrada', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desvincular: {str(e)}', 'error')

    return redirect(url_for('admin.ver_vinculaciones'))


@admin_bp.route('/estadisticas')
@login_required
@admin_required
def estadisticas():
    """
    Muestra estadísticas del sistema.
    Incluye distribución de roles, usuarios por mes y vinculaciones.
    """
    stats = {
        'usuarios_por_mes': [],
        'actividad_semanal': [],
        'distribucion_roles': {
            'administradores': Usuario.query.filter_by(Rol_Id=0).count(),
            'pacientes': Usuario.query.filter_by(Rol_Id=1).count(),
            'profesionales': Usuario.query.filter_by(Rol_Id=2).count()
        },
        'total_vinculaciones': Paciente_Profesional.query.count()
    }
    
    for i in range(12):
        fecha_inicio = datetime.now().replace(day=1) - timedelta(days=30*i)
        fecha_fin = fecha_inicio + timedelta(days=31)
        
        count = Usuario.query.filter(
            Usuario.Fecha_Registro >= fecha_inicio,
            Usuario.Fecha_Registro < fecha_fin
        ).count()
        
        stats['usuarios_por_mes'].append({
            'mes': fecha_inicio.strftime('%m/%Y'),
            'count': count
        })
    
    return render_template('admin/estadisticas.html', stats=stats)

@admin_bp.route('/exportar_usuarios')
@login_required
@admin_required
def exportar_usuarios():
    """
    Exporta la lista de usuarios a un archivo CSV.
    
    Returns:
        Archivo CSV con datos de todos los usuarios del sistema
    """
    usuarios = Usuario.query.all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Nombre', 'Apellidos', 'Email', 'Rol', 'Estado', 'Fecha Registro'])
    
    for usuario in usuarios:
        rol_texto = {0: 'Administrador', 1: 'Paciente', 2: 'Profesional'}.get(usuario.Rol_Id, 'Desconocido')
        estado_texto = 'Activo' if usuario.Estado == 1 else 'Inactivo'
        
        writer.writerow([
            usuario.Id,
            usuario.Nombre,
            usuario.Apellidos,
            usuario.Email,
            rol_texto,
            estado_texto,
            usuario.Fecha_Registro.strftime('%d/%m/%Y') if usuario.Fecha_Registro else ''
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracion():
    """
    Gestiona la configuración global del sistema.
    Permite modificar retención de videos, almacenamiento, notificaciones y backups.
    """
    form = ConfiguracionForm()
    
    # Cargar configuración actual
    config_actual = cargar_configuracion()
    
    # Pre-llenar formulario con valores actuales
    if request.method == 'GET':
        form.retencion_videos.data = config_actual.get('retencion_videos', '30')
        form.limite_almacenamiento.data = config_actual.get('limite_almacenamiento', '2')
        form.notificaciones_email.data = config_actual.get('notificaciones_email', 'enabled')
        form.backup_automatico.data = config_actual.get('backup_automatico', 'weekly')
    
    if form.validate_on_submit():
        try:
            nueva_config = {
                'retencion_videos': form.retencion_videos.data,
                'limite_almacenamiento': form.limite_almacenamiento.data,
                'notificaciones_email': form.notificaciones_email.data,
                'backup_automatico': form.backup_automatico.data
            }
            
            if guardar_configuracion(nueva_config):
                flash('Configuración del sistema actualizada y guardada en archivo JSON', 'success')
            else:
                flash('Error al guardar la configuración', 'error')
                
            return redirect(url_for('admin.configuracion'))
            
        except Exception as e:
            flash(f'Error al procesar configuración: {str(e)}', 'error')
    
    return render_template('admin/configuracion.html', form=form, config_actual=config_actual)
