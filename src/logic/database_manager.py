import os
import sqlite3
import shutil
import time
from src.logic.path_manager import find_server_directory

class DatabaseManager:
    def __init__(self, log_callback, steam_handler):
        self.log = log_callback
        self.steam = steam_handler
        self.base_dir = os.getcwd()
        
    def get_db_path(self):
        server_dir = find_server_directory(self.base_dir)
        # La ruta típica es SCUM/Saved/SaveFiles/SCUM.db
        return os.path.join(server_dir, "SCUM", "Saved", "SaveFiles", "SCUM.db")

    def inject_super_admin(self, steam_id):
        # 1. Verificación de Estado (CRÍTICO)
        if self.steam.esta_corriendo():
            self.log("❌ ERROR: El servidor está CORRIENDO. Debes apagarlo para editar la base de datos.")
            return False, "SERVER_RUNNING"

        db_path = self.get_db_path()
        if not os.path.exists(db_path):
            self.log(f"❌ ERROR: No se encuentra la base de datos en: {db_path}")
            return False, "DB_NOT_FOUND"

        try:
            # 2. Backup de Seguridad
            backup_path = db_path + ".bak"
            shutil.copy2(db_path, backup_path)
            self.log(f"📦 Backup creado: {os.path.basename(backup_path)}")

            # 3. Conexión y Operación
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Verificar si la tabla existe (por seguridad)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='elevated_users';")
            if not cursor.fetchone():
                self.log("❌ ERROR: La tabla 'elevated_users' no existe en la DB.")
                conn.close()
                return False, "TABLE_NOT_FOUND"

            # Inyección
            # Usamos INSERT OR IGNORE para no fallar si ya existe
            # El esquema típico es (steam_id, rank) o solo (steam_id) dependiendo de la versión, 
            # pero generalmente para super admin basta con el ID si la tabla lo soporta.
            # Vamos a intentar insertar solo el ID, que es lo estándar para esta tabla.
            
            # NOTA: En algunas versiones de SCUM, la tabla puede tener más columnas.
            # Vamos a asumir la estructura simple. Si falla, el try/catch lo atrapará.
            # CORRECCIÓN: La columna se llama 'user_id', no 'steam_id'.
            cursor.execute("INSERT OR IGNORE INTO elevated_users (user_id) VALUES (?)", (str(steam_id),))
            
            changes = conn.total_changes
            conn.commit()
            conn.close()

            if changes > 0:
                self.log(f"✅ ÉXITO: Usuario {steam_id} inyectado como Super Admin.")
                return True, "SUCCESS"
            else:
                self.log(f"⚠️ AVISO: El usuario {steam_id} ya estaba en la base de datos.")
                return True, "ALREADY_EXISTS"

        except Exception as e:
            self.log(f"❌ Error crítico en DB: {e}")
            return False, str(e)
