import customtkinter as ctk
from src.ui.main_window import VoidWindow
import os
import sys
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

def main():
    check_singleton()
    print(">> Iniciando VOID SCUM SERVER MANAGER...")
    app = VoidWindow()
    app.mainloop()

if __name__ == "__main__":
    main()