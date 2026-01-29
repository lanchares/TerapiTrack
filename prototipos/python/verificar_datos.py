import sqlite3
import os

# Ruta a tu base de datos
db_path = "instance/TerapiTrack.db"

if os.path.exists(db_path):
    print(f" Base de datos encontrada: {db_path}")
    print(f" Tamaño: {os.path.getsize(db_path)} bytes")
    
    # Conectar y verificar datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Listar todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    print(f"\n Tablas encontradas ({len(tablas)}):")
    for tabla in tablas:
        print(f"   - {tabla[0]}")
    
    # Verificar usuarios
    cursor.execute("SELECT COUNT(*) FROM Usuario")
    usuarios = cursor.fetchone()[0]
    print(f"\n👤 Usuarios: {usuarios}")
    
    # Verificar algunos usuarios específicos
    cursor.execute("SELECT Nombre, Email, Rol_Id FROM Usuario LIMIT 5")
    usuarios_data = cursor.fetchall()
    print("\n👥 Primeros usuarios:")
    for user in usuarios_data:
        roles = {0: 'Admin', 1: 'Paciente', 2: 'Profesional'}
        print(f"   - {user[0]} ({user[1]}) - {roles.get(user[2], 'Desconocido')}")
    
    conn.close()
    print("\n ¡La base de datos está funcionando correctamente!")
    
else:
    print(f" No se encontró la base de datos en: {db_path}")
