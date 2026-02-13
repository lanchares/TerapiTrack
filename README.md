# TerapiTrack

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-99%25%20Coverage-brightgreen.svg)]()

Sistema web de gestión de terapias de rehabilitación online para pacientes con dificultades motoras.

---

## Descripción

**TerapiTrack** es una plataforma web diseñada para facilitar la gestión de terapias de rehabilitación a distancia. Permite a profesionales sanitarios realizar seguimiento detallado de sus pacientes mediante ejercicios en vídeo, evaluaciones personalizadas y visualización del progreso temporal.

El sistema está especialmente adaptado para **pacientes con dificultades motoras** (ej. Parkinson), ofreciendo una interfaz accesible controlable mediante **mando SNES** para facilitar la navegación y ejecución de ejercicios.

---

## Funcionalidades principales

### Administrador
- Gestión completa de usuarios (crear, editar, activar/desactivar)
- Asignación de roles (Administrador, Profesional, Paciente)
- Vinculación de pacientes con profesionales sanitarios
- Configuración del sistema (políticas de retención de vídeos, límites de almacenamiento)
- Exportación de datos de usuarios a CSV
- Dashboard con estadísticas globales del sistema

### Profesional Sanitario
- Creación y gestión de ejercicios terapéuticos con vídeos demostrativos
- Creación de rutinas personalizadas de ejercicios
- Asignación de sesiones a pacientes con fechas programadas
- Ejecución de sesiones en tiempo real con sincronización profesional-paciente
- Evaluación de ejercicios grabados con reproductor lado a lado (demo vs ejecución del paciente)
- Visualización del progreso de pacientes con gráficos temporales
- Dashboard con sesiones pendientes y evaluaciones por realizar

### Paciente
- Acceso a rutinas asignadas con calendario de 3 semanas
- Ejecución de sesiones con pantalla dividida (vídeo demo + grabación propia)
- Grabación automática de ejercicios durante la sesión
- Control mediante mando SNES para mayor accesibilidad
- Visualización de evaluaciones históricas
- Dashboard con gráficos de evolución temporal
- Consulta de ejercicios disponibles
- Manual de ayuda integrado para uso del mando

---

## Tecnologías utilizadas

### Backend
- **Flask 3.1.0** - Framework web principal
- **SQLAlchemy 2.0.39** - ORM para gestión de base de datos
- **Flask-Login 0.6.3** - Gestión de autenticación y sesiones
- **Flask-WTF 1.2.2** - Formularios con validación
- **Bcrypt 4.3.0** - Cifrado de contraseñas
- **Gunicorn 23.0.0** - Servidor WSGI para producción

### Frontend
- **Jinja2 3.1.6** - Motor de plantillas HTML
- **Bootstrap 5** - Framework CSS responsive
- **Chart.js** - Gráficos de progresión temporal
- **Gamepad API** - Integración de mando SNES

### Base de datos
- **SQLite** (desarrollo local)
- **PostgreSQL** (producción en Heroku)
- Migración automática entre ambas

### Multimedia
- **Cloudinary** - Almacenamiento de vídeos en la nube
- **MediaRecorder API** - Grabación de vídeo del paciente
- **MoviePy 1.0.3** - Cálculo de duración de vídeos

### Testing
- **Pytest 8.4.0** - Framework de testing
- **Pytest-cov 6.2.1** - Cobertura de código (100% en modelos)

### Gestión del proyecto
- **Jira** - Planificación ágil con metodología Scrum
- **GitHub** - Control de versiones y trazabilidad

---

## Instalación y configuración

### Requisitos previos
- Python 3.11 o superior
- pip (gestor de paquetes Python)
- Git
- Cuenta en Cloudinary (para almacenamiento de vídeos)

### Instalación local

1. **Clonar el repositorio:**
git clone https://github.com/lanchares/TerapiTrack.git
cd TerapiTrack

2. **Crear entorno virtual:**
python -m venv venv

Activar entorno (Windows)
venv\Scripts\activate

Activar entorno (Linux/Mac)
source venv/bin/activate

