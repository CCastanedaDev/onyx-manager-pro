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
        Esta función mágica encuentra los archivos tanto si corres
        en Python normal como si es un .EXE compilado.
        """
        if getattr(sys, 'frozen', False):
            # Estamos en modo .EXE (onedir), buscar junto al ejecutable
            base_path = os.path.dirname(sys.executable)
            return os.path.join(base_path, relative_path)
        
        # Estamos en modo normal, buscar en la carpeta actual
        return os.path.join(os.getcwd(), relative_path)

    def load_language(self, lang_code):
        self.current_lang = lang_code
        
        # Usamos la función mágica para encontrar la carpeta data/lang
        # dentro del empaquetado
        base_path = self.get_resource_path(os.path.join("data", "lang"))
        file_path = os.path.join(base_path, f"{lang_code}.json")
        
        # Debug log
        try:
            log_path = r"C:\Users\Public\debug_lang.txt"
            with open(log_path, "w") as log:
                log.write(f"--- Loading Language: {lang_code} ---\n")
                log.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
                log.write(f"Executable: {sys.executable}\n")
                log.write(f"CWD: {os.getcwd()}\n")
                log.write(f"Base Path: {base_path}\n")
                log.write(f"File Path: {file_path}\n")
                log.write(f"Exists: {os.path.exists(file_path)}\n")
        except Exception as e:
            pass

        # Si no lo encuentra ahí, intento de respaldo en la carpeta local (por si acaso)
        if not os.path.exists(file_path):
             file_path = os.path.join(os.getcwd(), "data", "lang", f"{lang_code}.json")
             try:
                 with open(log_path, "a") as log:
                     log.write(f"Fallback Path: {file_path}\n")
                     log.write(f"Fallback Exists: {os.path.exists(file_path)}\n")
             except: pass

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)
                try:
                    with open(log_path, "a") as log: log.write("Loaded successfully.\n")
                except: pass
        except Exception as e:
            print(f"❌ Error cargando idioma {lang_code}: {e}")
            try:
                with open(log_path, "a") as log: log.write(f"Error: {e}\n")
            except: pass
            self.dictionary = {}

    def get(self, key):
        return self.dictionary.get(key, f"[{key}]")