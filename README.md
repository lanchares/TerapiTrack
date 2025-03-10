# TerapiTrack

## Descripción
**TerapiTrack** es una herramienta web diseñada para la gestión de un entorno de terapia con rehabilitación online. Permite a los terapeutas realizar un seguimiento detallado de sus pacientes mediante ejercicios en vídeo, fomentando una recuperación más eficiente y personalizada.

## Funcionalidades principales
### Administrador:
- Crear usuarios, asignar roles y vincular pacientes con personal sanitario.
- Configurar el tiempo de almacenamiento de los vídeos grabados por los pacientes.
- Activar y desactivar usuarios.
- Gestionar sesiones de pacientes (iniciar/cerrar sesión en el dispositivo).

### Terapeuta/Médico:
- Subir vídeos de ejemplo para ejercicios.
- Crear rutinas personalizadas de ejercicios.
- Asignar rutinas específicas a pacientes concretos.
- Calificar el desempeño de los pacientes en sus ejercicios.
- Abrir canales de comunicación en tiempo real (chat/videollamada).
- Gestionar sus datos personales.

### Paciente:
- Acceder a sus rutinas asignadas para el día actual.
- Visualizar resultados y evolución según las calificaciones del terapeuta.
- Navegar por la colección global de ejercicios disponibles.
- Ver vídeos de ejemplo antes o durante la realización del ejercicio.
- Grabar su desempeño en los ejercicios y almacenarlo en el sistema.

## Tecnologías utilizadas
- **Backend**: Flask (Python) como controlador principal.
- **Frontend**: Jinja para las vistas dinámicas HTML.
- **Base de datos**: SQLAlchemy como ORM, con soporte para SQLite o cualquier base de datos compatible.
- **Gestión del proyecto**: Jira para planificación ágil mediante metodología Scrum.
- **Control de versiones**: GitHub para gestión del código fuente.
- **IDE**: Visual Studio Code como entorno de desarrollo.

## Instalación
1. Clonar el repositorio:  git clone https://github.com/lanchares/TerapiTrack.git
2. Acceder al directorio del proyecto: cd TerapiTrack
3. Instalar dependencias: pip install -r requirements.txt
4. Ejecutar la aplicación: python src/app.py

## Licencia
Este proyecto está desarrollado como parte del Trabajo Fin de Grado (TFG) y no tiene licencia pública por ahora.

## Autor
Proyecto desarrollado por [lanchares](https://github.com/lanchares).


