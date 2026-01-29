-- Contar ejercicios por profesional
SELECT 
    u.Nombre AS Profesional,
    COUNT(ep.Ejercicio_Id) AS Total_Ejercicios
FROM Profesional p
INNER JOIN Usuario u ON p.Usuario_Id = u.Id
LEFT JOIN Ejercicio_Profesional ep ON p.Usuario_Id = ep.Profesional_Id
GROUP BY p.Usuario_Id;