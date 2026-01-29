-- 3. Borrar una relación N:M
DELETE FROM Profesional_Paciente WHERE Paciente_Id = 2 AND Profesional_Id = 3;

-- Verificar que se borró
SELECT COUNT(*) FROM Profesional_Paciente WHERE Paciente_Id = 2 AND Profesional_Id = 3;