-- Ver todas las sesiones de cada paciente
SELECT 
    up.Nombre AS Paciente_Nombre,
    up.Apellidos AS Paciente_Apellidos,
    s.Id AS Sesion_Id,
    s.Estado,
    s.Fecha_Programada,
    s.Fecha_Asignacion
FROM Sesion s
INNER JOIN Paciente p ON s.Paciente_Id = p.Usuario_Id
INNER JOIN Usuario up ON p.Usuario_Id = up.Id
ORDER BY up.Nombre, s.Fecha_Programada;