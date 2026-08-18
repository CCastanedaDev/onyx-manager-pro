import os
from src.logic.path_manager import find_server_directory

def _resolve_ini_path(base_path):
    """
    Resuelve la ruta de ServerSettings.ini.
    Soporta tres casos:
      1. base_path ya ES la carpeta SCUM_Server (contiene SCUM/ directamente)
      2. base_path contiene una subcarpeta SCUM_Server/
      3. None -> busca en ONYX_EXE_DIR o CWD
    """
    INI_SUBPATH = os.path.join("SCUM", "Saved", "Config", "WindowsServer", "ServerSettings.ini")

    if base_path:
        # Caso 1: base_path es la raiz de SCUM (tiene SCUM/ dentro)
        direct = os.path.join(base_path, INI_SUBPATH)
        if os.path.exists(direct) or os.path.isdir(os.path.join(base_path, "SCUM")):
            return direct

    # Caso 2 y 3: delegar a find_server_directory
    root = base_path or os.environ.get("ONYX_EXE_DIR") or os.getcwd()
    server_dir = find_server_directory(root)
    return os.path.join(server_dir, INI_SUBPATH)


class ConfigEditor:
    def __init__(self, log_callback, base_path=None):
        self.log = log_callback
        self.config_path = _resolve_ini_path(base_path)

    def verificar_archivo(self):
        if not os.path.exists(self.config_path):
            self.log(f"⚠ ADVERTENCIA: No se encontró ServerSettings.ini en: {self.config_path}")
            return False
        return True

    def guardar_configuracion(self, datos_dict):
        """
        Recibe un diccionario con los cambios. Ejemplo:
        {'scum.DisableSentrySpawning': 'True', 'scum.ServerName': 'Nuevo Nombre'}

        Usa matching case-insensitive para maxima compatibilidad con el formato
        del ServerSettings.ini de SCUM.
        """
        self.log(f"   [Editor] Ruta INI activa: {self.config_path}")

        if not self.verificar_archivo():
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()

            # Construir mapa de busqueda case-insensitive:
            # { "scum.disablesentryspawning": "scum.DisableSentrySpawning" }
            datos_lower = {k.lower(): k for k in datos_dict.keys()}

            nuevas_lineas = []
            claves_procesadas = set()

            for linea in lineas:
                linea_procesada = linea
                linea_limpia = linea.strip()

                # Solo procesar lineas con "=" que no sean secciones [...]
                if "=" in linea_limpia and not linea_limpia.startswith("["):
                    clave_actual = linea_limpia.split("=", 1)[0].strip()
                    clave_lower = clave_actual.lower()

                    # Buscar coincidencia exacta primero, luego case-insensitive
                    clave_real = None
                    if clave_actual in datos_dict:
                        clave_real = clave_actual
                    elif clave_lower in datos_lower:
                        clave_real = datos_lower[clave_lower]

                    if clave_real is not None:
                        nuevo_valor = datos_dict[clave_real]
                        linea_procesada = f"{clave_actual}={nuevo_valor}\n"
                        claves_procesadas.add(clave_real)
                        self.log(f"   -> Modificado: {clave_actual} = {nuevo_valor}")

                nuevas_lineas.append(linea_procesada)

            # Escribir de vuelta
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(nuevas_lineas)

                # Agregar claves nuevas que no existian en el archivo
                faltantes = [k for k in datos_dict.keys() if k not in claves_procesadas]
                if faltantes:
                    f.write("\n; --- AJUSTES AGREGADOS POR ONYX ---\n")
                    for k in faltantes:
                        val = datos_dict[k]
                        f.write(f"{k}={val}\n")
                        self.log(f"   -> [+] Agregado nuevo ajuste: {k} = {val}")

            self.log(">> CONFIGURACION ACTUALIZADA.")

        except Exception as e:
            self.log(f"Error guardando configuracion: {e}")

    def cargar_configuracion(self):
        """Lee el archivo y devuelve un diccionario para mostrar en la GUI.
        Las claves se normalizan a lower-case para evitar problemas de case-sensitivity
        (el .ini usa 'scum.servername' pero la GUI busca 'scum.ServerName').
        Devuelve adicionalmente una version con claves originales para escritura.
        """
        datos = {}
        if not self.verificar_archivo(): return datos

        try:
            with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
                for linea in f:
                    if "=" in linea and not linea.strip().startswith("["):
                        partes = linea.strip().split("=", 1)
                        if len(partes) == 2:
                            clave_original = partes[0].strip()
                            valor = partes[1].strip()
                            # Guardar con clave original Y clave lower-case
                            datos[clave_original] = valor
                            datos[clave_original.lower()] = valor
            return datos
        except Exception as e:
            return {}