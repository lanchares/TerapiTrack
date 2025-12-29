from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.controladores.decoradores import paciente_required
from src.modelos import Sesion, Ejercicio_Sesion, VideoRespuesta, Evaluacion, Paciente, Usuario
from src.extensiones import db
from datetime import datetime, timedelta
import pygame
import threading
import time
import json
import os
from collections import defaultdict


paciente_bp = Blueprint('paciente', __name__, url_prefix='/paciente')

# Inicializar pygame para el mando SNES
pygame.init()
pygame.joystick.init()
snes_controller = None

def init_snes_controller():
    global snes_controller
    try:
        pygame.joystick.quit()
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            snes_controller = pygame.joystick.Joystick(0)
            snes_controller.init()
            print(f"Mando SNES conectado: {snes_controller.get_name()}")
        else:
            print("No se detectó ningún mando SNES")
    except Exception as e:
        print(f"Error inicializando mando: {str(e)}")

def controller_monitor():
    while True:
        if snes_controller:
            pygame.event.pump()  # ✅ CRÍTICO: Esto actualiza el estado del mando
        time.sleep(0.1)

def get_video_path(video_filename):
    """Detecta si el video está en uploads/ejercicios o en videos"""
    from flask import current_app
    
    # Intentar primero en uploads/ejercicios (videos de profesionales)
    uploads_path = os.path.join(current_app.static_folder, 'uploads', 'ejercicios', video_filename)
    if os.path.exists(uploads_path):
        return f'/static/uploads/ejercicios/{video_filename}'
    
    # Si no existe, intentar en videos (ejercicios base)
    videos_path = os.path.join(current_app.static_folder, 'videos', video_filename)
    if os.path.exists(videos_path):
        return f'/static/videos/{video_filename}'
    
    # Si no existe en ningún lado, devolver la ruta por defecto
    return f'/static/uploads/ejercicios/{video_filename}'

# Inicializar al cargar
init_snes_controller()
if snes_controller:
    threading.Thread(target=controller_monitor, daemon=True).start()

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
        'mando_conectado': snes_controller is not None
    }  # ✅ CORREGIDO: Cerrar diccionario

    return render_template('paciente/dashboard.html',
                         sesiones=sesiones_proximas,
                         stats=stats)

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


@paciente_bp.route('/ejecutar_sesion/<int:sesion_id>')  # ✅ CORREGIDO: Faltaba <int:sesion_id>
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
        })  # ✅ CORREGIDO: Cerrar diccionario

    return render_template('paciente/ejecutar_sesion.html',
                         sesion=sesion,
                         ejercicios=ejercicios,
                         ejercicios_json=ejercicios_serializados)

@paciente_bp.route('/get_controller_state')
@login_required
def get_controller_state():
    """API para obtener estado del mando SNES"""
    if not snes_controller:
        return jsonify(error="Mando no conectado"), 404

    try:
        pygame.event.pump()
        
        # Obtener estado de botones
        state = {
            'X': bool(snes_controller.get_button(0)),
            'A': bool(snes_controller.get_button(1)),
            'B': bool(snes_controller.get_button(2)),
            'Y': bool(snes_controller.get_button(3)),
            'left': False,
            'right': False,
            'up': False,
            'down': False
        }
        
        # Tu mando SNES usa EJES para direccionales (no hats)
        if snes_controller.get_numaxes() >= 2:
            # Eje 0 = Izquierda/Derecha
            axis_x = snes_controller.get_axis(0)
            state['left'] = axis_x < -0.5
            state['right'] = axis_x > 0.5
            
            # Eje 1 = Arriba/Abajo
            axis_y = snes_controller.get_axis(1)
            state['up'] = axis_y < -0.5
            state['down'] = axis_y > 0.5

        return jsonify(state)
    except Exception as e:
        return jsonify(error=f"Error leyendo mando: {str(e)}"), 500


@paciente_bp.route('/reconectar_mando')
@login_required
def reconectar_mando():
    init_snes_controller()
    return jsonify(conectado=snes_controller is not None)

@paciente_bp.route('/ejercicios')
@login_required
@paciente_required
def ejercicios():
    ejercicios_asignados = db.session.query(Ejercicio_Sesion)\
                                    .join(Sesion)\
                                    .filter(Sesion.Paciente_Id == current_user.Id)\
                                    .all()
    
    ejercicios_unicos = {}
    for es in ejercicios_asignados:
        if es.ejercicio.Id not in ejercicios_unicos:
            ejercicios_unicos[es.ejercicio.Id] = {
                'ejercicio': es.ejercicio,
                'video_path': get_video_path(es.ejercicio.Video),
                'veces_asignado': 0,
                'ultima_sesion': None
            }  # ✅ CORREGIDO: Cerrar diccionario
        ejercicios_unicos[es.ejercicio.Id]['veces_asignado'] += 1
        if not ejercicios_unicos[es.ejercicio.Id]['ultima_sesion'] or \
           es.sesion.Fecha_Programada > ejercicios_unicos[es.ejercicio.Id]['ultima_sesion']:
            ejercicios_unicos[es.ejercicio.Id]['ultima_sesion'] = es.sesion.Fecha_Programada

    return render_template('paciente/ejercicios.html', ejercicios=list(ejercicios_unicos.values()))

@paciente_bp.route('/progreso')
@login_required
@paciente_required
def progreso():
    evaluaciones = db.session.query(Evaluacion)\
                            .join(Ejercicio_Sesion)\
                            .join(Sesion)\
                            .filter(Sesion.Paciente_Id == current_user.Id)\
                            .order_by(Evaluacion.Fecha_Evaluacion.desc()).all()
    
    if evaluaciones:
        puntuaciones = [e.Puntuacion for e in evaluaciones]
        stats = {
            'total_evaluaciones': len(evaluaciones),
            'puntuacion_promedio': round(sum(puntuaciones) / len(puntuaciones), 1),
            'mejor_puntuacion': max(puntuaciones),
            'ultima_evaluacion': evaluaciones[0].Fecha_Evaluacion if evaluaciones else None
        }
    else:
        stats = {
            'total_evaluaciones': 0,
            'puntuacion_promedio': 0,
            'mejor_puntuacion': 0,
            'ultima_evaluacion': None
        }

    # Detalle por ejercicio (para las tarjetas)
    evaluaciones_json = []
    for e in evaluaciones:
        evaluaciones_json.append({
            'Puntuacion': e.Puntuacion,
            'Fecha_Evaluacion': e.Fecha_Evaluacion.isoformat() if e.Fecha_Evaluacion else None,
            'ejercicio_nombre': e.ejercicio_sesion.ejercicio.Nombre if e.ejercicio_sesion and e.ejercicio_sesion.ejercicio else 'Sin nombre'
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
        'paciente/progreso.html',
        evaluaciones=evaluaciones,
        stats=stats,
        evaluaciones_json=evaluaciones_json,              # tarjetas
        evaluaciones_sesion_json=evaluaciones_sesion_json # gráfica
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
        'mando_conectado': snes_controller is not None
    })

