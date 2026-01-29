-- 3. Actualizar puntuación de una evaluación
UPDATE Evaluacion 
SET Puntuacion = 4, Comentarios = 'Mejorado después de la actualización'
WHERE Ejercicio_Sesion_Id = 1;

-- Verificar el cambio
SELECT * FROM Evaluacion WHERE Ejercicio_Sesion_Id = 1;