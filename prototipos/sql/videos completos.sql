-- Ver videos grabados con información del ejercicio y paciente
SELECT 
    vr.Ruta_Almacenamiento,
    vr.Fecha_Expiracion,
    e.Nombre AS Ejercicio_Nombre,
    s.Id AS Sesion_Id,
    up.Nombre AS Paciente_Nombre,
    up.Apellidos AS Paciente_Apellidos
FROM Video_Respuesta vr
INNER JOIN Ejercicio_Sesion es ON vr.Ejercicio_Sesion_Id = es.Id
INNER JOIN Ejercicio e ON es.Ejercicio_Id = e.Id
INNER JOIN Sesion s ON es.Sesion_Id = s.Id
INNER JOIN Paciente p ON s.Paciente_Id = p.Usuario_Id
INNER JOIN Usuario up ON p.Usuario_Id = up.Id;
