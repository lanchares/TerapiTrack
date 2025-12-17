from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.controladores.decoradores import profesional_required
from src.forms import CrearEjercicioForm, EvaluacionForm, CrearSesionDirectaForm
from src.modelos import Ejercicio, Sesion, Evaluacion, VideoRespuesta, Paciente, Ejercicio_Sesion, Profesional, Usuario
from src.modelos.asociaciones import Paciente_Profesional, Ejercicio_Profesional
from datetime import datetime, timedelta
from src.extensiones import db, csrf
import cloudinary
import cloudinary.uploader
import os
import time
from src.config import Config
from collections import defaultdict
from sqlalchemy.exc import IntegrityError
try:
    from moviepy.editor import VideoFileClip
except Exception:
    VideoFileClip = None 
profesional_bp = Blueprint('profesional', __name__, url_prefix='/profesional')

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# ---------------------------
# Estado en tiempo real sesión
# ---------------------------

# Todo el estado va en memoria, no en los modelos
estado_sesiones_tiempo_real = {}   # {sesion_id: ejercicio_activo_id o None}
estado_sesion_terminada = set()    # {sesion_id}

ultimo_cambio_sesion = {}
MIN_INTERVAL_CAMBIO = 6  # segundos mínimo entre cambios de ejercicio

@profesional_bp.route('/api/sesion/<int:sesion_id>/estado', methods=['GET', 'POST'])
@login_required
def estado_sesion(sesion_id):
    """
    GET: paciente y profesional consultan el estado en memoria.
    POST: solo el profesional actualiza ejercicio_activo_id y/o terminada.
    """
    sesion = Sesion.query.get_or_404(sesion_id)

    # --- GET: lectura de estado (paciente y profesional) ---
    if request.method == 'GET':
        ejercicio_activo_id = estado_sesiones_tiempo_real.get(sesion_id)
        terminada = sesion_id in estado_sesion_terminada
        return jsonify({
            'sesion_id': sesion_id,
            'ejercicio_activo_id': ejercicio_activo_id,
            'terminada': terminada
        })

    # --- POST: solo profesional que lleva la sesión ---
    if sesion.Profesional_Id != current_user.Id:
        return jsonify({"error": "Sin permisos"}), 403

    data = request.get_json() or {}
    ejercicio_activo_id = data.get('ejercicio_activo_id', None)
    terminada_flag = data.get('terminada', None)

    ahora = time.time()
    anterior = estado_sesiones_tiempo_real.get(sesion_id)
    ultimo = ultimo_cambio_sesion.get(sesion_id)

    # 1) Actualizar ejercicio activo si la clave viene en el JSON
    if 'ejercicio_activo_id' in data:
        # Si el id es exactamente el mismo que ya teníamos, no hacer nada
        if ejercicio_activo_id == anterior:
            return jsonify({
                "ok": True,
                "sesion_id": sesion_id,
                "ejercicio_activo_id": anterior,
                "terminada": sesion_id in estado_sesion_terminada
            })

        if ejercicio_activo_id is None:
            # Permitir poner None explícito (no hay ejercicio activo)
            estado_sesiones_tiempo_real[sesion_id] = None
            ultimo_cambio_sesion[sesion_id] = ahora
        else:
            # Anti‑rebote: evitar cambios de id demasiado rápidos
            if (anterior is not None and
                ejercicio_activo_id != anterior and
                ultimo is not None and
                ahora - ultimo < MIN_INTERVAL_CAMBIO):
                return jsonify({
                    "ok": False,
                    "sesion_id": sesion_id,
                    "ejercicio_activo_id": anterior,
                    "terminada": sesion_id in estado_sesion_terminada
                })

            estado_sesiones_tiempo_real[sesion_id] = ejercicio_activo_id
            ultimo_cambio_sesion[sesion_id] = ahora

    # 2) Marcar / desmarcar sesión terminada
    if terminada_flag is not None:
        terminada_bool = bool(terminada_flag)

        # Si ya está terminada y vuelven a mandar terminada=true, no hacer nada extra
        if terminada_bool and (sesion_id in estado_sesion_terminada):
            return jsonify({
                "ok": True,
                "sesion_id": sesion_id,
                "ejercicio_activo_id": estado_sesiones_tiempo_real.get(sesion_id),
                "terminada": True
            })

        if terminada_bool:
            estado_sesion_terminada.add(sesion_id)
        else:
            estado_sesion_terminada.discard(sesion_id)

    return jsonify({
        "ok": True,
        "sesion_id": sesion_id,
        "ejercicio_activo_id": estado_sesiones_tiempo_real.get(sesion_id),
        "terminada": sesion_id in estado_sesion_terminada
    })


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

    total_pacientes = db.session.query(Paciente_Profesional).filter_by(
        Profesional_Id=profesional.Usuario_Id
    ).count()

    sesiones_pendientes = Sesion.query.filter_by(
        Profesional_Id=profesional.Usuario_Id,
        Estado='PENDIENTE'
    ).count()

    evaluaciones_pendientes = db.session.query(Ejercicio_Sesion) \
        .join(Sesion) \
        .join(VideoRespuesta, VideoRespuesta.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id) \
        .filter(
            Sesion.Profesional_Id == profesional.Usuario_Id,
            Sesion.Estado == 'COMPLETADA',
            ~Ejercicio_Sesion.Id.in_(
                db.session.query(Evaluacion.Ejercicio_Sesion_Id).filter(
                    Evaluacion.Ejercicio_Sesion_Id.isnot(None)
                )
            )
        ).count()

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
    search = request.args.get('search', '')
    condicion_filter = request.args.get('condicion', '')
    edad_filter = request.args.get('edad', '')

    pacientes_ids = db.session.query(Paciente_Profesional.Paciente_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()

    pacientes_ids = [id_tuple[0] for id_tuple in pacientes_ids]
    query = Paciente.query.filter(Paciente.Usuario_Id.in_(pacientes_ids))

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
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ejercicios')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        video = form.video.data
        filename = f"ejercicio_{datetime.now().timestamp()}.mp4"
        video_path = os.path.join(upload_dir, filename)
        video.save(video_path)

        # Calcular duración real del vídeo si es posible
        duracion_segundos = 0
        if VideoFileClip is not None:
            try:
                clip = VideoFileClip(video_path)
                duracion_segundos = int(clip.duration)  # duración en segundos
                clip.close()
            except Exception as e:
                print(f"Error calculando duración del vídeo: {e}")
                duracion_segundos = 0

        nuevo_ejercicio = Ejercicio(
            Nombre=form.nombre.data,
            Descripcion=form.descripcion.data,
            Tipo=form.tipo.data,
            Video=filename,
            Duracion=duracion_segundos
        )
        db.session.add(nuevo_ejercicio)
        db.session.commit()

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

    pacientes_ids = db.session.query(Paciente_Profesional.Paciente_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()

    pacientes_ids = [id_tuple[0] for id_tuple in pacientes_ids]
    pacientes = Paciente.query.filter(Paciente.Usuario_Id.in_(pacientes_ids)).all()
    form.paciente_id.choices = [(p.Usuario_Id, f"{p.usuario.Nombre} {p.usuario.Apellidos}") for p in pacientes]

    if paciente_id_preseleccionado is not None:
        form.paciente_id.data = paciente_id_preseleccionado

    ejercicios_ids = db.session.query(Ejercicio_Profesional.Ejercicio_Id).filter_by(
        Profesional_Id=current_user.Id
    ).distinct().all()

    ejercicios_ids = [id_tuple[0] for id_tuple in ejercicios_ids]
    ejercicios = Ejercicio.query.filter(Ejercicio.Id.in_(ejercicios_ids)).all()
    form.ejercicios.choices = [(e.Id, e.Nombre) for e in ejercicios]

    if form.validate_on_submit():
        nueva_sesion = Sesion(
            Paciente_Id=form.paciente_id.data,
            Profesional_Id=current_user.Id,
            Estado='PENDIENTE',
            Fecha_Asignacion=datetime.now(),
            Fecha_Programada=form.fecha_programada.data
        )
        db.session.add(nueva_sesion)
        db.session.flush()

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
    estado_filter = request.args.get('estado', '')
    paciente_filter = request.args.get('paciente', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')

    query = Sesion.query.filter_by(Profesional_Id=current_user.Id)

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
            fh = fh.replace(hour=23, minute=59, second=59)
            query = query.filter(Sesion.Fecha_Programada <= fh)
        except ValueError:
            pass

    sesiones = query.order_by(Sesion.Fecha_Programada.desc()).all()

    sesiones_con_estado = []
    for sesion in sesiones:
        if sesion.Estado == 'COMPLETADA':
            ejercicios_con_video = db.session.query(Ejercicio_Sesion) \
                .join(VideoRespuesta, VideoRespuesta.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id) \
                .filter(Ejercicio_Sesion.Sesion_Id == sesion.Id) \
                .count()

            ejercicios_evaluados = db.session.query(Ejercicio_Sesion) \
                .join(VideoRespuesta, VideoRespuesta.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id) \
                .join(Evaluacion, Evaluacion.Ejercicio_Sesion_Id == Ejercicio_Sesion.Id) \
                .filter(Ejercicio_Sesion.Sesion_Id == sesion.Id) \
                .count()

            if ejercicios_con_video > 0:
                if ejercicios_evaluados == ejercicios_con_video:
                    sesion.estado_evaluacion = 'COMPLETAMENTE_EVALUADA'
                elif ejercicios_evaluados > 0:
                    sesion.estado_evaluacion = 'PARCIALMENTE_EVALUADA'
                else:
                    sesion.estado_evaluacion = 'SIN_EVALUAR'

                sesion.porcentaje_evaluacion = (ejercicios_evaluados / ejercicios_con_video * 100)
            else:
                sesion.estado_evaluacion = 'NO_EVALUABLE'
                sesion.porcentaje_evaluacion = 0
        else:
            sesion.estado_evaluacion = 'NO_APLICABLE'
            sesion.porcentaje_evaluacion = 0

        sesiones_con_estado.append(sesion)

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

@profesional_bp.route('/sesion/<int:sesion_id>')
@login_required
@profesional_required
def ver_sesion(sesion_id):
    """Ver detalle de sesión con verificación de permisos"""
    sesion = Sesion.query.get_or_404(sesion_id)

    if sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para ver esta sesión', 'error')
        return redirect(url_for('profesional.listar_sesiones'))

    ejercicios_data = []
    ejercicios_sesion = Ejercicio_Sesion.query.filter_by(Sesion_Id=sesion_id).all()

    for ej_sesion in ejercicios_sesion:
        evaluacion = Evaluacion.query.filter_by(
            Ejercicio_Sesion_Id=ej_sesion.Id
        ).first()
        ej_sesion.evaluacion = evaluacion
        ejercicios_data.append(ej_sesion)

    return render_template('profesional/ver_sesion.html',
                           sesion=sesion,
                           ejercicios=ejercicios_data)

@profesional_bp.route('/sesion/ejecutar/<int:sesion_id>')
@login_required
@profesional_required
def ejecutar_sesion(sesion_id):
    """Ejecutar sesión (CU6)"""
    sesion = Sesion.query.get_or_404(sesion_id)

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

    # Marcamos terminada en la caché también
    estado_sesion_terminada.add(sesion_id)
    return jsonify(success=True)

# ---------------------------
# Evaluación de ejercicios
# ---------------------------
@profesional_bp.route('/evaluar_sesion/<int:sesion_id>')
@login_required
@profesional_required
def evaluar_sesion(sesion_id):
    """Evaluar sesión completa (CU8.1)"""
    sesion = Sesion.query.get_or_404(sesion_id)

    if sesion.Profesional_Id != current_user.Id:
        flash('No tienes permisos para evaluar esta sesión', 'error')
        return redirect(url_for('profesional.listar_sesiones'))

    if sesion.Estado != 'COMPLETADA':
        flash('Solo se pueden evaluar sesiones completadas', 'warning')
        return redirect(url_for('profesional.ver_sesion', sesion_id=sesion_id))

    ejercicios = []
    ejercicios_sesion = Ejercicio_Sesion.query.filter_by(Sesion_Id=sesion_id).all()

    for ej_sesion in ejercicios_sesion:
        video_respuesta = VideoRespuesta.query.filter_by(
            Ejercicio_Sesion_Id=ej_sesion.Id
        ).first()

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

    vinculacion = Paciente_Profesional.query.filter_by(
        Paciente_Id=paciente_id,
        Profesional_Id=current_user.Id
    ).first()

    if not vinculacion:
        flash('No tienes permisos para ver este paciente', 'error')
        return redirect(url_for('profesional.listar_pacientes'))

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

    evaluaciones_dict = []
    for e in evaluaciones:
        evaluaciones_dict.append({
            'Fecha_Evaluacion': e.Fecha_Evaluacion.strftime('%Y-%m-%d'),
            'Puntuacion': e.Puntuacion,
            'Comentarios': e.Comentarios,
            'Ejercicio_Nombre': e.ejercicio_sesion.ejercicio.Nombre
        })

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
        evaluaciones_json=evaluaciones_dict,
        evaluaciones_sesion_json=evaluaciones_sesion_json
    )

# ---------------------------
# Gestión de videos
# ---------------------------
@profesional_bp.route('/guardar_video/<int:ejercicio_sesion_id>', methods=['POST'])
@login_required
@csrf.exempt
def guardar_video(ejercicio_sesion_id):
    """Guardar video de respuesta en Cloudinary (CU7). Garantiza solo 1 vídeo por ejercicio_sesion."""
    try:
        ejercicio_sesion = Ejercicio_Sesion.query.get_or_404(ejercicio_sesion_id)
        sesion = ejercicio_sesion.sesion
        paciente = sesion.paciente

        # 1) Permisos: solo el paciente dueño puede subir
        if paciente.Usuario_Id != current_user.Id:
            return jsonify({'success': False, 'error': 'Sin permisos'}), 403

        # 2) Comprobar si ya existe un vídeo para este ejercicio_sesion
        video_respuesta_existente = VideoRespuesta.query.filter_by(
            Ejercicio_Sesion_Id=ejercicio_sesion_id
        ).first()

        if video_respuesta_existente:
            # Ya hay vídeo guardado; no subir otro ni pisar el existente
            return jsonify({
                'success': True,
                'mensaje': 'Video ya existente, se ignora nueva subida'
            }), 200

        # 3) Validar presencia de archivo
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No se encontró el archivo'}), 400

        video_file = request.files['video']

        if not video_file or video_file.filename == '':
            return jsonify({'success': False, 'error': 'Archivo vacío'}), 400

        # 4) Subir a Cloudinary
        upload_result = cloudinary.uploader.upload(
            video_file,
            resource_type="video",
            folder="terapitrack/respuestas",
            public_id=f"respuesta_{ejercicio_sesion_id}",
            overwrite=True,
            unique_filename=False
        )


        video_url = upload_result.get('secure_url')
        if not video_url:
            return jsonify({'success': False, 'error': 'No se obtuvo URL del video'}), 500

        # 5) Crear registro nuevo (ya sabemos que no existía en este proceso)
        fecha_expiracion = datetime.now() + timedelta(days=30)

        try:
            video_respuesta = VideoRespuesta(
                Ejercicio_Sesion_Id=ejercicio_sesion_id,
                Ruta_Almacenamiento=video_url,
                Fecha_Expiracion=fecha_expiracion
            )
            db.session.add(video_respuesta)
            db.session.commit()

            print(f"✅ Video guardado en Cloudinary: {video_url}")
            return jsonify({'success': True, 'mensaje': 'Video guardado correctamente'}), 200

        except IntegrityError:
            # Otra petición paralela insertó este registro justo antes del commit
            db.session.rollback()
            print(f"ℹ️ Video ya existente (race) para ejercicio_sesion_id={ejercicio_sesion_id}")
            return jsonify({
                'success': True,
                'mensaje': 'Video ya existente (race), se ignora nueva subida'
            }), 200

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