3. **Instalar dependencias:**
pip install -r requirements.txt

4. **Configurar variables de entorno:**

Crear archivo `.env` en la raíz del proyecto:
SECRET_KEY=tu_clave_secreta_aqui
DATABASE_URL=sqlite:///TerapiTrack.db
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

5. **Poblar la base de datos con datos de prueba:**
python poblar_bd.py

Este script crea automáticamente:
- 1 administrador del sistema
- 5 profesionales sanitarios (médico, terapeuta, psicólogo, enfermero)
- 15 pacientes con enfermedad de Parkinson
- 14 ejercicios específicos para rehabilitación neurológica
- Sesiones de ejemplo (completadas y pendientes)
- Evaluaciones de prueba con puntuaciones

6. **Ejecutar la aplicación:**
python app.py

7. **Acceder a la aplicación:**
http://localhost:5000

---

## Usuarios de prueba

Después de ejecutar `poblar_bd.py`, puedes acceder con estas credenciales:

### Administrador
- **Email:** admin@terapitrack.com
- **Contraseña:** admin123

### Profesionales
- **Email:** juan.perez@terapitrack.com
- **Contraseña:** medico123

*(También disponibles: ana.lopez, carlos.gomez, luis.martinez, maria.sanchez @terapitrack.com)*

### Pacientes
- **Email:** antonio.garcia@email.com
- **Contraseña:** paciente123

*(También disponibles: mariacarmen.lopez, josemanuel.rodriguez, isabel.fernandez, etc. @email.com)*

---

## Ejecutar tests

### Tests unitarios con reporte de cobertura:
pytest tests/ -v --cov=src --cov-report=html

### Ver reporte de cobertura en navegador:
Windows
start htmlcov/index.html

Linux/Mac
open htmlcov/index.html

### Ejecutar solo tests de un módulo específico:
pytest tests/test_admin_controlador.py -v

---

## Uso del mando SNES

TerapiTrack incluye soporte completo para mandos SNES conectados por USB, facilitando el uso a pacientes con dificultades motoras.

### Controles

| Botón | Función |
|-------|---------|
| Cruceta ↑↓←→ | Navegación entre elementos |
| A (Rojo) | Seleccionar / Confirmar |
| B (Amarillo) | Acción secundaria |
| X (Azul) | Ver ejercicios |
| Y (Verde) | Volver / Cancelar |

El mando funciona en todas las pantallas del área de paciente (dashboard, sesiones, ejercicios, progreso, ayuda).

---

## Despliegue en Heroku

**Aplicación en producción:** [https://terapitrack-tfg-dccabad31cfb.herokuapp.com/](https://terapitrack-tfg-dccabad31cfb.herokuapp.com/)

1. Crear aplicación en Heroku
2. Añadir addon PostgreSQL:
heroku addons:create heroku-postgresql:mini
3. Configurar variables de entorno en el dashboard de Heroku
4. Desplegar:
git push heroku main

---

## Gestión del proyecto

- **Metodología:** Scrum con sprints de 1-2 semanas
- **Tablero Jira:** https://terapitrack.atlassian.net/
- **Tareas completadas:** 77 de 86 (90%)
- **Épicas:** Usuarios, Ejercicios, Sesiones, Grabación, Interfaz, Configuración, Documentación

---

## Documentación

La documentación completa (memoria y anexos técnicos) se encuentra en la carpeta `doc/` en formato LaTeX.

Incluye:
- Plan de proyecto y planificación temporal
- Estudio de viabilidad
- Requisitos funcionales y no funcionales
- Diseño de base de datos (ER, relacional, diccionario de datos)
- Casos de uso detallados
- Manuales del programador y usuario

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT.

El texto completo de la licencia se encuentra en el archivo [`LICENSE`](LICENSE) incluido en este repositorio.

---

## Autor

**Alberto Lanchares Díez**  
GitHub: [@lanchares](https://github.com/lanchares)

---

## Agradecimientos

A mis tutores del TFG por su guía durante el desarrollo del proyecto.