BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Ejercicio" (
	"Id"	INTEGER,
	"Nombre"	TEXT NOT NULL,
	"Descripcion"	TEXT NOT NULL,
	"Tipo"	TEXT NOT NULL,
	"Video"	TEXT NOT NULL,
	"Duracion"	INTEGER NOT NULL,
	PRIMARY KEY("Id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Ejercicio_Profesional" (
	"Profesional_Id"	INTEGER NOT NULL,
	"Ejercicio_Id"	INTEGER NOT NULL,
	PRIMARY KEY("Profesional_Id","Ejercicio_Id"),
	FOREIGN KEY("Ejercicio_Id") REFERENCES "Ejercicio"("Id"),
	FOREIGN KEY("Profesional_Id") REFERENCES "Profesional"("Usuario_Id")
);
CREATE TABLE IF NOT EXISTS "Ejercicio_Sesion" (
	"Id"	INTEGER,
	"Sesion_Id"	INTEGER NOT NULL,
	"Ejercicio_Id"	INTEGER NOT NULL,
	PRIMARY KEY("Id" AUTOINCREMENT),
	FOREIGN KEY("Ejercicio_Id") REFERENCES "Ejercicio"("Id"),
	FOREIGN KEY("Sesion_Id") REFERENCES "Sesion"("Id")
);
CREATE TABLE IF NOT EXISTS "Evaluacion" (
	"Ejercicio_Sesion_Id"	INTEGER,
	"Puntuacion"	NUMERIC NOT NULL CHECK("Puntuacion" >= 1 AND "Puntuacion" <= 5),
	"Comentarios"	TEXT,
	"Fecha_Evaluacion"	TEXT NOT NULL,
	PRIMARY KEY("Ejercicio_Sesion_Id"),
	FOREIGN KEY("Ejercicio_Sesion_Id") REFERENCES "Ejercicio_Sesion"("Id")
);
CREATE TABLE IF NOT EXISTS "Paciente" (
	"Usuario_Id"	INTEGER,
	"Fecha_Nacimiento"	TEXT NOT NULL,
	"Condicion_Medica"	TEXT,
	"Notas"	TEXT,
	PRIMARY KEY("Usuario_Id"),
	FOREIGN KEY("Usuario_Id") REFERENCES "Usuario"("Id")
);
CREATE TABLE IF NOT EXISTS "Paciente_Profesional" (
	"Paciente_Id"	INTEGER,
	"Profesional_Id"	INTEGER,
	"Fecha_Asignacion"	TEXT NOT NULL,
	PRIMARY KEY("Profesional_Id","Paciente_Id"),
	FOREIGN KEY("Paciente_Id") REFERENCES "Paciente"("Usuario_Id"),
	FOREIGN KEY("Profesional_Id") REFERENCES "Profesional"("Usuario_Id")
);
CREATE TABLE IF NOT EXISTS "Profesional" (
	"Usuario_Id"	INTEGER,
	"Especialidad"	TEXT NOT NULL,
	"Tipo_Profesional"	TEXT NOT NULL CHECK("Tipo_Profesional" IN ('MEDICO', 'TERAPEUTA', 'ENFERMERO', 'PSICOLOGO')),
	PRIMARY KEY("Usuario_Id"),
	FOREIGN KEY("Usuario_Id") REFERENCES "Usuario"("Id")
);
CREATE TABLE IF NOT EXISTS "Sesion" (
	"Id"	INTEGER,
	"Paciente_Id"	INTEGER NOT NULL,
	"Profesional_Id"	INTEGER NOT NULL,
	"Fecha_Asignacion"	TEXT NOT NULL,
	"Estado"	TEXT NOT NULL CHECK("Estado" IN ('PENDIENTE', 'COMPLETADA', 'CANCELADA')),
	"Fecha_Programada"	TEXT NOT NULL,
	PRIMARY KEY("Id" AUTOINCREMENT),
	FOREIGN KEY("Paciente_Id") REFERENCES "Paciente"("Usuario_Id"),
	FOREIGN KEY("Profesional_Id") REFERENCES "Profesional"("Usuario_Id")
);
CREATE TABLE IF NOT EXISTS "Usuario" (
	"Id"	INTEGER,
	"Nombre"	TEXT NOT NULL,
	"Apellidos"	TEXT NOT NULL,
	"Email"	TEXT NOT NULL UNIQUE,
	"Contraseña"	TEXT NOT NULL,
	"Rol_Id"	INTEGER NOT NULL CHECK("RolId" IN (0, 1, 2)),
	"Fecha_Registro"	TEXT NOT NULL,
	"Estado"	INTEGER NOT NULL CHECK("Estado" IN (0, 1)),
	PRIMARY KEY("Id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Video_Respuesta" (
	"Ejercicio_Sesion_Id"	INTEGER,
	"Ruta_Almacenamiento"	TEXT NOT NULL,
	"Fecha_Expiracion"	TEXT,
	PRIMARY KEY("Ejercicio_Sesion_Id"),
	FOREIGN KEY("Ejercicio_Sesion_Id") REFERENCES "Ejercicio_Sesion"("Id")
);
CREATE UNIQUE INDEX IF NOT EXISTS "Idice_Unico_Sesion_Ejercicio" ON "Ejercicio_Sesion" (
	"Sesion_Id",
	"Ejercicio_Id"
);
COMMIT;
