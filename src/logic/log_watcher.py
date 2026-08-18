"""
log_watcher.py - Monitor de log del servidor SCUM para contar jugadores en tiempo real
                 y detectar IPs de conexión.

SCUM escribe dos líneas clave por conexión:

  Auth:  LogSCUM: UDedicatedServerResponse::ProcessAuthenticateUserRequest:
         Begin auth session for user '76561198XXXXXXXXX' (1.2.3.4:PORT)
         -> Aqui estan el SteamID64 Y la IP juntos. <- USAMOS ESTA.

  Join:  "LogNet: Join request: /Game/...?user=76561198XXXXXXXXX?..."

  Leave: "UChannel::Close: Sending CloseBunch..." / "Client disconnected" / etc.

Este modulo sigue el archivo desde su posicion actual (como 'tail -f') en un
thread daemon y mantiene un contador de jugadores conectados.
"""
import os
import re
import threading
import time


class SCUMLogWatcher:
    """
    Monitorea SCUM.log en tiempo real para detectar joins, desconexiones e IPs.
    Expone player_count (int) actualizado en background.
    Llama a on_player_join(steam_id, ip) en cada conexion detectada.
    """

    # Patron de autenticacion: extrae SteamID64 e IP del auth request
    # Ejemplo: Begin auth session for user '76561198131660898' (177.40.140.222:51662)
    _RE_AUTH = re.compile(
        r"ProcessAuthenticateUserRequest.*Begin auth session for user '(\d{17})'\s*\(([^)]+)\)",
        re.IGNORECASE
    )

    # Fallback: Join request con ?user=SteamID (sin IP, para contador)
    _RE_JOIN = re.compile(r'LogNet: Join request:', re.IGNORECASE)

    # Patron de desconexion
    _RE_LEAVE = re.compile(
        r'(UChannel::Close.*CloseBunch|Client disconnected|'
        r'LogNet: UNetConnection::Close|Connection lost)',
        re.IGNORECASE
    )

    def __init__(self, server_base_path, log_callback=None, on_player_join=None):
        """
        server_base_path : ruta a la carpeta SCUM_Server (raiz del servidor).
        log_callback     : funcion opcional para emitir mensajes de debug.
        on_player_join   : callback(steam_id: str, ip: str) llamado en cada conexion.
        """
        self.log_path = os.path.join(
            server_base_path, "SCUM", "Saved", "Logs", "SCUM.log"
        )
        self._log_cb        = log_callback or (lambda msg: None)
        self.on_player_join = on_player_join
        self.player_count   = 0
        self._running       = False
        self._thread        = None
        self._lock          = threading.Lock()
        # SteamIDs vistos en esta sesion del log (evitar doble conteo)
        self._seen_auth     = set()

    def start(self):
        if self._running:
            return
        self._running = True
        self._seen_auth.clear()
        self._thread = threading.Thread(target=self._tail_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _tail_loop(self):
        """Lee el log desde el final del archivo y lo sigue en tiempo real."""
        wait_count = 0
        while self._running and not os.path.exists(self.log_path):
            if wait_count == 0:
                self._log_cb(f"[LogWatcher] Esperando log del servidor: {self.log_path}")
            wait_count += 1
            time.sleep(5)
            if wait_count > 60:
                self._log_cb("[LogWatcher] Log no encontrado despues de 5 min. Desactivando.")
                return

        if os.path.exists(self.log_path):
            self._log_cb(f"[LogWatcher] Monitoreando: {self.log_path}")

        try:
            file_size = os.path.getsize(self.log_path)
        except OSError:
            file_size = 0

        while self._running:
            try:
                if not os.path.exists(self.log_path):
                    time.sleep(2)
                    with self._lock:
                        self.player_count = 0
                    self._seen_auth.clear()
                    continue

                current_size = os.path.getsize(self.log_path)

                if current_size < file_size:
                    self._log_cb("[LogWatcher] Log rotado. Reseteando contador de jugadores.")
                    file_size = 0
                    with self._lock:
                        self.player_count = 0
                    self._seen_auth.clear()

                if current_size > file_size:
                    with open(self.log_path, 'r', encoding='utf-8', errors='replace') as f:
                        f.seek(file_size)
                        new_data = f.read()
                    file_size = current_size

                    for line in new_data.splitlines():
                        self._process_line(line)

            except Exception as e:
                self._log_cb(f"[LogWatcher] Error: {e}")

            time.sleep(1)

    def _process_line(self, line):
        # -- Autenticacion: SteamID + IP --
        m = self._RE_AUTH.search(line)
        if m:
            steam_id = m.group(1)
            ip_raw   = m.group(2)  # "1.2.3.4:PORT"
            ip       = ip_raw.split(":")[0]

            if steam_id not in self._seen_auth:
                self._seen_auth.add(steam_id)
                with self._lock:
                    self.player_count = max(0, self.player_count + 1)
                if self.on_player_join:
                    try:
                        self.on_player_join(steam_id, ip)
                    except Exception as e:
                        self._log_cb(f"[LogWatcher] Error en on_player_join: {e}")
            return

        # -- Join request sin auth (fallback contador) --
        if self._RE_JOIN.search(line):
            m2 = re.search(r'[?&]user=(\d{17})', line)
            if m2:
                sid = m2.group(1)
                if sid not in self._seen_auth:
                    self._seen_auth.add(sid)
                    with self._lock:
                        self.player_count = max(0, self.player_count + 1)
            else:
                with self._lock:
                    self.player_count = max(0, self.player_count + 1)
            return

        # -- Desconexion --
        if self._RE_LEAVE.search(line):
            with self._lock:
                self.player_count = max(0, self.player_count - 1)

    def get_count(self):
        with self._lock:
            return self.player_count
