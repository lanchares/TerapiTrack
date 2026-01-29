-- Ver evaluaciones con información del ejercicio, sesión y paciente
SELECT 
    ev.Puntuacion,
    ev.Comentarios,
    ev.Fecha_Evaluacion,
    e.Nombre AS Ejercicio_Nombre,
    s.Id AS Sesion_Id,
    up.Nombre AS Paciente_Nombre,
    up.Apellidos AS Paciente_Apellidos
FROM Evaluacion ev
INNER JOIN Ejercicio_Sesion es ON ev.Ejercicio_Sesion_Id = es.Id
INNER JOIN Ejercicio e ON es.Ejercicio_Id = e.Id
INNER JOIN Sesion s ON es.Sesion_Id = s.Id
INNER JOIN Paciente p ON s.Paciente_Id = p.Usuario_Id
INNER JOIN Usuario up ON p.Usuario_Id = up.Id;
