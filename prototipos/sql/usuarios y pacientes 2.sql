-- Ver pacientes con información completa del usuario
SELECT u.Nombre, u.Apellidos, u.Email, u.Rol_Id, p.Condicion_Medica, p.Notas
FROM Paciente p
INNER JOIN Usuario u ON p.Usuario_Id = u.Id;