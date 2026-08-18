import os
import subprocess
import threading
import time
import requests
import json
import psutil
import signal
import ctypes
import zipfile
import urllib.request
import re
import sys

# Flags seguros para ejecutar SteamCMD sin consola desde una app windowed (.exe compilado)
# DETACHED_PROCESS (0x00000008) evita herencia de handles de consola → no WinError 6
_DETACHED = 0x00000008
_NO_WINDOW = 0x08000000
_SAFE_FLAGS = _DETACHED | _NO_WINDOW


def _get_base_dir():
    """Devuelve el directorio base correcto tanto en desarrollo como en .exe compilado."""
    # Preferir la variable de entorno establecida por main.py
    env_dir = os.environ.get("ONYX_EXE_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.getcwd()


class SteamHandler:
    def __init__(self, log_callback):
        self.log = log_callback
        self.base_dir = _get_base_dir()
        self.steamcmd_path = os.path.join(self.base_dir, "steamcmd", "steamcmd.exe")
        self.server_install_dir = os.path.join(self.base_dir, "SCUM_Server")
        self.server_exe = os.path.join(self.server_install_dir, "SCUM", "Binaries", "Win64", "SCUMServer.exe")
        
        self.app_id = "3792580"

        self.is_stopping    = False
        self.is_restarting  = False
        self.local_build_id = self.leer_build_id_local()

        self.process = None

        # Candado de operaciones de ciclo de vida del servidor.
        # Serializa reinicio_seguro / chequeo_auto_update para que NUNCA se
        # solapen un reinicio programado, un auto-update y un reinicio manual
        # (lo que dejaba el servidor colgado/offline de forma intermitente).
        self._op_lock = threading.Lock()

        # Vigilante dedicado de la ventana de arranque tras un reinicio AUTOMÁTICO.
        # Mientras está activo, el guardián general cede para no pisarse con él.
        self._vigilancia_arranque_activa = False

        # Guardian de proceso
        self._guardian_activo  = False
        self._guardian_log     = None
        self._guardian_thread  = None
        self._guardian_intento = 0   # cuantas veces ha intentado reiniciar seguidas

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

    def _proceso_scum_vivo(self):
        """
        True si hay un SCUMServer.exe corriendo desde NUESTRA carpeta.
        Seguro ante exe=None / AccessDenied (no lanza TypeError).
        """
        target_path = os.path.normpath(self.server_exe).lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                nombre = proc.info.get('name')
                if not nombre or "scumserver" not in nombre.lower():
                    continue
                exe = proc.info.get('exe')
                if exe and os.path.normpath(exe).lower() == target_path:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                continue
        return False

    def esta_corriendo(self):
        # 1. Referencia interna al proceso
        if self.process:
            if self.process.poll() is None:
                return True
            self.process = None  # estaba muerto, limpiar referencia
        # 2. Búsqueda global pero específica de NUESTRA ruta
        return self._proceso_scum_vivo()

    def _taskkill_forzado(self):
        """
        Mata cualquier SCUMServer.exe de forma forzada (taskkill /F).
        ÚLTIMO RECURSO: puede provocar rollback del mundo. No usar en el
        camino normal de apagado.
        """
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/IM", "SCUMServer.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=_NO_WINDOW
            )
        except Exception:
            pass

    def _esperar_muerte(self, timeout):
        """
        Espera hasta `timeout` segundos a que el proceso SCUM desaparezca.
        Sondea cada 0.5s y SALE en cuanto el proceso muere (no agota el timeout
        si cierra antes). Devuelve True si murió dentro del plazo.
        """
        pasos = max(1, int(timeout / 0.5))
        for _ in range(pasos):
            ref_muerta = (not self.process) or (self.process.poll() is not None)
            if ref_muerta and not self._proceso_scum_vivo():
                return True
            time.sleep(0.5)
        return not self._proceso_scum_vivo()

    def _run_steamcmd_silent(self, args, timeout=120):
        """
        Ejecuta steamcmd sin ventana y sin heredar handles de consola.
        Usa DETACHED_PROCESS para evitar WinError 6 en apps windowed (.exe compilado).
        """
        cmd = [self.steamcmd_path] + args
        try:
            # Redirigir stdout/stderr a DEVNULL para no necesitar handles válidos de consola
            with open(os.devnull, 'wb') as devnull:
                proc = subprocess.Popen(
                    cmd,
                    stdout=devnull,
                    stderr=devnull,
                    stdin=subprocess.DEVNULL,
                    creationflags=_SAFE_FLAGS
                )
                proc.wait(timeout=timeout)
                return proc.returncode
        except Exception as e:
            self.log(f"⚠️ _run_steamcmd_silent error: {e}")
            return -1

    def descargar_steamcmd(self):
        steamcmd_dir = os.path.dirname(self.steamcmd_path)
        os.makedirs(steamcmd_dir, exist_ok=True)
        zip_path = os.path.join(steamcmd_dir, "steamcmd.zip")
        url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
        try:
            self.log("\u2b07\ufe0f Descargando SteamCMD desde Steam...")

            def progreso(count, block_size, total):
                if total > 0:
                    pct = int(count * block_size * 100 / total)
                    if pct % 20 == 0:
                        self.log(f"   \U0001f4e6 Descargando... {min(pct, 100)}%")

            urllib.request.urlretrieve(url, zip_path, reporthook=progreso)
            self.log("\U0001f4e6 Extrayendo SteamCMD...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(steamcmd_dir)
            os.remove(zip_path)
            self.log("\u23f3 Ejecutando SteamCMD por primera vez para que se auto-actualice...")
            # IMPORTANTE: esta primera ejecución descarga la config de Steam
            # que luego necesita para poder instalar apps (evita error código 8)
            self._run_steamcmd_silent(["+quit"], timeout=120)
            self.log("\u2705 SteamCMD listo.")
            return True
        except Exception as e:
            self.log(f"\u274c Error descargando SteamCMD: {e}")
            return False

    def instalar_servidor(self):
        # Descargar SteamCMD automáticamente si no existe
        if not os.path.exists(self.steamcmd_path):
            self.log("⚠️ SteamCMD no encontrado. Iniciando descarga automática...")
            if not self.descargar_steamcmd():
                self.log("❌ No se pudo instalar SteamCMD. Abortando.")
                return

        # DETENER GUARDIAN PARA QUE NO SE INTERRUMPA LA ACTUALIZACIÓN
        was_guardian_active = self._guardian_activo
        self.detener_guardian()

        was_running = self.esta_corriendo()
        if was_running:
            self.log("⚠️ Update: Cerrando servidor...")
            self.detener_servidor()
            time.sleep(2)

        # Crear carpeta de instalación si no existe
        os.makedirs(self.server_install_dir, exist_ok=True)

        # PASO PREVIO: forzar actualización de config de Steam para evitar
        # el error 'Missing configuration' (código 8) en la primera instalación
        self.log("⏳ Preparando Steam (descargando config)...")
        self._run_steamcmd_silent(["+quit"], timeout=120)

        self.log(f"⬇️ Iniciando instalación/actualización del servidor SCUM (AppID: {self.app_id})...")
        cmd = [self.steamcmd_path, "+force_install_dir", self.server_install_dir, "+login", "anonymous", "+app_update", self.app_id, "validate", "+quit"]

        exito = False
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            if intento > 1:
                self.log(f"🔄 Reintentando instalación (intento {intento}/{max_intentos})...")
                time.sleep(3)
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=_SAFE_FLAGS
                )
                # Leer en chunks para capturar líneas con \r (progreso de SteamCMD)
                buffer = b""
                ultima_progreso = ""
                while True:
                    chunk = process.stdout.read(512)
                    if not chunk:
                        break
                    buffer += chunk
                    partes = re.split(b'\r\n|\r|\n', buffer)
                    buffer = partes[-1]
                    for parte in partes[:-1]:
                        linea = parte.decode("utf-8", errors="replace").strip()
                        if not linea:
                            continue
                        # Para líneas de progreso [XX%] solo mostrar si cambió
                        if re.match(r'^\[[\s\d\-]+%\]', linea):
                            if linea != ultima_progreso:
                                self.log(linea)
                                ultima_progreso = linea
                        else:
                            self.log(linea)
                if buffer:
                    linea = buffer.decode("utf-8", errors="replace").strip()
                    if linea:
                        self.log(linea)
                process.wait()

                if process.returncode == 0:
                    self.local_build_id = self.leer_build_id_local()
                    self.log(f"✅ Instalación completada. Build ID: {self.local_build_id}")
                    exito = True
                    break
                elif process.returncode == 8:
                    # Código 8 = "Missing configuration" — error transitorio de Steam CDN
                    # En el siguiente intento la config ya estará cacheada
                    self.log(f"⚠️ Steam no tiene la configuración lista aún (código 8). Reintentando...")
                else:
                    self.log(f"❌ SteamCMD terminó con errores (Código {process.returncode}).")
                    break
            except Exception as e:
                self.log(f"❌ Error crítico en instalación: {e}")
                break

        if not exito:
            self.log("❌ No se pudo completar la instalación después de varios intentos. Verifica tu conexión o inténtalo más tarde.")

        # Restaurar estado de servidor y guardián
        if was_running:
            self.log("🚀 Reiniciando servidor post-actualización...")
            self._reaplicar_config_gui(self.log)
            self._arrancar_y_verificar(intentos=2, log=self.log)

        if was_guardian_active:
            self.iniciar_guardian(self.log)

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
        # Leer config desde AppData (donde se guarda en modo .exe)
        # Fallback: junto al exe (desarrollo)
        appdata = os.environ.get("ONYX_APPDATA_DIR")
        if appdata:
            settings_path = os.path.join(appdata, "data", "gui_settings.json")
        else:
            settings_path = os.path.join(self.base_dir, "data", "gui_settings.json")

        port = "7777"
        query_port = "27015"
        nobattleye_enabled = False

        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    data = json.load(f)
                    if "port" in data and data["port"]: port = data["port"]
                    if "query" in data and data["query"]: query_port = data["query"]
                    if "nobattleye" in data and data["nobattleye"] == 1:
                        nobattleye_enabled = True
            except: pass
        
        args.append(f"Port={port}")
        args.append(f"QueryPort={query_port}")
        args.append("-log") 
        args.append("-NoSteamClient") 

        if nobattleye_enabled:
            args.append("-nobattleye")
            args.append("-fileopenlog")
            
        return args

    def iniciar_servidor(self):
        """
        Lanza el servidor SCUM.

        NO fuerza cierres aquí (eso lo maneja detener_servidor de forma limpia).
        Si por alguna razón aún hay un proceso cerrándose, le damos un margen
        breve para que termine LIMPIO — nunca un taskkill /F, porque podría
        provocar rollback del mundo. El arranque NUNCA se aborta.
        """
        # Si el proceso anterior aún se está cerrando, esperarlo limpio (sin forzar)
        if self._proceso_scum_vivo():
            self.log("⏳ [Inicio] Aún hay un proceso SCUM cerrándose. Esperando cierre limpio...")
            self._esperar_muerte(30)

        self.log("🚀 LANZANDO SERVIDOR (Safe Mode)...")
        try:
            comando = [self.server_exe] + self.obtener_argumentos_lanzamiento()
            self.log(f"🔎 DEBUG COMANDO: {comando}")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            # CREATE_NEW_CONSOLE: crea una consola oculta pero valida para el servidor.
            # Es fundamental para que luego podamos hacer AttachConsole y enviar Ctrl+C.
            creation_flags = subprocess.CREATE_NEW_CONSOLE

            self.process = subprocess.Popen(
                comando, cwd=os.path.dirname(self.server_exe),
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, startupinfo=startupinfo, creationflags=creation_flags
            )
            threading.Thread(target=self.leer_salida_proceso, daemon=True).start()
            self.log("✅ [Inicio] Proceso del servidor lanzado correctamente.")
        except Exception as e:
            self.log(f"❌ Error inicio: {e}")
            self.process = None
        finally:
            self.is_stopping    = False
            self.is_restarting  = False

    def _arrancar_y_verificar(self, intentos=2, log=None):
        """
        Arranca el servidor y CONFIRMA que el proceso se sostiene los primeros
        segundos (detecta puerto ocupado / crash inmediato). Si el proceso muere
        al instante, reintenta el ARRANQUE. Nunca fuerza cierres (sin rollback).

        Garantía: siempre se intenta arrancar; devuelve True si el proceso quedó
        vivo y estable, False si no se pudo sostener tras varios intentos.
        """
        log = log or self.log
        for intento in range(1, intentos + 1):
            self.iniciar_servidor()
            sostiene = False
            for _ in range(12):  # ~12s observando que el proceso no muera al arrancar
                time.sleep(1)
                if self.process and self.process.poll() is None:
                    sostiene = True
                else:
                    sostiene = False
                    break
            if sostiene and self._proceso_scum_vivo():
                log(f"✅ [Arranque] Servidor en marcha (intento {intento}/{intentos}).")
                return True
            log(f"⚠️ [Arranque] El proceso no se sostuvo (intento {intento}/{intentos}).")
        log("🚨 [Arranque] No se pudo mantener el servidor activo tras varios intentos.")
        return False


    def detener_servidor(self, espera_graceful=60):
        """
        APAGADO LIMPIO (ATTACH CONSOLE + CTRL_C) — método intacto que evita rollback.
        1. Nos desconectamos de nuestra consola (FreeConsole).
        2. Nos conectamos a la consola del servidor (AttachConsole).
        3. Desactivamos nuestro manejo de Ctrl+C para no morir.
        4. Enviamos Ctrl+C al servidor (GenerateConsoleCtrlEvent).
        5. ESPERAMOS pacientemente a que SCUM termine de guardar y se cierre solo.

        CLAVE ANTI-ROLLBACK: tras enviar el Ctrl+C NO matamos el proceso a la
        fuerza. Le damos hasta `espera_graceful` segundos para completar su
        guardado (salimos en cuanto cierra). Sólo si queda colgado de verdad
        forzamos como ÚLTIMO recurso, avisando del riesgo.

        Devuelve True si el proceso terminó (limpio o forzado), False si no se
        pudo confirmar el cierre.
        """
        self.is_stopping = True

        try:
            if not self.process:
                self.server_running = False
                return True   # finally se ejecuta igualmente y limpia is_stopping

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

                    # Pequeña pausa para que la señal se entregue
                    time.sleep(1.0)

                    # 5. Desconectarse de la consola del servidor
                    kernel32.FreeConsole()

                    # 6. Restaurar manejo de señales
                    kernel32.SetConsoleCtrlHandler(None, False)

                    self.log("⚡ Señal de apagado limpio enviada. Esperando a que SCUM guarde y cierre...")
                else:
                    # Sin consola adjunta no podemos mandar Ctrl+C: pedimos cierre
                    # graceful con taskkill SIN /F (envía WM_CLOSE, no mata a la fuerza).
                    self.log("⚠️ No se pudo adjuntar a la consola. Pidiendo cierre graceful (sin /F)...")
                    subprocess.run(f"taskkill /PID {pid} /T", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   stdin=subprocess.DEVNULL, creationflags=_NO_WINDOW)

            except Exception as e:
                self.log(f"⚠️ Error en AttachConsole: {e}")
                # FALLBACK graceful (sin /F) para no arriesgar rollback
                try:
                    subprocess.run(f"taskkill /PID {pid} /T", shell=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   stdin=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                except Exception:
                    pass

            # --- Esperar PACIENTEMENTE el cierre limpio (sin matar) ---
            # Sale en cuanto el proceso muere; el techo sólo aplica si se cuelga.
            if self._esperar_muerte(espera_graceful):
                self.log("✅ Servidor cerrado limpiamente (sin rollback).")
                self.process = None
                self.server_running = False
                return True

            # ÚLTIMO RECURSO: el proceso quedó colgado de verdad tras esperar mucho.
            self.log(f"🚨 El servidor no cerró en {espera_graceful}s (proceso colgado). "
                     f"Forzando como último recurso (posible rollback)...")
            self._taskkill_forzado()
            self.process = None
            self.server_running = False
            return self._esperar_muerte(8)

        finally:
            self.is_stopping = False

    # -------------------------------------------------------------------------
    # GUARDIAN DE PROCESO
    # Verifica cada 90s que el servidor siga corriendo.
    # Si cayo sin que el admin lo detuviera, lo reinicia automaticamente.
    # -------------------------------------------------------------------------

    def iniciar_guardian(self, log_fn):
        """Lanza el hilo guardian. Llamar despues de iniciar el servidor."""
        self._guardian_log    = log_fn
        self._guardian_activo = True
        self._guardian_intento = 0
        if self._guardian_thread and self._guardian_thread.is_alive():
            return  # ya esta corriendo
        self._guardian_thread = threading.Thread(
            target=self._guardian_loop, daemon=True, name="ServerGuardian"
        )
        self._guardian_thread.start()
        log_fn("🛡️ [Guardian] Vigilancia de proceso activada (chequeo cada 90s).")

    def detener_guardian(self):
        """Detiene el guardian (llamar cuando el admin detiene el servidor a proposito)."""
        self._guardian_activo = False

    def _guardian_sleep(self, segundos):
        """Duerme en trozos de 1s respetando _guardian_activo. False si hay que salir."""
        for _ in range(int(segundos)):
            if not self._guardian_activo:
                return False
            time.sleep(1)
        return self._guardian_activo

    def _guardian_loop(self):
        """Hilo interno: vigila que el servidor no caiga sin querer."""
        CHECK_INTERVAL = 30   # segundos entre chequeos (detección rápida para el SLA)
        MAX_INTENTOS   = 3    # maximo de reinicios consecutivos antes de alertar

        while self._guardian_activo:
            # Esperar el intervalo respetando detener_guardian()
            if not self._guardian_sleep(CHECK_INTERVAL):
                return

            # Durante la ventana post-reinicio manda el vigilante dedicado: ceder.
            if self._vigilancia_arranque_activa:
                self._guardian_intento = 0
                continue

            # Si el admin esta deteniendo/reiniciando manualmente, esperar
            if self.is_stopping or self.is_restarting:
                self._guardian_intento = 0
                continue

            # Comprobar si el servidor sigue vivo
            if self.esta_corriendo():
                self._guardian_intento = 0   # esta bien, resetear contador
                continue

            # ----- Servidor caido detectado -----
            self._guardian_intento += 1
            log = self._guardian_log or self.log

            if self._guardian_intento > MAX_INTENTOS:
                log(
                    f"🚨 [Guardian] El servidor cayo {self._guardian_intento} veces seguidas. "
                    "Verifica el servidor manualmente."
                )
                # Seguir vigilando pero no reiniciar mas hasta que el admin actue
                if not self._guardian_sleep(300):
                    return
                self._guardian_intento = 0
                continue

            log(
                f"🔴 [Guardian] Servidor caido detectado "
                f"(intento {self._guardian_intento}/{MAX_INTENTOS}). "
                "Reiniciando automaticamente..."
            )
            try:
                # Re-chequear justo antes de arrancar: el admin pudo intervenir
                if not self._guardian_activo or self.is_stopping or self.is_restarting:
                    continue
                # No solapar con un reinicio/auto-update en curso (p.ej. SteamCMD
                # descargando con el servidor detenido a propósito).
                if not self._op_lock.acquire(blocking=False):
                    log("⏳ [Guardian] Hay una operación de servidor en curso (update/reinicio). "
                        "Reintento pospuesto.")
                    self._guardian_intento -= 1   # no contar como caída real
                    continue
                try:
                    if self._arrancar_y_verificar(intentos=1, log=log):
                        log("✅ [Guardian] Servidor reiniciado correctamente.")
                        self._guardian_intento = 0
                    else:
                        log("⚠️ [Guardian] El servidor no arranco despues del intento de reinicio.")
                finally:
                    self._op_lock.release()
            except Exception as e:
                log(f"❌ [Guardian] Error al reiniciar: {e}")


    # -------------------------------------------------------------------------
    # VIGILANTE DE ARRANQUE POST-REINICIO (solo para reinicios AUTOMÁTICOS)
    # Vigila toda la ventana de carga del mundo (no solo que el proceso nazca):
    # si el servidor no arrancó o se cae mientras carga, lo vuelve a iniciar.
    # -------------------------------------------------------------------------

    def vigilar_arranque_post_reinicio(self, log_fn, ventana=240, intervalo=10,
                                       estable_necesario=90, max_reintentos=3):
        """
        Lanza un vigilante DEDICADO para la ventana crítica tras un reinicio
        AUTOMÁTICO. A diferencia del guardián general (que solo mira que el
        proceso exista cada 30s), este confirma que el servidor se mantiene
        vivo durante toda la carga del mundo. Si el proceso muere o nunca
        arrancó dentro de la ventana, lo vuelve a iniciar (hasta max_reintentos).
        Cuando lleva `estable_necesario` segundos vivo, da el arranque por bueno
        y cede al guardián normal. Corre en su propio hilo.
        """
        threading.Thread(
            target=self._vigilar_arranque_loop,
            args=(log_fn, ventana, intervalo, estable_necesario, max_reintentos),
            daemon=True, name="ArranqueWatcher"
        ).start()

    def _vigilar_arranque_loop(self, log_fn, ventana, intervalo, estable_necesario, max_reintentos):
        log = log_fn or self.log
        self._vigilancia_arranque_activa = True
        log("🛡️ [Vigilante reinicio] Vigilando el arranque tras el reinicio automático...")
        try:
            reintentos = 0
            estable_seguidos = 0
            pasos = max(1, ventana // intervalo)

            for _ in range(pasos):
                time.sleep(intervalo)

                # Si el admin tomó el control (stop/restart manual), ceder.
                if self.is_stopping or self.is_restarting:
                    log("ℹ️ [Vigilante reinicio] Operación manual detectada. Vigilancia cedida.")
                    return

                if self._proceso_scum_vivo():
                    estable_seguidos += intervalo
                    if estable_seguidos >= estable_necesario:
                        log("✅ [Vigilante reinicio] Servidor estable tras el reinicio. Todo OK.")
                        return
                    continue

                # --- Proceso caído (o nunca arrancó) dentro de la ventana ---
                estable_seguidos = 0
                reintentos += 1
                if reintentos > max_reintentos:
                    log(f"🚨 [Vigilante reinicio] El servidor no logró arrancar tras "
                        f"{max_reintentos} reintentos. Requiere revisión manual.")
                    return

                log(f"🔴 [Vigilante reinicio] El servidor NO está arriba tras el reinicio "
                    f"(reintento {reintentos}/{max_reintentos}). Volviendo a iniciar...")
                # No pisar un reinicio/auto-update que pudiera estar en curso.
                if self._op_lock.acquire(blocking=False):
                    try:
                        self._arrancar_y_verificar(intentos=1, log=log)
                    finally:
                        self._op_lock.release()
                else:
                    log("⏳ [Vigilante reinicio] Otra operación en curso; reintento pospuesto.")
                    reintentos -= 1   # no gastar un intento por esto

            log("✅ [Vigilante reinicio] Fin de la ventana de vigilancia post-reinicio.")
        finally:
            self._vigilancia_arranque_activa = False


    def reinicio_seguro(self, callback_log, post_stop_callback=None):
        """
        Secuencia de reinicio seguro.

        post_stop_callback (opcional): función sin argumentos que se ejecuta
        DESPUÉS de confirmar que el proceso de SCUM ha muerto completamente
        y ANTES de arrancar el servidor de nuevo. Úsalo para re-aplicar
        configuraciones de perfil, ya que SCUM escribe su propio INI durante
        el shutdown y podría pisar los cambios aplicados previamente.
        """
        # Candado: si ya hay un reinicio/auto-update en curso, NO solapar.
        if not self._op_lock.acquire(blocking=False):
            callback_log("⚠️ [Reinicio] Hay otra operación de servidor en curso "
                         "(reinicio o auto-update). Se omite este reinicio para evitar conflictos.")
            return

        self.is_restarting = True
        try:
            callback_log("🔄 INICIANDO SECUENCIA DE REINICIO...")

            # 1. Apagado LIMPIO (Ctrl+C). detener_servidor ya espera pacientemente
            #    a que SCUM guarde y cierre solo — sin taskkill /F (sin rollback).
            self.detener_servidor()

            # 2. Buffer post-cierre: dejar que SCUM termine de volcar su INI/DB a disco
            #    antes de que nosotros reescribamos el INI.
            callback_log("⏳ Buffer post-cierre (2s)...")
            time.sleep(2)

            # 3. Re-aplicar configuración del panel ANTES de arrancar.
            # SCUM borra MOTD/nombre/contraseña del .ini durante su shutdown; esto
            # garantiza que lo que el usuario configuró en el panel siempre gane.
            if post_stop_callback is not None:
                callback_log("🔧 Re-aplicando configuración de perfil post-stop...")
                try:
                    post_stop_callback()
                except Exception as e:
                    callback_log(f"⚠️ Error en post_stop_callback: {e}")
            self._reaplicar_config_gui(callback_log)

            # 4. Arrancar con verificación + reintento: nunca quedarse offline en
            #    silencio. _arrancar_y_verificar confirma que el proceso se sostiene.
            callback_log("🚀 Iniciando servidor...")
            if not self._arrancar_y_verificar(intentos=2, log=callback_log):
                callback_log("🚨 [Reinicio] El servidor NO arrancó. El guardián seguirá intentándolo.")
        except Exception as e:
            callback_log(f"❌ [Reinicio] Error inesperado: {e}")
        finally:
            self.is_restarting = False
            self._guardian_intento = 0   # el guardián parte limpio tras el reinicio
            self._op_lock.release()

    def _reaplicar_config_gui(self, callback_log=None):
        """
        Lee gui_settings.json y re-escribe en el ServerSettings.ini los valores
        que SCUM suele borrar al cerrarse (MOTD, nombre, contraseña, bienvenida).
        Así el servidor siempre arranca con la config que el usuario definió en el panel.
        """
        log = callback_log or self.log
        try:
            appdata = os.environ.get("ONYX_APPDATA_DIR")
            if appdata:
                settings_path = os.path.join(appdata, "data", "gui_settings.json")
            else:
                settings_path = os.path.join(self.base_dir, "data", "gui_settings.json")

            if not os.path.exists(settings_path):
                return

            with open(settings_path, 'r', encoding='utf-8') as f:
                gui = json.load(f)

            # Mapeo campo_gui → clave_ini
            campos = {
                "name":    "scum.ServerName",
                "motd":    "scum.MessageOfTheDay",
                "welcome": "scum.WelcomeMessage",
                "pass":    "scum.ServerPassword",
            }

            # Sólo incluir campos que tienen valor (o vacío explícito para contraseña/motd)
            datos_a_escribir = {}
            for campo_gui, clave_ini in campos.items():
                if campo_gui in gui:
                    datos_a_escribir[clave_ini] = gui[campo_gui]

            if not datos_a_escribir:
                return

            # Buscar el ServerSettings.ini
            ini_path = os.path.join(
                self.server_install_dir, "SCUM", "Saved", "Config", "WindowsServer", "ServerSettings.ini"
            )
            if not os.path.exists(ini_path):
                return

            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()

            datos_lower = {k.lower(): k for k in datos_a_escribir}
            nuevas_lineas = []
            claves_escritas = set()

            for linea in lineas:
                linea_proc = linea
                limpia = linea.strip()
                if "=" in limpia and not limpia.startswith("["):
                    clave = limpia.split("=", 1)[0].strip()
                    clave_l = clave.lower()
                    if clave in datos_a_escribir:
                        linea_proc = f"{clave}={datos_a_escribir[clave]}\n"
                        claves_escritas.add(clave)
                    elif clave_l in datos_lower:
                        real = datos_lower[clave_l]
                        linea_proc = f"{clave}={datos_a_escribir[real]}\n"
                        claves_escritas.add(real)
                nuevas_lineas.append(linea_proc)

            # Agregar claves que no existían en el .ini
            faltantes = [k for k in datos_a_escribir if k not in claves_escritas]
            if faltantes:
                nuevas_lineas.append("\n")
                for k in faltantes:
                    nuevas_lineas.append(f"{k}={datos_a_escribir[k]}\n")

            with open(ini_path, 'w', encoding='utf-8') as f:
                f.writelines(nuevas_lineas)

            log("✅ [Post-restart] Config del panel re-aplicada al INI (MOTD, nombre, contraseña).")
        except Exception as e:
            if callback_log:
                callback_log(f"⚠️ [Post-restart] No se pudo re-aplicar config: {e}")


    def chequeo_auto_update(self):
        """
        Automatico: Solo actualiza si hay una version nueva en Steam.
        Se ejecuta cada 15 minutos cuando Auto-Update esta activado.
        Usa un lock para evitar ejecuciones simultaneas.
        """
        # Lock para evitar ejecuciones simultaneas

        if getattr(self, '_auto_update_running', False):
            self.log("⚠️ [Auto-Update] Ya hay una verificacion en curso. Saltando.")
            return
        self._auto_update_running = True

        try:
            public_build = None

            # --- Intento 1: API de SteamCMD ---
            try:
                url = f"https://api.steamcmd.net/v1/info/{self.app_id}"
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    # Usar .get() encadenado para evitar KeyError
                    public_build = (
                        data.get('data', {})
                            .get(self.app_id, {})
                            .get('depots', {})
                            .get('branches', {})
                            .get('public', {})
                            .get('buildid')
                    )
                    if public_build:
                        self.log(f"✅ [Auto-Update] API SteamCMD respondio. Build remoto: {public_build}")
                    else:
                        self.log(f"⚠️ [Auto-Update] API SteamCMD respondio pero sin BuildID (codigo {r.status_code}).")
                else:
                    self.log(f"⚠️ [Auto-Update] API SteamCMD respondio con error HTTP {r.status_code}.")
            except Exception as e:
                self.log(f"⚠️ [Auto-Update] API SteamCMD no disponible: {e}")

            if not public_build:
                self.log("⚠️ [Auto-Update] No se pudo obtener el Build ID remoto. Reintentara en 15 min.")
                return

            local  = str(self.local_build_id)
            remote = str(public_build)

            if local == "0":
                self.log("⚠️ [Auto-Update] Build local desconocido (servidor no instalado aun). Saltando.")
                return

            if remote == local:
                self.log(f"✅ [Auto-Update] Servidor al dia (Build {local}). Sin cambios.")
                return

            # Hay actualizacion disponible → vamos a operar el servidor.
            self.log(f"🆕 [Auto-Update] Nueva version detectada: {local} -> {remote}. Iniciando actualizacion...")

            # Candado: no solapar con un reinicio (programado o manual) en curso.
            if not self._op_lock.acquire(blocking=False):
                self.log("⚠️ [Auto-Update] Hay un reinicio en curso. La actualización se reintentará en 15 min.")
                return
            try:
                was_running = self.esta_corriendo()

                if was_running:
                    self.log("🛑 [Auto-Update] Deteniendo servidor para actualizar...")
                    if not self.detener_servidor():
                        self.log("❌ [Auto-Update] No se pudo detener el servidor de forma segura. Actualizacion cancelada.")
                        return

                    # Buffer post-muerte: SCUM escribe su INI al cerrarse
                    self.log("⏳ [Auto-Update] Buffer post-cierre (2s) para que SCUM termine su escritura en disco...")
                    time.sleep(2)

                self.instalar_servidor()

                if was_running:
                    self.log("🚀 [Auto-Update] Reiniciando servidor tras la actualizacion...")
                    # Re-aplicar config del panel (MOTD/nombre/contraseña) que SCUM
                    # pudo pisar, y arrancar con verificación para garantizar que vuelve.
                    self._reaplicar_config_gui(self.log)
                    self._arrancar_y_verificar(intentos=2, log=self.log)
            finally:
                self._op_lock.release()

        except requests.exceptions.Timeout:
            self.log("⚠️ [Auto-Update] Tiempo de espera agotado al contactar la API de Steam. Reintentara en 15 min.")
        except requests.exceptions.ConnectionError:
            self.log("⚠️ [Auto-Update] Sin conexion a internet. Reintentara en 15 min.")
        except Exception as e:
            self.log(f"❌ [Auto-Update] Error inesperado: {e}")
        finally:
            self._auto_update_running = False