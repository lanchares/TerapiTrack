-- Ver qué profesionales atiende cada paciente
SELECT 
    up.Nombre AS Paciente,
    COUNT(pp.Profesional_Id) AS Num_Profesionales,
    GROUP_CONCAT(upr.Nombre || ' ' || upr.Apellidos) AS Profesionales
FROM Paciente p
INNER JOIN Usuario up ON p.Usuario_Id = up.Id
LEFT JOIN Profesional_Paciente pp ON p.Usuario_Id = pp.Paciente_Id
LEFT JOIN Profesional pr ON pp.Profesional_Id = pr.Usuario_Id
LEFT JOIN Usuario upr ON pr.Usuario_Id = upr.Id
GROUP BY p.Usuario_Id;