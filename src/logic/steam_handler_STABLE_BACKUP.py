import os
import subprocess
import threading
import time
import requests
import json
import psutil
import signal
import ctypes

class SteamHandler:
    def __init__(self, log_callback):
        self.log = log_callback
        self.base_dir = os.getcwd()
        self.steamcmd_path = os.path.join(self.base_dir, "steamcmd", "steamcmd.exe")
        self.server_install_dir = os.path.join(self.base_dir, "SCUM_Server")
        self.server_exe = os.path.join(self.server_install_dir, "SCUM", "Binaries", "Win64", "SCUMServer.exe")
        
        self.app_id = "3792580"
        
        self.is_stopping = False
        self.is_restarting = False
        self.local_build_id = self.leer_build_id_local()
        
        self.process = None

    def leer_build_id_local(self):
        manifest_path = os.path.join(self.server_install_dir, "steamapps", f"appmanifest_{self.app_id}.acf")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if "buildid" in line.lower():
                            return line.split('"')[3]
            except: pass
        return "0"

    def esta_corriendo(self):
        if self.process and self.process.poll() is None:
            return True
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == "SCUMServer.exe":
                    return True
            except: pass
        return False

    def instalar_servidor(self):
        if self.esta_corriendo():
            self.log("⚠️ Update: Cerrando servidor...")
            self.detener_servidor()
            time.sleep(2)
            
        self.log(f"⬇️ Iniciando SteamCMD (AppID: {self.app_id})...")
        cmd = [self.steamcmd_path, "+force_install_dir", self.server_install_dir, "+login", "anonymous", "+app_update", self.app_id, "validate", "+quit"]

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0 
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, startupinfo=startupinfo
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None: break
                if line: self.log(line.strip())

            if process.returncode == 0:
                self.local_build_id = self.leer_build_id_local()
                self.log(f"✅ Update completado. Build ID: {self.local_build_id}")
            else:
                self.log(f"❌ SteamCMD terminó con errores (Código {process.returncode}).")
        except Exception as e: self.log(f"❌ Error crítico Update: {e}")

    def leer_salida_proceso(self):
        if not self.process: return
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line: self.log(line.strip())
                if self.is_stopping: break
        except (ValueError, OSError): pass # Handle closed pipes gracefully
        except: pass

    def obtener_argumentos_lanzamiento(self):
        args = []
        settings_path = os.path.join(self.base_dir, "data", "gui_settings.json")
        port = "7777"
        query_port = "27015"
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    data = json.load(f)
                    if "port" in data and data["port"]: port = data["port"]
                    if "query" in data and data["query"]: query_port = data["query"]
            except: pass
        args.append(f"Port={port}")
        args.append(f"QueryPort={query_port}")
        args.append("-log") 
        args.append("-NoSteamClient") 
        return args

    def iniciar_servidor(self):
        if self.esta_corriendo():
            self.log("⚠️ Servidor ya corriendo.")
            return

        self.log("🚀 LANZANDO SERVIDOR (Safe Mode)...")
        try:
            comando = [self.server_exe] + self.obtener_argumentos_lanzamiento()
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0 
            
            # IMPORTANTE: CREATE_NEW_CONSOLE
            # Esto crea una consola oculta pero válida para el servidor.
            # Es fundamental para que luego podamos hacer AttachConsole y enviar Ctrl+C.
            creation_flags = subprocess.CREATE_NEW_CONSOLE
            
            self.process = subprocess.Popen(
                comando, cwd=os.path.dirname(self.server_exe),
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, startupinfo=startupinfo, creationflags=creation_flags
            )
            threading.Thread(target=self.leer_salida_proceso, daemon=True).start()
            self.is_stopping = False
            self.is_restarting = False
        except Exception as e: self.log(f"❌ Error inicio: {e}")

    def detener_servidor(self):
        """
        ESTRATEGIA: ATTACH CONSOLE + CTRL_C (RESTAURADA)
        Esta es la técnica que funcionó.
        1. Nos desconectamos de nuestra consola (FreeConsole).
        2. Nos conectamos a la consola del servidor (AttachConsole).
        3. Desactivamos nuestro manejo de Ctrl+C para no morir.
        4. Enviamos Ctrl+C al servidor (GenerateConsoleCtrlEvent).
        5. Nos desconectamos y restauramos todo.
        """
        self.is_stopping = True
        
        if not self.process:
            self.server_running = False
            return True

        pid = self.process.pid
        self.log(f"🛑 ENVIANDO SEÑAL CTRL+C (AttachConsole PID: {pid})...")
        
        try:
            kernel32 = ctypes.windll.kernel32
            
            # 1. Liberar nuestra consola actual (si tenemos)
            kernel32.FreeConsole()
            
            # 2. Conectarse a la consola del servidor
            if kernel32.AttachConsole(pid):
                # 3. Ignorar Ctrl+C en nuestro proceso para no cerrarnos
                kernel32.SetConsoleCtrlHandler(None, True)
                
                # 4. Enviar la señal Ctrl+C (0 = CTRL_C_EVENT, 0 = Process Group)
                kernel32.GenerateConsoleCtrlEvent(0, 0)
                
                # Esperar un momento para que la señal se procese
                time.sleep(0.1)
                
                # 5. Desconectarse de la consola del servidor
                kernel32.FreeConsole()
                
                # 6. Restaurar manejo de señales
                kernel32.SetConsoleCtrlHandler(None, False)
                
                self.log("⚡ Señal enviada correctamente.")
            else:
                self.log("⚠️ No se pudo adjuntar a la consola del servidor (¿Access Denied?).")
                # Fallback: Taskkill Graceful si falla el attach
                subprocess.Popen(f"taskkill /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        except Exception as e:
            self.log(f"⚠️ Error en AttachConsole: {e}")

        # FIRE AND FORGET
        self.process = None
        self.server_running = False
        self.is_stopping = False
        
        return True

    def reinicio_seguro(self, callback_log):
        self.is_restarting = True
        callback_log("🔄 INICIANDO SECUENCIA DE REINICIO...")
        
        # 1. Attempt Safe Stop
        if not self.detener_servidor():
            callback_log("❌ Reinicio cancelado: El cierre no fue seguro.")
            self.is_restarting = False
            return
        
        # 2. Mandatory Cooldown
        callback_log("⏳ ENFRIAMIENTO: Esperando 10s para liberar archivos...")
        time.sleep(10)
        
        # 3. Start
        callback_log("🚀 Iniciando servidor...")
        self.iniciar_servidor()
        self.is_restarting = False

    def chequeo_auto_update(self):
        """
        Automático: Solo si hay versión nueva.
        """
        try:
            url = f"https://api.steamcmd.net/v1/info/{self.app_id}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                public_build = data['data'][self.app_id]['depots']['branches']['public']['buildid']
                if str(public_build) != str(self.local_build_id) and self.local_build_id != "0":
                    was_running = self.esta_corriendo()
                    
                    # Try safe stop
                    if was_running:
                        if not self.detener_servidor():
                            self.log("❌ Auto-Update cancelado: No se pudo detener el servidor de forma segura.")
                            return

                    self.instalar_servidor()
                    
                    if was_running:
                        self.iniciar_servidor()
        except: pass