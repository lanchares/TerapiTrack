-- Ver profesionales con información completa del usuario
SELECT u.Nombre, u.Apellidos, u.Email, pr.Especialidad, pr.Tipo_Profesional
FROM Profesional pr
INNER JOIN Usuario u ON pr.Usuario_Id = u.Id;