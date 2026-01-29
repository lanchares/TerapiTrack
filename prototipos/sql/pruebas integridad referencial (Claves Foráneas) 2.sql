-- 1. Intentar borrar un Usuario que tenga un Paciente asociado
DELETE FROM Usuario WHERE Id = (SELECT Usuario_Id FROM Paciente LIMIT 1);
-- RESULTADO ESPERADO: Error si hay ON DELETE RESTRICT
-- 2. Intentar borrar un Usuario que tenga un Profesional asociado
DELETE FROM Usuario WHERE Id = (SELECT Usuario_Id FROM Profesional LIMIT 1);
-- RESULTADO ESPERADO: Error si hay ON DELETE RESTRICT
-- 3. Intentar borrar una Sesion que tenga Ejercicio_Sesion asociados
DELETE FROM Sesion WHERE Id = (SELECT Sesion_Id FROM Ejercicio_Sesion LIMIT 1);
-- RESULTADO ESPERADO: Error si hay ON DELETE RESTRICT
-- 4. Intentar borrar un Ejercicio que esté en uso
DELETE FROM Ejercicio WHERE Id = (SELECT Ejercicio_Id FROM Ejercicio_Sesion LIMIT 1);
-- RESULTADO ESPERADO: Error si hay ON DELETE RESTRICT



