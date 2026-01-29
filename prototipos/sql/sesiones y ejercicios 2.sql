-- Contar ejercicios por sesión
SELECT 
    s.Id AS Sesion_Id,
    s.Estado,
    COUNT(es.Ejercicio_Id) AS Total_Ejercicios
FROM Sesion s
LEFT JOIN Ejercicio_Sesion es ON s.Id = es.Sesion_Id
GROUP BY s.Id;