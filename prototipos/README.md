# Prototipos y pruebas iniciales

Esta carpeta recoge scripts, consultas SQL y capturas utilizados durante las primeras iteraciones del proyecto (por ejemplo, en el Sprint 2) para validar el modelo de datos y la integración con la base de datos.

- `python/`:
  - `test_connection.py`: script para comprobar la conexión a la base de datos mediante SQLAlchemy, ejecutando consultas sobre los modelos principales (`Usuario`, `Paciente`, `Profesional`, `Ejercicio` y `Sesion`) y verificando la integridad con `PRAGMA integrity_check`.

  - `verificar_datos.py`: script auxiliar que conecta a la base de datos y muestra información resumida (número de usuarios, pacientes, profesionales, etc.) para comprobar que el contenido es coherente durante las primeras pruebas.

- `sql/`:
  - `actualizaciones-3.sql`: actualiza la puntuación y los comentarios de una evaluación concreta y consulta después la tabla `Evaluacion` para verificar el cambio.
  
  - `deletes-3.sql`: borra una relación N:M en `Profesional_Paciente` y comprueba con un `COUNT(*)` que la fila se ha eliminado correctamente.

  - `emails-unicos.sql`: detecta posibles correos duplicados agrupando por `Email` en la tabla `Usuario`.

  - `evaluaciones-completas.sql`: muestra evaluaciones con toda la información asociada (ejercicio, sesión y datos del paciente) a partir de varias tablas relacionadas.

  - `huerfanos.sql`: busca registros huérfanos en `Paciente`, `Profesional`, `Sesion`, `Ejercicio_Sesion` y `Evaluacion` mediante `LEFT JOIN` y comprobación de claves foráneas nulas.

  - `paciente-y-sesiones.sql`: lista todas las sesiones de cada paciente con sus datos básicos, estado y fechas de asignación y programación.

  - `pacientes-y-profesionales-2.sql`: para cada paciente, cuenta cuántos profesionales tiene asociados y concatena sus nombres y apellidos a partir de la tabla intermedia `Paciente_Profesional`.

  - `profesionales-y-ejercicios-2.sql`: cuenta cuántos ejercicios tiene asignados cada profesional usando la tabla `Ejercicio_Profesional`.

  - `pruebas-integridad-referencial.sql`: intenta borrar usuarios, sesiones y ejercicios que están siendo referenciados para comprobar que las restricciones de integridad referencial impiden esos borrados.

  - `registros-tablas.sql`: realiza un resumen del número de registros en las tablas principales (`Usuario`, `Paciente`, `Profesional`, `Ejercicio`, `Sesion`, `Ejercicio_Sesion`, `Evaluacion`, `Video_Respuesta`).

  - `restricciones-errores.sql`: inserta datos inválidos (roles o estados fuera de rango, puntuaciones erróneas, estados de sesión inventados) para provocar fallos de restricciones `CHECK`.

  - `restricciones.sql`: ejecuta consultas de verificación para detectar registros que incumplan los dominios permitidos en roles, estados, puntuaciones, estados de sesión o tipos de profesional.

  - `sesion-completa.sql`: muestra información completa de cada sesión (estado, fechas, paciente, profesional, especialidad y número de ejercicios) combinando varias tablas.

  - `sesiones-y-ejercicios-2.sql`: cuenta los ejercicios asociados a cada sesión, mostrando el identificador y el estado de la sesión.

  - `Terapitrack.sql`: define el esquema de la base de datos de TerapiTrack (tablas, claves primarias, foráneas, restricciones `CHECK` e índice único de `Ejercicio_Sesion`) para SQLite.

  - `usuarios-y-pacientes-2.sql`: consulta pacientes con la información completa del usuario (nombre, apellidos, email, rol, condición médica y notas).

  - `usuarios-y-profesionales-2.sql`: consulta profesionales con sus datos de usuario (nombre, apellidos, email) y los campos específicos de especialidad y tipo de profesional.

  - `videos-completos.sql`: lista los vídeos grabados con su ruta y fecha de expiración, junto con el ejercicio, la sesión y los datos del paciente.

- `capturas/`:
  - `actualizacion-3.png` y `borrado-3.png`: capturas de DB Browser for SQLite ejecutando sentencias `UPDATE` y `DELETE` sobre la base de datos de prueba y verificando el resultado.

  - `herokudeploy_1.png`, `herokudeploy_2.png` y `heroku_1.png`–`heroku_6.png`: capturas de distintas pruebas de despliegue y comandos de diagnóstico en Heroku (logs de despliegue, ejecución de `heroku run`, comprobación de ficheros y vídeos en el servidor).

  - `probar-conexion.png`: captura de la ejecución del script de prueba de conexión a la base de datos en la terminal local.

  - `prueba-shell-flask-1.png`–`prueba-shell-flask-8.png`: capturas de sesiones de `flask shell` creando usuarios, pacientes, profesionales, sesiones, evaluaciones y vídeos, y comprobando las relaciones y métodos auxiliares de los modelos.