import os
import shutil
import datetime
import glob

class BackupManager:
    def __init__(self, log_callback):
        self.log = log_callback
        self.base_dir = os.getcwd()
        # Ruta donde está la base de datos real
        self.db_source = os.path.join(self.base_dir, "SCUM_Server", "SCUM", "Saved", "SaveFiles", "SCUM.db")
        # Carpeta donde guardaremos los backups
        self.backup_folder = os.path.join(self.base_dir, "Backups")
        
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)

    def crear_backup(self):
        if not os.path.exists(self.db_source):
            self.log("⚠️ No se encontró SCUM.db para respaldar.")
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"Backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_folder, backup_name)

        try:
            shutil.copy2(self.db_source, backup_path)
            self.log(f"💾 BACKUP CREADO: {backup_name}")
            self.limpiar_backups_antiguos()
        except Exception as e:
            self.log(f"❌ Error creando backup: {e}")

    def limpiar_backups_antiguos(self, max_backups=5):
        """Mantiene solo los X backups más recientes"""
        patron = os.path.join(self.backup_folder, "Backup_*.db")
        lista_backups = glob.glob(patron)
        
        # Ordenar por fecha de creación (el más viejo primero)
        lista_backups.sort(key=os.path.getmtime)
        
        # Si hay más de 5, borramos los sobrantes (los más viejos)
        while len(lista_backups) > max_backups:
            archivo_viejo = lista_backups.pop(0) # Sacar el primero (el más viejo)
            try:
                os.remove(archivo_viejo)
                self.log(f"🗑 Backup antiguo eliminado: {os.path.basename(archivo_viejo)}")
            except Exception as e:
                self.log(f"⚠ No se pudo borrar backup viejo: {e}")