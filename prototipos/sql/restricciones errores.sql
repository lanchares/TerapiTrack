-- 1. Usuario con Rol_Id fuera del rango (0, 1, 2)
INSERT INTO Usuario (Nombre, Apellidos, Email, Contraseña, Rol_Id, Fecha_Registro, Estado) 
VALUES ('Test', 'User', 'test@error.com', 'pass123', 5, '2025-01-01', 1);
-- RESULTADO ESPERADO: Error CHECK constraint failed: Rol_Id

-- 2. Usuario con Estado fuera del rango (0, 1)
INSERT INTO Usuario (Nombre, Apellidos, Email, Contraseña, Rol_Id, Fecha_Registro, Estado) 
VALUES ('Test2', 'User2', 'test2@error.com', 'pass123', 1, '2025-01-01', 3);
-- RESULTADO ESPERADO: Error CHECK constraint failed: Estado

-- 3. Evaluacion con Puntuacion fuera del rango (1-5)
INSERT INTO Evaluacion (Ejercicio_Sesion_Id, Puntuacion, Comentarios, Fecha_Evaluacion) 
VALUES (1, 10, 'Puntuación inválida', '2025-01-01');
-- RESULTADO ESPERADO: Error si tienes CHECK para puntuación

-- 4. Sesion con Estado inválido
INSERT INTO Sesion (Paciente_Id, Profesional_Id, Estado, Fecha_Asignacion, Fecha_Programada) 
VALUES (1, 1, '2025-06-10', 'ESTADO_INVENTADO', '2025-06-10');
-- RESULTADO ESPERADO: Error si tienes CHECK para estado de sesión
