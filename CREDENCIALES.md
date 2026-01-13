# Credenciales y acceso a TerapiTrack

Este documento recoge la información necesaria para que el tribunal y otros revisores puedan acceder a la instancia desplegada de TerapiTrack y probar la aplicación con distintos perfiles de usuario.

## URL de despliegue

La aplicación está desplegada en:

- https://terapitrack-tfg-dccabad31cfb.herokuapp.com

## Cuentas de acceso de prueba

Las cuentas de prueba se corresponden con los usuarios creados por el script `poblar_bd.py`. Todas las contraseñas son ficticias y se han definido únicamente para la evaluación del TFG.

### Administrador

- Usuario: `admin@terapitrack.com`  
- Contraseña: `admin123`

### Profesionales sanitarios

Los siguientes usuarios tienen rol de profesional sanitario:

- Usuario: `juan.perez@terapitrack.com` — Contraseña: `medico123`
- Usuario: `ana.lopez@terapitrack.com` — Contraseña: `terapeuta123`
- Usuario: `carlos.gomez@terapitrack.com` — Contraseña: `psicologo123`
- Usuario: `luis.martinez@terapitrack.com` — Contraseña: `enfermero123`
- Usuario: `maria.sanchez@terapitrack.com` — Contraseña: `medico123`

### Pacientes

El script crea 15 pacientes con rol 1, todos con la misma contraseña:

- Contraseña común: `paciente123`

Algunos ejemplos de cuentas de paciente:

- Usuario: `antonio.garcia@email.com`
- Usuario: `mariacarmen.lopez@email.com`
- Usuario: `josemanuel.rodriguez@email.com`
- Usuario: `isabel.fernandez@email.com`
