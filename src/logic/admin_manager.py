import os
from src.logic.path_manager import find_server_directory

class AdminManager:
    def __init__(self, log_callback):
        self.log = log_callback
        self.base_dir = os.getcwd()
        
        # Ruta base de configuración
        server_dir = find_server_directory(self.base_dir)
        self.config_dir = os.path.join(server_dir, "SCUM", "Saved", "Config", "WindowsServer")
        
        # Rutas de los archivos
        self.file_main = os.path.join(self.config_dir, "AdminUsers.ini")
        self.file_settings = os.path.join(self.config_dir, "ServerSettingsAdminUsers.ini")

    def leer_main(self):
        """Lee el contenido completo de AdminUsers.ini tal cual está en el disco"""
        if os.path.exists(self.file_main):
            try:
                with open(self.file_main, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except: return "; Error leyendo AdminUsers.ini"
        # CAMBIO: Ya no forzamos cabeceras [GodMode]. Devolvemos vacío para que el usuario decida el formato.
        return "" 

    def leer_settings(self):
        """Lee el contenido completo de ServerSettingsAdminUsers.ini"""
        if os.path.exists(self.file_settings):
            try:
                with open(self.file_settings, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except: return "; Error leyendo ServerSettingsAdminUsers.ini"
        return "" # Vacío por defecto

    def guardar_texto_main(self, contenido):
        """
        SOBREESCRIBE AdminUsers.ini con el contenido exacto de la caja de texto.
        """
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
            
            # 'w' significa WRITE (Sobreescribir todo).
            with open(self.file_main, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            self.log("✅ AdminUsers.ini actualizado (Formato personalizado).")
            return True
        except Exception as e:
            self.log(f"❌ Error guardando AdminUsers.ini: {e}")
            return False

    def guardar_texto_settings(self, contenido):
        """
        SOBREESCRIBE ServerSettingsAdminUsers.ini con el contenido exacto de la caja de texto.
        """
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
                
            with open(self.file_settings, 'w', encoding='utf-8') as f:
                f.write(contenido)
                
            self.log("✅ ServerSettingsAdminUsers.ini actualizado.")
            return True
        except Exception as e:
            self.log(f"❌ Error guardando ServerSettingsAdminUsers.ini: {e}")
            return False