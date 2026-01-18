import os
import json
import datetime
from datetime import timedelta
from src.logic.path_manager import find_server_directory

class UserManager:
    def __init__(self, log_callback):
        self.log = log_callback
        self.base_dir = os.getcwd()
        self.users_db_file = os.path.join("data", "users_db.json")
        
        # Rutas a los archivos reales del servidor
        server_dir = find_server_directory(self.base_dir)
        self.config_dir = os.path.join(server_dir, "SCUM", "Saved", "Config", "WindowsServer")
        self.ban_file = os.path.join(self.config_dir, "Ban.txt")
        self.whitelist_file = os.path.join(self.config_dir, "Whitelist.txt")
        
        # Cargar base de datos de tiempos
        self.db = self.cargar_db()
        
        # Sincronizar con archivos existentes (Importar bans/whitelist viejos)
        self.sincronizar_con_archivos()

    def sincronizar_con_archivos(self):
        """Lee Ban.txt y Whitelist.txt y sincroniza la DB interna (altas y bajas)"""
        self.sincronizar_tipo_desde_txt("BAN", self.ban_file)
        self.sincronizar_tipo_desde_txt("VIP", self.whitelist_file)

    def sincronizar_tipo_desde_txt(self, tipo, archivo):
        if not os.path.exists(archivo): 
            return
        
        try:
            with open(archivo, 'r') as f:
                ids_en_archivo = [l.strip() for l in f.readlines() if l.strip()]
                
            cambios = False
            
            # 1. Importar IDs que están en el archivo pero no en la DB
            for steam_id in ids_en_archivo:
                existe = any(u["id"] == steam_id and u["tipo"] == tipo for u in self.db)
                if not existe:
                    self.log(f"📥 [SYNC] Detectada alta externa en {tipo}: {steam_id}")
                    self.db.append({
                        "id": steam_id,
                        "tipo": tipo,
                        "expira": "PERMANENTE",
                        "notas": "Sincronizado desde archivo"
                    })
                    cambios = True
            
            # 2. Eliminar IDs de la DB que ya no están en el archivo (Borrado manual externo)
            db_nueva = []
            for u in self.db:
                if u["tipo"] == tipo:
                    if u["id"] in ids_en_archivo:
                        db_nueva.append(u)
                    else:
                        self.log(f"🗑 [SYNC] Detectada baja externa en {tipo}: {u['id']}")
                        cambios = True
                else:
                    db_nueva.append(u)
            
            self.db = db_nueva
            
            if cambios: 
                self.guardar_db()
        except Exception as e:
            self.log(f"❌ Error sincronizando {tipo}: {e}")

    def agregar_usuario(self, tipo, steam_id, duracion_horas, notas=""):
        """
        tipo: 'BAN' o 'VIP'
        duracion_horas: int (Si es -1 es permanente)
        """
        fecha_expiracion = "PERMANENTE"
        if duracion_horas > 0:
            exp = datetime.datetime.now() + timedelta(hours=duracion_horas)
            fecha_expiracion = exp.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Agregar a la base de datos interna (para el timer)
        nuevo_registro = {
            "id": steam_id,
            "tipo": tipo,
            "expira": fecha_expiracion,
            "notas": notas
        }
        
        # Evitar duplicados
        self.db = [u for u in self.db if u["id"] != steam_id or u["tipo"] != tipo]
        self.db.append(nuevo_registro)
        self.guardar_db()
        
        # 2. Escribir en el archivo real del juego (.txt)
        self.escribir_txt(tipo, steam_id, accion="ADD")
        
        tipo_str = "BANEADO" if tipo == "BAN" else "WHITELIST/VIP"
        duracion_str = "Indefinido" if duracion_horas == -1 else f"{duracion_horas} horas"
        self.log(f"👤 {tipo_str}: {steam_id} ({duracion_str}) - {notas}")

    def remover_usuario(self, tipo, steam_id):
        # 1. Quitar de la DB
        self.db = [u for u in self.db if not (u["id"] == steam_id and u["tipo"] == tipo)]
        self.guardar_db()
        
        # 2. Quitar del archivo real
        self.escribir_txt(tipo, steam_id, accion="REMOVE")
        self.log(f"🗑 Usuario removido de {tipo}: {steam_id}")

    def revisar_expiraciones(self):
        """Revisa si algún VIP o BAN ha caducado"""
        ahora = datetime.datetime.now()
        eliminados = []
        
        for usuario in self.db:
            if usuario["expira"] != "PERMANENTE":
                fecha_fin = datetime.datetime.strptime(usuario["expira"], "%Y-%m-%d %H:%M:%S")
                if ahora >= fecha_fin:
                    # HA EXPIRADO
                    eliminados.append(usuario)
        
        for u in eliminados:
            self.log(f"⏰ TIEMPO CUMPLIDO: Removiendo {u['tipo']} a {u['id']}")
            self.remover_usuario(u['tipo'], u['id'])

    def escribir_txt(self, tipo, steam_id, accion):
        """Manipula los archivos de texto de SCUM"""
        archivo = self.ban_file if tipo == "BAN" else self.whitelist_file
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(archivo), exist_ok=True)
        if not os.path.exists(archivo):
            with open(archivo, 'w') as f: pass

        # Leer contenido actual
        with open(archivo, 'r') as f:
            lineas = [l.strip() for l in f.readlines() if l.strip()]

        if accion == "ADD":
            if steam_id not in lineas:
                lineas.append(steam_id)
        elif accion == "REMOVE":
            if steam_id in lineas:
                lineas.remove(steam_id)

        # Guardar
        with open(archivo, 'w') as f:
            f.write("\n".join(lineas))

    # --- UTILIDADES DB ---
    def cargar_db(self):
        if os.path.exists(self.users_db_file):
            try:
                with open(self.users_db_file, 'r') as f: return json.load(f)
            except: return []
        return []

    def guardar_db(self):
        with open(self.users_db_file, 'w') as f: json.dump(self.db, f, indent=4)