from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.controladores.decoradores import paciente_required
from src.modelos import Sesion, Ejercicio_Sesion, VideoRespuesta, Evaluacion, Paciente, Usuario
from src.extensiones import db
from datetime import datetime, timedelta
import os
from collections import defaultdict

paciente_bp = Blueprint('paciente', __name__, url_prefix='/paciente')


def get_video_path(video_filename):
    """Detecta si el video está en uploads/ejercicios o en videos"""
    from flask import current_app
    
    uploads_path = os.path.join(current_app.static_folder, 'uploads', 'ejercicios', video_filename)
    if os.path.exists(uploads_path):
        return f'/static/uploads/ejercicios/{video_filename}'
    
    videos_path = os.path.join(current_app.static_folder, 'videos', video_filename)
    if os.path.exists(videos_path):
        return f'/static/videos/{video_filename}'
    
    return f'/static/uploads/ejercicios/{video_filename}'


@paciente_bp.route('/dashboard')
@login_required
@paciente_required
def dashboard():
    sesiones_proximas = Sesion.query.filter(
        Sesion.Paciente_Id == current_user.Id,
        Sesion.Estado == 'PENDIENTE',
        Sesion.Fecha_Programada >= datetime.now()
    ).order_by(Sesion.Fecha_Programada).limit(3).all()

    stats = {
        'sesiones_pendientes': len(sesiones_proximas),
        'nombre_completo': f"{current_user.Nombre} {current_user.Apellidos}",
        # El mando ahora se gestiona en el navegador, así que aquí siempre False o lo quitas
        'mando_conectado': False
    }

    return render_template(
        'paciente/dashboard.html',
        sesiones=sesiones_proximas,
        stats=stats
    )


@paciente_bp.route('/mis_sesiones')
@login_required
@paciente_required
def mis_sesiones():
    fecha_inicio = datetime.now()
    fecha_fin = fecha_inicio + timedelta(weeks=3)
    
    sesiones = Sesion.query.filter(
        Sesion.Paciente_Id == current_user.Id,
        Sesion.Fecha_Programada >= fecha_inicio,
        Sesion.Fecha_Programada <= fecha_fin
    ).order_by(Sesion.Fecha_Programada).all()

    sesiones_json = []
    for s in sesiones:
        sesiones_json.append({
            'Id': s.Id,
            'Fecha_Programada': s.Fecha_Programada.isoformat() if s.Fecha_Programada else None,
            'Fecha_Texto': s.Fecha_Programada.strftime('%Y-%m-%d') if s.Fecha_Programada else '',
            'Hora_Texto': s.Fecha_Programada.strftime('%H:%M') if s.Fecha_Programada else '',
            'Estado': s.Estado,
            'profesional': {
                'usuario': {
                    'Nombre': s.profesional.usuario.Nombre,
                    'Apellidos': s.profesional.usuario.Apellidos
                },
                'Tipo_Profesional': s.profesional.Tipo_Profesional
            },
            'ejercicios_sesion': [{'Id': es.Id} for es in s.ejercicios_sesion]
        })

    return render_template('paciente/mis_sesiones.html', sesiones=sesiones_json)


@paciente_bp.route('/ejecutar_sesion/<int:sesion_id>')
@login_required
@paciente_required
def ejecutar_sesion(sesion_id):
    sesion = Sesion.query.get_or_404(sesion_id)
    if sesion.Paciente_Id != current_user.Id:
        flash('No tienes permisos para esta sesión', 'error')
        return redirect(url_for('paciente.dashboard'))

    ejercicios = Ejercicio_Sesion.query.filter_by(Sesion_Id=sesion_id).order_by(Ejercicio_Sesion.Id).all()

    ejercicios_serializados = []
    for es in ejercicios:
        ejercicios_serializados.append({
            'Id': es.Id,
            'ejercicio': {
                'Id': es.ejercicio.Id,
                'Nombre': es.ejercicio.Nombre,
                'Tipo': es.ejercicio.Tipo,
                'Video': get_video_path(es.ejercicio.Video),
                'Duracion': es.ejercicio.Duracion
            }
        })

    return render_template(
        'paciente/ejecutar_sesion.html',
        sesion=sesion,
        ejercicios=ejercicios,
        ejercicios_json=ejercicios_serializados
    )


@paciente_bp.route('/ejercicios')
@login_required
@paciente_required
def ejercicios():
    ejercicios_asignados = (
        db.session.query(Ejercicio_Sesion)
        .join(Sesion)
        .filter(Sesion.Paciente_Id == current_user.Id)
        .all()
    )
    
    ejercicios_unicos = {}
    for es in ejercicios_asignados:
        if es.ejercicio.Id not in ejercicios_unicos:
            ejercicios_unicos[es.ejercicio.Id] = {
                'ejercicio': es.ejercicio,
                'video_path': get_video_path(es.ejercicio.Video),
                'veces_asignado': 0,
                'ultima_sesion': None
            }
        ejercicios_unicos[es.ejercicio.Id]['veces_asignado'] += 1
        if (not ejercicios_unicos[es.ejercicio.Id]['ultima_sesion'] or
                es.sesion.Fecha_Programada > ejercicios_unicos[es.ejercicio.Id]['ultima_sesion']):
            ejercicios_unicos[es.ejercicio.Id]['ultima_sesion'] = es.sesion.Fecha_Programada

    return render_template('paciente/ejercicios.html', ejercicios=list(ejercicios_unicos.values()))


@paciente_bp.route('/progreso')
@login_required
@paciente_required
def progreso():
    evaluaciones = (
        db.session.query(Evaluacion)
        .join(Ejercicio_Sesion)
        .join(Sesion)
        .filter(Sesion.Paciente_Id == current_user.Id)
        .order_by(Evaluacion.Fecha_Evaluacion.desc())
        .all()
    )
    
    if evaluaciones:
        puntuaciones = [e.Puntuacion for e in evaluaciones]
        stats = {
            'total_evaluaciones': len(evaluaciones),
            'puntuacion_promedio': round(sum(puntuaciones) / len(puntuaciones), 1),
            'mejor_puntuacion': max(puntuaciones),
            'ultima_evaluacion': evaluaciones[0].Fecha_Evaluacion
        }
    else:
        stats = {
            'total_evaluaciones': 0,
            'puntuacion_promedio': 0,
            'mejor_puntuacion': 0,
            'ultima_evaluacion': None
        }

    evaluaciones_json = []
    for e in evaluaciones:
        evaluaciones_json.append({
            'Puntuacion': e.Puntuacion,
            'Fecha_Evaluacion': e.Fecha_Evaluacion.isoformat() if e.Fecha_Evaluacion else None,
            'ejercicio_nombre': e.ejercicio_sesion.ejercicio.Nombre
            if e.ejercicio_sesion and e.ejercicio_sesion.ejercicio else 'Sin nombre'
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
        'paciente/progreso.html',
        evaluaciones=evaluaciones,
        stats=stats,
        evaluaciones_json=evaluaciones_json,
        evaluaciones_sesion_json=evaluaciones_sesion_json
    )


@paciente_bp.route('/ayuda')
@login_required
@paciente_required
def ayuda():
    return render_template('paciente/ayuda.html')


@paciente_bp.route('/session_info')
@login_required
@paciente_required
def session_info():
    return jsonify({
        'usuario': current_user.Nombre,
        'rol': 'Paciente',
        'tiempo_conectado': 'Sesión persistente',
        'mando_conectado': False   # ahora siempre gestionado en frontend
    })
