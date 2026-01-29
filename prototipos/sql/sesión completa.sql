-- Ver información completa de cada sesión
SELECT 
    s.Id AS Sesion_Id,
    s.Estado,
    s.Fecha_Programada,
    up.Nombre AS Paciente_Nombre,
    up.Apellidos AS Paciente_Apellidos,
    upr.Nombre AS Profesional_Nombre,
    upr.Apellidos AS Profesional_Apellidos,
    pr.Especialidad,
    COUNT(es.Ejercicio_Id) AS Total_Ejercicios
FROM Sesion s
INNER JOIN Paciente p ON s.Paciente_Id = p.Usuario_Id
INNER JOIN Usuario up ON p.Usuario_Id = up.Id
INNER JOIN Profesional pr ON s.Profesional_Id = pr.Usuario_Id
INNER JOIN Usuario upr ON pr.Usuario_Id = upr.Id
LEFT JOIN Ejercicio_Sesion es ON s.Id = es.Sesion_Id
GROUP BY s.Id;
