import sqlite3
import os

# Ruta hardcodeada basada en la estructura conocida
db_path = r"C:\Users\stink\Desktop\VOID_SCUM_MANAGER\SCUM_Server\SCUM\Saved\SaveFiles\SCUM.db"

if not os.path.exists(db_path):
    print(f"No se encontró la DB en: {db_path}")
    exit()

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Conectado a: {db_path}")
    
    # Obtener info de la tabla elevated_users
    cursor.execute("PRAGMA table_info(elevated_users);")
    columns = cursor.fetchall()
    
    if not columns:
        print("La tabla 'elevated_users' no parece existir o está vacía.")
    else:
        print("Estructura de 'elevated_users':")
        for col in columns:
            # cid, name, type, notnull, dflt_value, pk
            print(f"   - {col[1]} ({col[2]})")

    conn.close()

except Exception as e:
    print(f"Error al leer DB: {e}")
