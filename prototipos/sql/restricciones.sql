-- Verificar que los roles están en el rango correcto (0, 1, 2)
SELECT Id, Nombre, Rol_Id 
FROM Usuario 
WHERE Rol_Id NOT IN (0, 1, 2);

-- Verificar que los estados están en el rango correcto (0, 1)
SELECT Id, Nombre, Estado 
FROM Usuario 
WHERE Estado NOT IN (0, 1);

-- Verificar que las puntuaciones están entre 1 y 5
SELECT Ejercicio_Sesion_Id, Puntuacion 
FROM Evaluacion 
WHERE Puntuacion NOT BETWEEN 1 AND 5;

-- Verificar que los estados de sesión son válidos
SELECT Id, Estado 
FROM Sesion 
WHERE Estado NOT IN ('PENDIENTE', 'COMPLETADA', 'CANCELADA');

-- Verificar que los tipos de profesional son válidos
SELECT Usuario_Id, Tipo_Profesional 
FROM Profesional 
WHERE Tipo_Profesional NOT IN ('MEDICO', 'ENFERMERO', 'PSICOLOGO', 'TERAPEUTA' );