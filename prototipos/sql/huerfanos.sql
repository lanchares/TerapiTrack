-- Buscar registros huérfanos en Paciente
SELECT p.Usuario_Id 
FROM Paciente p
LEFT JOIN Usuario u ON p.Usuario_Id = u.Id
WHERE u.Id IS NULL;

-- Buscar registros huérfanos en Profesional
SELECT pr.Usuario_Id 
FROM Profesional pr
LEFT JOIN Usuario u ON pr.Usuario_Id = u.Id
WHERE u.Id IS NULL;

-- Buscar sesiones sin paciente válido
SELECT s.Id, s.Paciente_Id
FROM Sesion s
LEFT JOIN Paciente p ON s.Paciente_Id = p.Usuario_Id
WHERE p.Usuario_Id IS NULL;

-- Buscar sesiones sin profesional válido
SELECT s.Id, s.Profesional_Id
FROM Sesion s
LEFT JOIN Profesional pr ON s.Profesional_Id = pr.Usuario_Id
WHERE pr.Usuario_Id IS NULL;

-- Buscar Ejercicio_Sesion sin sesión válida
SELECT es.Id, es.Sesion_Id
FROM Ejercicio_Sesion es
LEFT JOIN Sesion s ON es.Sesion_Id = s.Id
WHERE s.Id IS NULL;

-- Buscar evaluaciones sin Ejercicio_Sesion válido
SELECT ev.Ejercicio_Sesion_Id
FROM Evaluacion ev
LEFT JOIN Ejercicio_Sesion es ON ev.Ejercicio_Sesion_Id = es.Id
WHERE es.Id IS NULL;
