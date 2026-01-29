-- Contar registros en cada tabla
SELECT 'Usuario' AS Tabla, COUNT(*) AS Total FROM Usuario
UNION ALL
SELECT 'Paciente' AS Tabla, COUNT(*) AS Total FROM Paciente
UNION ALL
SELECT 'Profesional' AS Tabla, COUNT(*) AS Total FROM Profesional
UNION ALL
SELECT 'Ejercicio' AS Tabla, COUNT(*) AS Total FROM Ejercicio
UNION ALL
SELECT 'Sesion' AS Tabla, COUNT(*) AS Total FROM Sesion
UNION ALL
SELECT 'Ejercicio_Sesion' AS Tabla, COUNT(*) AS Total FROM Ejercicio_Sesion
UNION ALL
SELECT 'Evaluacion' AS Tabla, COUNT(*) AS Total FROM Evaluacion
UNION ALL
SELECT 'Video_Respuesta' AS Tabla, COUNT(*) AS Total FROM Video_Respuesta;

