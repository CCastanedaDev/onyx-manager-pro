import json
import os

class LanguageManager:
    def __init__(self, lang_code="es"):
        self.current_lang = lang_code
        self.dictionary = {}
        self.load_language(lang_code)

    def load_language(self, lang_code):
        """Carga el archivo JSON del idioma seleccionado"""
        self.current_lang = lang_code
        
        # Buscamos en la carpeta data/lang
        # Subimos dos niveles desde src/logic/ para llegar a la raíz y luego a data
        base_dir = os.getcwd()
        file_path = os.path.join(base_dir, "data", "lang", f"{lang_code}.json")
        
        # Si no existe, intentamos cargar español por defecto
        if not os.path.exists(file_path):
            print(f"⚠️ Idioma {lang_code} no encontrado. Cargando español por defecto.")
            file_path = os.path.join(base_dir, "data", "lang", "es.json")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.dictionary = json.load(f)
        except Exception as e:
            print(f"❌ Error crítico cargando idioma: {e}")
            self.dictionary = {}

    def get(self, key):
        """Devuelve la traducción o la clave si no existe"""
        return self.dictionary.get(key, f"[{key}]")