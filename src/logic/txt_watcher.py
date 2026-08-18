"""
txt_watcher.py
--------------
Observa Ban.txt y Whitelist.txt en tiempo real usando la librería `watchdog`.
Cuando detecta un cambio (creación, modificación, o eliminación), llama al
`callback` de forma thread-safe a través de `after_fn` (el método `after()`
de Tkinter), para que la UI pueda refrescar sus listas sin race conditions.

Uso típico:
    from src.logic.txt_watcher import TxtWatcher

    self.txt_watcher = TxtWatcher(
        watch_dir   = self.users.config_dir,   # directorio que contiene Ban.txt / Whitelist.txt
        after_fn    = self.after,              # Tkinter's self.after
        callback    = self.accion_sincronizar_usuarios,
        log_fn      = self.log_sistema,
    )
    self.txt_watcher.start()

    # Al cerrar la app:
    self.txt_watcher.stop()
"""

import os
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


# Archivos que nos interesan (nombres en minusculas para comparar)
# SCUM usa BannedUsers.ini y WhitelistedUsers.ini
WATCHED_FILES = {"bannedusers.ini", "whitelistedusers.ini"}

# Tiempo mínimo entre dos refrescos consecutivos (segundos).
# SCUM puede disparar varios eventos seguidos al guardar — el debounce
# los agrupa en una sola llamada.
DEBOUNCE_SECONDS = 1.0


class _Handler(FileSystemEventHandler):
    """Handler interno: filtra sólo los archivos de interés y aplica debounce."""

    def __init__(self, after_fn, callback, log_fn):
        super().__init__()
        self._after_fn  = after_fn
        self._callback  = callback
        self._log       = log_fn
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    # watchdog llama a estos métodos desde su hilo interno
    def on_modified(self, event):
        self._handle(event)

    def on_created(self, event):
        self._handle(event)

    def on_deleted(self, event):
        self._handle(event)

    def _handle(self, event):
        if event.is_directory:
            return
        fname = os.path.basename(event.src_path).lower()
        if fname not in WATCHED_FILES:
            return
        self._log(f"👁 [TxtWatcher] Cambio detectado en: {os.path.basename(event.src_path)}")
        self._debounce()

    def _debounce(self):
        """Cancela el timer anterior y programa uno nuevo."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._dispatch)
            self._timer.daemon = True
            self._timer.start()

    def _dispatch(self):
        """Ejecuta el callback en el hilo de Tkinter."""
        try:
            # after(0, fn) encola fn en el event-loop de Tkinter → 100% thread-safe
            self._after_fn(0, self._callback)
        except Exception:
            pass


class TxtWatcher:
    """
    Watcher de alto nivel. Encapsula Observer + Handler y expone start/stop.
    Es seguro llamar a stop() aunque start() no haya sido invocado.
    """

    def __init__(self, watch_dir: str, after_fn, callback, log_fn=None):
        """
        Parámetros
        ----------
        watch_dir : str
            Directorio donde viven Ban.txt y Whitelist.txt.
        after_fn  : callable
            self.after de la ventana Tkinter.
        callback  : callable
            Función sin argumentos que se llama cuando un archivo cambia.
            Se ejecuta en el hilo principal de Tkinter.
        log_fn    : callable | None
            Función de log (optional). Recibe un str.
        """
        self._watch_dir = watch_dir
        self._after_fn  = after_fn
        self._callback  = callback
        self._log       = log_fn or (lambda msg: None)
        self._observer: Observer | None = None
        self._started   = False

    def start(self):
        if not WATCHDOG_AVAILABLE:
            self._log("⚠️ [TxtWatcher] Librería 'watchdog' no instalada. "
                      "Ejecuta: pip install watchdog")
            return

        if not os.path.isdir(self._watch_dir):
            self._log(f"⚠️ [TxtWatcher] Directorio no existe aún: {self._watch_dir}. "
                      "El watcher se activará cuando el servidor sea instalado.")
            return

        handler = _Handler(self._after_fn, self._callback, self._log)
        self._observer = Observer()
        self._observer.schedule(handler, self._watch_dir, recursive=False)
        self._observer.start()
        self._started = True
        self._log(f"✅ [TxtWatcher] Monitoreando: {self._watch_dir}")

    def stop(self):
        if self._observer and self._started:
            try:
                self._observer.stop()
                self._observer.join(timeout=3)
            except Exception:
                pass
            self._started = False
            self._log("🛑 [TxtWatcher] Detenido.")
