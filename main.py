import customtkinter as ctk
from src.ui.main_window import VoidWindow
import os
import sys
import shutil
import atexit

# Configuración Global de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

LOCK_FILE = "void_manager.lock"

def check_singleton():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is actually running
            import psutil
            if psutil.pid_exists(pid):
                print(f"⚠ YA ESTÁ EN EJECUCIÓN (PID: {pid}). Cerrando esta instancia.")
                # Opcional: Podrías intentar traer la ventana al frente aquí si tuvieras el handle
                sys.exit(0)
        except Exception:
            # Si el archivo está corrupto o no se puede leer, asumimos que no corre y lo sobreescribimos
            pass
            
    # Create lock file
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
        
    atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)

def ensure_persistence():
    """
    Si corre en modo 'frozen' (PyInstaller OneFile), verifica si las carpetas
    críticas (data, steamcmd, etc.) existen al lado del .exe.
    Si no existen, las extrae del bundle (_MEIPASS).
    Esto garantiza que los datos se guarden fuera del temp y persistan.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = sys._MEIPASS
        # En OneFile, sys.executable es la ruta al .exe, no al python interpreter
        exe_dir = os.path.dirname(sys.executable)
        
        # Lista de carpetas a persistir
        folders_to_check = ["data", "steamcmd", "installer_langs", "favicon_io"]
        
        print(f"--- VERIFICANDO PERSISTENCIA ---")
        print(f"Ubicación del Ejecutable: {exe_dir}")
        print(f"Ubicación del Bundle: {bundle_dir}")
        
        for folder in folders_to_check:
            target_path = os.path.join(exe_dir, folder)
            source_path = os.path.join(bundle_dir, folder)
            
            if not os.path.exists(target_path):
                print(f">> 📦 Primera ejecución detectada. Extrayendo: {folder} ...")
                try:
                    if os.path.exists(source_path):
                        shutil.copytree(source_path, target_path)
                        print("   ✅ Extraído correctamente.")
                    else:
                        print(f"   ⚠️ No se encontró '{folder}' dentro del ejecutable.")
                except Exception as e:
                    print(f"   ❌ Error copiando {folder}: {e}")
            else:
                print(f"   ✅ {folder} verificado (Ya existe).")
        print("--------------------------------")

def main():
    ensure_persistence()
    # check_singleton() -> Desactivado para permitir múltiples instancias
    print(">> Iniciando VOID SCUM SERVER MANAGER (Multi-Instance)...")
    app = VoidWindow()
    app.mainloop()

if __name__ == "__main__":
    main()