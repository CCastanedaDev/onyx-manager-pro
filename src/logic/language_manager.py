import json
import os
import sys

class LanguageManager:
    def __init__(self, lang_code="es"):
        self.current_lang = lang_code
        self.dictionary = {}
        self.load_language(lang_code)

    def get_resource_path(self, relative_path):
        """
        Resuelve rutas de recursos.
        - En onefile (.exe): lee idiomas desde _MEIPASS (bundle interno)
        - En onedir (.exe): lee desde carpeta junto al exe
        - En desarrollo: lee desde CWD
        """
        # Primero intentar APPDATA si está definido (config del usuario)
        appdata = os.environ.get("ONYX_APPDATA_DIR")
        if appdata:
            appdata_path = os.path.join(appdata, relative_path)
            if os.path.exists(appdata_path):
                return appdata_path

        # Luego desde el bundle (onefile) o junto al exe (onedir)
        if getattr(sys, 'frozen', False):
            # Onefile: _MEIPASS tiene los assets empaquetados
            if hasattr(sys, '_MEIPASS'):
                meipass_path = os.path.join(sys._MEIPASS, relative_path)
                if os.path.exists(meipass_path):
                    return meipass_path
            # Onedir: junto al ejecutable
            exe_path = os.path.join(os.path.dirname(sys.executable), relative_path)
            if os.path.exists(exe_path):
                return exe_path

        # Desarrollo: CWD
        return os.path.join(os.getcwd(), relative_path)

    def load_language(self, lang_code):
        self.current_lang = lang_code
        base_path = self.get_resource_path(os.path.join("data", "lang"))
        file_path = os.path.join(base_path, f"{lang_code}.json")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)
        except Exception as e:
            print(f"Error cargando idioma {lang_code}: {e}")
            self.dictionary = {}

    def get(self, key):
        return self.dictionary.get(key, f"[{key}]")