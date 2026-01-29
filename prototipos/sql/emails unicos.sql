-- Verificar emails únicos
SELECT Email, COUNT(*) AS Duplicados
FROM Usuario
GROUP BY Email
HAVING COUNT(*) > 1;
