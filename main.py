import customtkinter as ctk
import os
import sys
import shutil
import traceback

# ── Configuración Global de CustomTkinter ─────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ── Directorio de datos del usuario ───────────────────────────────────────────
# %APPDATA%\OnyxManager\   →  config persistente, invisible para el usuario
APPDATA_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "OnyxManager"
)


def get_bundle_dir():
    """Assets de solo lectura: dentro del bundle _MEIPASS (onefile) o carpeta del script."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_exe_dir():
    """Carpeta real del .exe (o del script en desarrollo)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def setup_appdata():
    """
    Crea %APPDATA%\\OnyxManager\\data\\ con la MISMA estructura que el proyecto:
        data/
          gui_settings.json
          profiles.json
          schedule.json
          users_db.json
          lang/
            es.json  en.json  ...

    De esta forma todos los open("data/xxx.json") del código siguen funcionando
    sin cambios: CWD apuntará a APPDATA_DIR y data/ estará dentro.
    """
    data_dir = os.path.join(APPDATA_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)

    bundle = get_bundle_dir()
    bundle_data = os.path.join(bundle, "data")

    # ── Archivos de configuración (escribibles) ────────────────────────────────
    config_files = ["gui_settings.json", "profiles.json", "schedule.json", "users_db.json"]
    for fname in config_files:
        dst = os.path.join(data_dir, fname)
        if not os.path.exists(dst):
            src = os.path.join(bundle_data, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
            else:
                # Crear vacío / default
                defaults = {
                    "gui_settings.json": {
                        "ip": "",
                        "port": "7777",
                        "query": "27015",
                        "name": "My SCUM Server",
                        "welcome": "Welcome!",
                        "motd": "",
                        "pass": "",
                        "players": "64",
                        "auto_update": 0,
                        "lang": "es",
                        "steam_api_key": "",
                        "watchdog_enabled": 0,
                        "nobattleye": 0
                    },
                    "profiles.json": [],
                    "schedule.json": [],
                    "users_db.json": [],
                }
                import json
                with open(dst, "w", encoding="utf-8") as f:
                    json.dump(defaults.get(fname, {}), f, indent=2, ensure_ascii=False)

    # ── Carpeta lang (solo lectura — se copia del bundle una sola vez) ─────────
    lang_dst = os.path.join(data_dir, "lang")
    if not os.path.exists(lang_dst):
        lang_src = os.path.join(bundle_data, "lang")
        if os.path.exists(lang_src):
            shutil.copytree(lang_src, lang_dst)


def set_env_vars():
    """Expone rutas clave como variables de entorno para todos los módulos."""
    os.environ["ONYX_EXE_DIR"]     = get_exe_dir()
    os.environ["ONYX_BUNDLE_DIR"]  = get_bundle_dir()
    os.environ["ONYX_APPDATA_DIR"] = APPDATA_DIR


def main():
    # 1. Preparar datos en AppData (misma estructura que el proyecto)
    setup_appdata()

    # 2. Fijar CWD = AppData → open("data/xxx.json") funciona sin tocar nada más
    os.chdir(APPDATA_DIR)

    # 3. Variables de entorno para steam_handler y otros módulos
    set_env_vars()

    # 4. Lanzar UI
    from src.ui.main_window import VoidWindow
    app = VoidWindow()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        log_path = os.path.join(APPDATA_DIR, "error_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "ONYX MANAGER - Error al iniciar",
                f"El programa encontro un error.\n\nLog en:\n{log_path}"
            )
        except Exception:
            pass
        sys.exit(1)
