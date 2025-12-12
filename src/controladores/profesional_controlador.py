from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.controladores.decoradores import profesional_required
from src.forms import CrearEjercicioForm, EvaluacionForm, CrearSesionDirectaForm
from src.modelos import Ejercicio, Sesion, Evaluacion, VideoRespuesta, Paciente, Ejercicio_Sesion, Profesional, Usuario
from src.modelos.asociaciones import Paciente_Profesional, Ejercicio_Profesional
from datetime import datetime, timedelta
from src.extensiones import db
import cloudinary
import cloudinary.uploader
import os
import time
from src.config import Config
from collections import defaultdict


profesional_bp = Blueprint('profesional', __name__, url_prefix='/profesional')


# Configurar Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


# Estado de sesiones en memoria: { sesion_id: ejercicio_activo_id }
estado_sesiones_tiempo_real = {}
estado_sesion_terminada = set()

# ---------------------------
# Dashboard profesional
# ---------------------------
@profesional_bp.route('/dashboard')
@login_required
@profesional_required
def dashboard():
    profesional = Profesional.query.filter_by(Usuario_Id=current_user.Id).first()
    if not profesional:
        flash('No se encontró el profesional asociado', 'error')
        return redirect(url_for('auth.login'))

    # Estadísticas del profesional
    total_pacientes = db.session.query(Paciente_Profesional).filter_by(
        Profesional_Id=profesional.Usuario_Id
    ).count()

    # Solo sesiones PENDIENTES
    sesiones_pendientes = Sesion.query.filter_by(
        Profesional_Id=profesional.Usuario_Id,
        Estado='PENDIENTE'
    ).count()

    # ✅ CORREGIDO: Solo ejercicios con VIDEO del paciente y sin evaluar
    evaluaciones_pendientes = db.session.query(Ejercicio_Sesion)\
        .join(Sesion)\
        .join(VideoRespuesta, VideoRespuesta.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id)\
        .filter(
            Sesion.Profesional_Id == profesional.Usuario_Id,
            Sesion.Estado == 'COMPLETADA',
            ~Ejercicio_Sesion.Id.in_(
                db.session.query(Evaluacion.Ejercicio_Sesion_Id).filter(
                    Evaluacion.Ejercicio_Sesion_Id.isnot(None)
                )
            )
        ).count()

    # ✅ CAMBIO: Sesiones de la próxima semana (7 días)
    hoy = datetime.now()
    una_semana_despues = hoy + timedelta(days=7)
    
    proximas_sesiones = Sesion.query.filter(
        Sesion.Profesional_Id == profesional.Usuario_Id,
        Sesion.Estado == 'PENDIENTE',
        Sesion.Fecha_Programada >= hoy,
        Sesion.Fecha_Programada <= una_semana_despues
    ).order_by(Sesion.Fecha_Programada).limit(5).all()

    stats = {
        'total_pacientes': total_pacientes,
        'sesiones_pendientes': sesiones_pendientes,
        'evaluaciones_pendientes': evaluaciones_pendientes,
        'proximas_sesiones': proximas_sesiones
    }

    return render_template('profesional/dashboard.html', stats=stats)



