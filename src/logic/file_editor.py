import os
from src.logic.path_manager import find_server_directory

class ConfigEditor:
    def __init__(self, log_callback, base_path=None):
        self.log = log_callback
        # Ruta construida dinámicamente
        root_dir = base_path if base_path else os.getcwd()
        
        # Usar path dinámico para el servidor
        server_dir = find_server_directory(root_dir)
        
        self.config_path = os.path.join(server_dir, "SCUM", "Saved", "Config", "WindowsServer", "ServerSettings.ini")
        
    def verificar_archivo(self):
        if not os.path.exists(self.config_path):
            self.log("⚠ ADVERTENCIA: No se encontró ServerSettings.ini")
            return False
        return True

    def guardar_configuracion(self, datos_dict):
        """
        Recibe un diccionario con los cambios. Ejemplo:
        {'scum.DisableSentrySpawning': '1', 'scum.ServerName': 'Nuevo Nombre'}
        """
        if not self.verificar_archivo():
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()

            nuevas_lineas = []
            # Lista de claves que ya modificamos para saber cuáles faltan al final
            claves_procesadas = []

            for linea in lineas:
                linea_procesada = linea
                linea_limpia = linea.strip()
                
                # Ignoramos líneas vacías o secciones [General]
                if "=" in linea_limpia and not linea_limpia.startswith("["):
                    clave_actual = linea_limpia.split("=", 1)[0].strip()
                    
                    # Verificamos si esta clave está en nuestro diccionario de cambios
                    if clave_actual in datos_dict:
                        nuevo_valor = datos_dict[clave_actual]
                        # Mantenemos la indentación o formato original si es posible
                        linea_procesada = f"{clave_actual}={nuevo_valor}\n"
                        claves_procesadas.append(clave_actual)
                        self.log(f"   -> Modificado: {clave_actual} = {nuevo_valor}")

                nuevas_lineas.append(linea_procesada)

            # Escribimos de vuelta
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(nuevas_lineas)
                
                # Agregar claves nuevas que no existían en el archivo
                faltantes = [k for k in datos_dict.keys() if k not in claves_procesadas]
                if faltantes:
                    f.write("\n; --- AJUSTES AGREGADOS POR ONYX ---\n")
                    for k in faltantes:
                        val = datos_dict[k]
                        f.write(f"{k}={val}\n")
                        self.log(f"   -> [+] Agregado nuevo ajuste: {k} = {val}")

            self.log(">> ✅ CONFIGURACIÓN ACTUALIZADA.")
            
        except Exception as e:
            self.log(f"❌ Error guardando configuración: {e}")

    def cargar_configuracion(self):
        """Lee el archivo y devuelve un diccionario para mostrar en la GUI"""
        datos = {}
        if not self.verificar_archivo(): return datos

        try:
            with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
                for linea in f:
                    if "=" in linea and not linea.strip().startswith("["):
                        partes = linea.strip().split("=", 1)
                        if len(partes) == 2:
                            datos[partes[0].strip()] = partes[1].strip()
            return datos
        except Exception as e:
            return {}