# ---------------------------
# Gestión de pacientes
# ---------------------------
@profesional_bp.route('/pacientes')
@login_required
@profesional_required
def listar_pacientes():
    # Filtros
    search = request.args.get('search', '')
    condicion_filter = request.args.get('condicion', '')
    edad_filter = request.args.get('edad', '')

    # Solo pacientes asignados al profesional actual
    pacientes_ids = db.session.query(Paciente_Profesional.Paciente_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()
    
    pacientes_ids = [id_tuple[0] for id_tuple in pacientes_ids]
    query = Paciente.query.filter(Paciente.Usuario_Id.in_(pacientes_ids))

    # Aplicar filtros
    if search:
        query = query.join(Usuario).filter(
            db.or_(
                Usuario.Nombre.contains(search),
                Usuario.Apellidos.contains(search)
            )
        )

    if condicion_filter:
        query = query.filter(Paciente.Condicion_Medica.contains(condicion_filter))

    pacientes = query.all()

    # Filtro por edad
    if edad_filter:
        try:
            edad_min, edad_max = map(int, edad_filter.split('-'))
            pacientes = [p for p in pacientes if p.edad() and edad_min <= p.edad() <= edad_max]
        except:
            pass

    return render_template('profesional/pacientes.html',
                          pacientes=pacientes,
                          search=search,
                          condicion_filter=condicion_filter,
                          edad_filter=edad_filter)

# ---------------------------
# Biblioteca de ejercicios
# ---------------------------
@profesional_bp.route('/ejercicios')
@login_required
@profesional_required
def listar_ejercicios():
    # Biblioteca completa de ejercicios
    tipo = request.args.get('tipo', '')
    search = request.args.get('search', '')

    query = Ejercicio.query

    if tipo:
        query = query.filter(Ejercicio.Tipo == tipo)
    if search:
        query = query.filter(Ejercicio.Nombre.contains(search))

    ejercicios = query.all()
    return render_template('profesional/ejercicios.html',
                          ejercicios=ejercicios,
                          tipo=tipo,
                          search=search)

@profesional_bp.route('/ejercicios/crear', methods=['GET', 'POST'])
@login_required
@profesional_required
def crear_ejercicio():
    form = CrearEjercicioForm()
    
    if form.validate_on_submit():
        # Crear directorio si no existe
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ejercicios')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Guardar video
        video = form.video.data
        filename = f"ejercicio_{datetime.now().timestamp()}.mp4"
        video_path = os.path.join(upload_dir, filename)
        video.save(video_path)

        # Crear ejercicio
        nuevo_ejercicio = Ejercicio(
            Nombre=form.nombre.data,
            Descripcion=form.descripcion.data,
            Tipo=form.tipo.data,  # Campo de texto libre
            Video=filename,        # Nombre del archivo guardado
            Duracion=0             # Se puede calcular después
        )
        db.session.add(nuevo_ejercicio)
        db.session.commit()

        # Asociar con el profesional
        asociacion = Ejercicio_Profesional(
            Profesional_Id=current_user.Id,
            Ejercicio_Id=nuevo_ejercicio.Id
        )
        db.session.add(asociacion)
        db.session.commit()

        flash('Ejercicio creado correctamente', 'success')
        return redirect(url_for('profesional.listar_ejercicios'))
    
    return render_template('profesional/crear_ejercicio.html', form=form)


# ---------------------------
# Gestión de sesiones
# ---------------------------
@profesional_bp.route('/sesiones/crear', methods=['GET', 'POST'])
@login_required
@profesional_required
def crear_sesion():
    """Crear sesión (CU5.1 + CU5.2 combinados)"""
    paciente_id_preseleccionado = request.args.get('paciente_id', type=int)
    form = CrearSesionDirectaForm()

    # Obtener pacientes del profesional
    pacientes_ids = db.session.query(Paciente_Profesional.Paciente_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()
    
    pacientes_ids = [id_tuple[0] for id_tuple in pacientes_ids]
    pacientes = Paciente.query.filter(Paciente.Usuario_Id.in_(pacientes_ids)).all()
    form.paciente_id.choices = [(p.Usuario_Id, f"{p.usuario.Nombre} {p.usuario.Apellidos}") for p in pacientes]

    # Preselección de paciente si se recibió por parámetro
    if paciente_id_preseleccionado is not None:
        form.paciente_id.data = paciente_id_preseleccionado

    # Obtener ejercicios disponibles
    ejercicios_ids = db.session.query(Ejercicio_Profesional.Ejercicio_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()
    
    ejercicios_ids = [id_tuple[0] for id_tuple in ejercicios_ids]
    ejercicios = Ejercicio.query.filter(Ejercicio.Id.in_(ejercicios_ids)).all()
    form.ejercicios.choices = [(e.Id, e.Nombre) for e in ejercicios]

    if form.validate_on_submit():
        # Crear sesión directamente asignada
        nueva_sesion = Sesion(
            Paciente_Id=form.paciente_id.data,
            Profesional_Id=current_user.Id,
            Estado='PENDIENTE',
            Fecha_Asignacion=datetime.now(),
            Fecha_Programada=form.fecha_programada.data
        )
        db.session.add(nueva_sesion)
        db.session.flush()

        # Asociar ejercicios a la sesión
        for ejercicio_id in form.ejercicios.data:
            ejercicio_sesion = Ejercicio_Sesion(
                Sesion_Id=nueva_sesion.Id,
                Ejercicio_Id=ejercicio_id
            )
            db.session.add(ejercicio_sesion)

        db.session.commit()
        flash('Sesión creada y asignada correctamente', 'success')
        return redirect(url_for('profesional.listar_sesiones'))

    return render_template('profesional/crear_sesion.html', form=form)

@profesional_bp.route('/sesiones')
@login_required
@profesional_required
def listar_sesiones():
    """Consultar sesiones programadas (CU5.3)"""
    # Filtros
    estado_filter = request.args.get('estado', '')
    paciente_filter = request.args.get('paciente', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')

    # Solo sesiones del profesional actual
    query = Sesion.query.filter_by(Profesional_Id=current_user.Id)

    # Aplicar filtros
    if estado_filter:
        query = query.filter(Sesion.Estado == estado_filter)
    if paciente_filter:
        query = query.filter(Sesion.Paciente_Id == int(paciente_filter))
    if fecha_desde:
        try:
            fd = datetime.strptime(fecha_desde, '%Y-%m-%d')
            query = query.filter(Sesion.Fecha_Programada >= fd)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            fh = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # incluir todo el día
            fh = fh.replace(hour=23, minute=59, second=59)
            query = query.filter(Sesion.Fecha_Programada <= fh)
        except ValueError:
            pass

    sesiones = query.order_by(Sesion.Fecha_Programada.desc()).all()

    # ✅ CORREGIDO: Calcular estado evaluación solo con videos
    sesiones_con_estado = []
    for sesion in sesiones:
        if sesion.Estado == 'COMPLETADA':
            # Contar solo ejercicios CON VIDEO del paciente
            ejercicios_con_video = db.session.query(Ejercicio_Sesion)\
                .join(VideoRespuesta, VideoRespuesta.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id)\
                .filter(Ejercicio_Sesion.Sesion_Id == sesion.Id)\
                .count()
            
            # Contar ejercicios con video Y evaluados
            ejercicios_evaluados = db.session.query(Ejercicio_Sesion)\
                .join(VideoRespuesta, VideoRespuesta.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id)\
                .join(Evaluacion, Evaluacion.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id)\
                .filter(Ejercicio_Sesion.Sesion_Id == sesion.Id)\
                .count()
            
            # Determinar estado solo basado en ejercicios con video
            if ejercicios_con_video > 0:
                if ejercicios_evaluados == ejercicios_con_video:
                    sesion.estado_evaluacion = 'COMPLETAMENTE_EVALUADA'
                elif ejercicios_evaluados > 0:
                    sesion.estado_evaluacion = 'PARCIALMENTE_EVALUADA'
                else:
                    sesion.estado_evaluacion = 'SIN_EVALUAR'
                
                sesion.porcentaje_evaluacion = (ejercicios_evaluados / ejercicios_con_video * 100)
            else:
                # No hay videos = no evaluable
                sesion.estado_evaluacion = 'NO_EVALUABLE'
                sesion.porcentaje_evaluacion = 0
        else:
            sesion.estado_evaluacion = 'NO_APLICABLE'
            sesion.porcentaje_evaluacion = 0
        
        sesiones_con_estado.append(sesion)

    # Pacientes para el filtro
    pacientes_ids = db.session.query(Paciente_Profesional.Paciente_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()
    
    pacientes_ids = [id_tuple[0] for id_tuple in pacientes_ids]
    pacientes = Paciente.query.filter(Paciente.Usuario_Id.in_(pacientes_ids)).all()

    return render_template('profesional/sesiones.html',
                          sesiones=sesiones_con_estado,
                          pacientes=pacientes,
                          estado_filter=estado_filter,
                          paciente_filter=paciente_filter,
                          fecha_desde=fecha_desde,
                          fecha_hasta=fecha_hasta)




@profesional_bp.route('/sesion/<int:sesion_id>')  # ✅ Añadir parámetro
@login_required
@profesional_required
def ver_sesion(sesion_id):
    """Ver detalle de sesión con verificación de permisos"""
    sesion = Sesion.query.get_or_404(sesion_id)
    
    # Verificar que la sesión pertenece al profesional actual
    if sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para ver esta sesión', 'error')
        return redirect(url_for('profesional.listar_sesiones'))

    # ✅ AÑADIR: Obtener ejercicios con evaluaciones
    ejercicios_data = []
    ejercicios_sesion = Ejercicio_Sesion.query.filter_by(Sesion_Id=sesion_id).all()
    
    for ej_sesion in ejercicios_sesion:
        # Obtener evaluación si existe
        evaluacion = Evaluacion.query.filter_by(
            Ejercicio_Sesion_Id=ej_sesion.Id
        ).first()
        
        # Crear objeto con ejercicio y evaluación
        ej_sesion.evaluacion = evaluacion
        ejercicios_data.append(ej_sesion)

    return render_template('profesional/ver_sesion.html', 
                          sesion=sesion, 
                          ejercicios=ejercicios_data)

@profesional_bp.route('/sesion/ejecutar/<int:sesion_id>')  # ✅ Añadir parámetro
@login_required
@profesional_required
def ejecutar_sesion(sesion_id):
    """Ejecutar sesión (CU6)"""
    sesion = Sesion.query.get_or_404(sesion_id)
    
    # Verificar permisos
    if sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para ejecutar esta sesión', 'error')
        return redirect(url_for('profesional.listar_sesiones'))

    ejercicios = Ejercicio_Sesion.query.filter_by(Sesion_Id=sesion_id).order_by(Ejercicio_Sesion.Id).all()
    
    if not ejercicios:
        flash('Esta sesión no tiene ejercicios asignados.', 'warning')
        return redirect(url_for('profesional.ver_sesion', sesion_id=sesion_id))
    
    return render_template('profesional/ejecutar_sesion.html',
                          sesion=sesion,
                          ejercicios=ejercicios)

@profesional_bp.route('/sesion/finalizar/<int:sesion_id>', methods=['POST'])
@login_required
@profesional_required
def finalizar_sesion(sesion_id):
    sesion = Sesion.query.get_or_404(sesion_id)
    if sesion.Profesional_Id != current_user.Id:
        return jsonify(success=False, error='Sin permisos')

    sesion.Estado = 'COMPLETADA'
    db.session.commit()

    estado_sesion_terminada.add(sesion_id)  # si estás usando el set
    return jsonify(success=True)


@profesional_bp.route('/api/sesion/<int:sesion_id>/estado', methods=['GET'])
@login_required
def obtener_estado_sesion(sesion_id):
    sesion = Sesion.query.get_or_404(sesion_id)
    ejercicio_activo_id = estado_sesiones_tiempo_real.get(sesion_id)
    return jsonify({
        'sesion_id': sesion_id,
        'ejercicio_activo_id': ejercicio_activo_id,
        'terminada': sesion_id in estado_sesion_terminada
    })

@profesional_bp.route('/api/sesion/<int:sesion_id>/estado', methods=['POST'])
@login_required
@profesional_required
def actualizar_estado_sesion(sesion_id):
    sesion = Sesion.query.get_or_404(sesion_id)
    if sesion.Profesional_Id != current_user.Id:
        return jsonify({"error": "Sin permisos"}), 403

    data = request.get_json() or {}
    ejercicio_activo_id = data.get('ejercicio_activo_id')
    if ejercicio_activo_id is None:
        return jsonify({"error": "Falta ejercicio_activo_id"}), 400

    estado_sesiones_tiempo_real[sesion_id] = ejercicio_activo_id
    # por si se marca terminada y luego se reanuda
    if sesion_id in estado_sesion_terminada:
        estado_sesion_terminada.discard(sesion_id)

    return jsonify({
        "ok": True,
        "sesion_id": sesion_id,
        "ejercicio_activo_id": ejercicio_activo_id
    })

# ---------------------------
# Evaluación de ejercicios
# ---------------------------
@profesional_bp.route('/evaluar_sesion/<int:sesion_id>')
@login_required
@profesional_required
def evaluar_sesion(sesion_id):
    """Evaluar sesión completa (CU8.1)"""
    sesion = Sesion.query.get_or_404(sesion_id)
    
    # Verificar permisos y estado
    if sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para evaluar esta sesión', 'error')
        return redirect(url_for('profesional.listar_sesiones'))
    
    if sesion.Estado != 'COMPLETADA':
        flash('Solo se pueden evaluar sesiones completadas', 'warning')
        return redirect(url_for('profesional.ver_sesion', sesion_id=sesion_id))

    # ✅ CORREGIDO: Obtener ejercicios con videos y evaluaciones
    ejercicios = []
    ejercicios_sesion = Ejercicio_Sesion.query.filter_by(Sesion_Id=sesion_id).all()
    
    for ej_sesion in ejercicios_sesion:
        # Obtener video de respuesta
        video_respuesta = VideoRespuesta.query.filter_by(
            Ejercicio_Sesion_Id=ej_sesion.Id
        ).first()
        
        # Obtener evaluación existente
        evaluacion = Evaluacion.query.filter_by(
            Ejercicio_Sesion_Id=ej_sesion.Id
        ).first()
        
        ejercicios.append({
            'ejercicio_sesion': ej_sesion,
            'video_respuesta': video_respuesta,
            'evaluacion': evaluacion
        })
    
    return render_template('profesional/evaluar_sesion.html',
                          sesion=sesion,
                          ejercicios=ejercicios)


@profesional_bp.route('/evaluar/<int:ejercicio_sesion_id>', methods=['GET', 'POST'])
@login_required
@profesional_required
def evaluar_ejercicio(ejercicio_sesion_id):
    """Evaluar ejercicio individual (CU8.2)"""
    form = EvaluacionForm()
    ejercicio_sesion = Ejercicio_Sesion.query.get_or_404(ejercicio_sesion_id)
    
    # Verificar permisos
    if ejercicio_sesion.sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para evaluar este ejercicio', 'error')
        return redirect(url_for('profesional.listar_sesiones'))

    video_respuesta = VideoRespuesta.query.filter_by(
        Ejercicio_Sesion_Id=ejercicio_sesion_id
    ).first()

    if form.validate_on_submit():
        nueva_evaluacion = Evaluacion(
            Ejercicio_Sesion_Id=ejercicio_sesion_id,
            Puntuacion=form.puntuacion.data,
            Comentarios=form.comentarios.data,
            Fecha_Evaluacion=datetime.now()
        )
        db.session.add(nueva_evaluacion)
        db.session.commit()
        
        flash('Evaluación registrada', 'success')
        return redirect(url_for('profesional.evaluar_sesion', 
                               sesion_id=ejercicio_sesion.Sesion_Id))

    return render_template('profesional/evaluar_ejercicio.html',
                          form=form,
                          ejercicio_sesion=ejercicio_sesion,
                          video_respuesta=video_respuesta)

# ---------------------------
# Seguimiento y progreso
# ---------------------------
@profesional_bp.route('/progreso/<int:paciente_id>')
@login_required
@profesional_required
def ver_progreso(paciente_id):
    """Ver progreso de paciente (CU9.1)"""
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Verificar que el paciente está asignado al profesional
    vinculacion = Paciente_Profesional.query.filter_by(
        Paciente_Id=paciente_id,
        Profesional_Id=current_user.Id
    ).first()
    
    if not vinculacion:
        flash('No tienes permisos para ver este paciente', 'error')
        return redirect(url_for('profesional.listar_pacientes'))

    # Obtener evaluaciones del paciente
    evaluaciones = (
        db.session.query(Evaluacion)
        .join(Ejercicio_Sesion)
        .join(Sesion)
        .filter(
            Sesion.Paciente_Id == paciente_id,
            Sesion.Profesional_Id == current_user.Id
        )
        .order_by(Evaluacion.Fecha_Evaluacion.desc())
        .all()
    )

    # Detalle por ejercicio (para la tabla)
    evaluaciones_dict = []
    for e in evaluaciones:
        evaluaciones_dict.append({
            'Fecha_Evaluacion': e.Fecha_Evaluacion.strftime('%Y-%m-%d'),
            'Puntuacion': e.Puntuacion,
            'Comentarios': e.Comentarios,
            'Ejercicio_Nombre': e.ejercicio_sesion.ejercicio.Nombre
        })

    # NUEVO: media de puntuación por sesión (para la gráfica)
    evaluaciones_por_sesion = defaultdict(list)
    for e in evaluaciones:
        if e.ejercicio_sesion and e.ejercicio_sesion.sesion:
            sesion_id = e.ejercicio_sesion.Sesion_Id
            evaluaciones_por_sesion[sesion_id].append(e.Puntuacion)

    evaluaciones_sesion_json = []
    for sesion_id, puntos in evaluaciones_por_sesion.items():
        media = sum(puntos) / len(puntos)
        sesion = Sesion.query.get(sesion_id)
        fecha = (
            sesion.Fecha_Programada.strftime('%Y-%m-%d')
            if sesion and sesion.Fecha_Programada
            else None
        )
        evaluaciones_sesion_json.append({
            'Sesion_Id': sesion_id,
            'Fecha': fecha,
            'Media_Puntuacion': round(media, 1),
        })

    evaluaciones_sesion_json.sort(key=lambda e: e['Fecha'] or '')

    return render_template(
        'profesional/ver_progreso.html',
        paciente=paciente,
        evaluaciones=evaluaciones,
        evaluaciones_json=evaluaciones_dict,              # tabla detallada
        evaluaciones_sesion_json=evaluaciones_sesion_json # gráfica por sesión
    )


# ---------------------------
# Gestión de videos
# ---------------------------
@profesional_bp.route('/guardar_video/<int:ejercicio_sesion_id>', methods=['POST'])
@login_required
def guardar_video(ejercicio_sesion_id):
    """Guardar video de respuesta en Cloudinary (CU7)"""
    try:
        ejercicio_sesion = Ejercicio_Sesion.query.get_or_404(ejercicio_sesion_id)
        
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No se encontró el archivo'}), 400
        
        video_file = request.files['video']
        
        if video_file.filename == '':
            return jsonify({'success': False, 'error': 'Archivo vacío'}), 400
        
        # Subir a Cloudinary
        upload_result = cloudinary.uploader.upload(
            video_file,
            resource_type="video",
            folder="terapitrack/respuestas",
            public_id=f"respuesta_{ejercicio_sesion_id}_{int(time.time())}",
            overwrite=True
        )
        
        # La URL del video en Cloudinary
        video_url = upload_result['secure_url']
        
        # Guardar la URL en la base de datos
        video_respuesta = VideoRespuesta.query.filter_by(Ejercicio_Sesion_Id=ejercicio_sesion_id).first()
        
        fecha_expiracion = datetime.now() + timedelta(days=30)
        
        if video_respuesta:
            video_respuesta.Ruta_Almacenamiento = video_url
            video_respuesta.Fecha_Expiracion = fecha_expiracion
        else:
            video_respuesta = VideoRespuesta(
                Ejercicio_Sesion_Id=ejercicio_sesion_id,
                Ruta_Almacenamiento=video_url,
                Fecha_Expiracion=fecha_expiracion
            )
            db.session.add(video_respuesta)
        
        db.session.commit()
        
        print(f"✅ Video guardado en Cloudinary: {video_url}")
        return jsonify({'success': True, 'mensaje': 'Video guardado correctamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al guardar video: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500



@profesional_bp.route('/ver_evaluacion/<int:ejercicio_sesion_id>')
@login_required
@profesional_required
def ver_evaluacion(ejercicio_sesion_id):
    """Ver evaluación existente"""
    ejercicio_sesion = Ejercicio_Sesion.query.get_or_404(ejercicio_sesion_id)
    
    # Verificar permisos
    if ejercicio_sesion.sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para ver esta evaluación', 'error')
        return redirect(url_for('profesional.listar_sesiones'))

    evaluacion = Evaluacion.query.filter_by(
        Ejercicio_Sesion_Id=ejercicio_sesion_id
    ).first_or_404()

    video_respuesta = VideoRespuesta.query.filter_by(
        Ejercicio_Sesion_Id=ejercicio_sesion_id
    ).first()

    return render_template('profesional/ver_evaluacion.html',
                          ejercicio_sesion=ejercicio_sesion,
                          evaluacion=evaluacion,
                          video_respuesta=video_respuesta)
