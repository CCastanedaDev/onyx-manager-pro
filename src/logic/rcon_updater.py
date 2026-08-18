import os
import re
import urllib.request
import zipfile
import tempfile
import shutil

class RCONUpdater:
    def __init__(self, server_dir: str, log_fn=None):
        self.server_dir = server_dir
        self.bin_dir = os.path.join(server_dir, "SCUM", "Binaries", "Win64")
        self.log = log_fn or print
        
    def obtener_version_local(self) -> str:
        """Lee la versión instalada de RCON desde el log rcon_proxy.log."""
        log_path = os.path.join(self.bin_dir, "rcon_proxy.log")
        if not os.path.exists(log_path):
            return "0.0.0"
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
                # Ejemplo: [2026-06-23 12:00:21] [INFO] === SCUM RCON Proxy v6.11.0 ===
                match = re.search(r"Proxy v(\d+\.\d+\.\d+)", first_line)
                if match:
                    return match.group(1)
        except Exception as e:
            self.log(f"⚠️ [RCON Update] Error al leer versión local de RCON: {e}")
        return "0.0.0"

    def obtener_version_remota(self) -> str:
        """Consulta la web de lanzamientos del bot para obtener la versión más reciente."""
        url = "https://theprisonerbot.com/releases"
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                # Buscar patrones de versiones: "6.11.1"
                versions = re.findall(r'"(\d+\.\d+\.\d+)"', html)
                if versions:
                    # Convertir a tuplas numéricas para ordenar correctamente
                    def parse_v(v_str):
                        return tuple(map(int, v_str.split('.')))
                    sorted_versions = sorted(versions, key=parse_v, reverse=True)
                    return sorted_versions[0]
        except Exception as e:
            self.log(f"⚠️ [RCON Update] No se pudo verificar la versión online de RCON: {e}")
        return "0.0.0"

    def descargar_y_preparar(self, download_url: str) -> bool:
        """
        Descarga el .zip de actualización y lo descomprime en una carpeta temporal,
        ignorando/eliminando archivos .ini para no pisar credenciales.
        """
        if not download_url:
            self.log("❌ [RCON Update] No se ha configurado la URL de descarga del RCON.")
            return False
            
        temp_dir = os.path.join(self.bin_dir, "rcon_update_temp")
        if os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except: pass
        os.makedirs(temp_dir, exist_ok=True)
        
        zip_path = os.path.join(temp_dir, "update.zip")
        self.log(f"📥 [RCON Update] Descargando actualización desde: {download_url}...")
        try:
            req = urllib.request.Request(
                download_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(zip_path, "wb") as f:
                    f.write(response.read())
            self.log("✅ [RCON Update] Descarga completada. Descomprimiendo y filtrando...")
            
            # Descomprimir y filtrar archivos
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    filename = file_info.filename
                    # Evitar carpetas padre o archivos INI
                    if filename.endswith('.ini') or 'example.ini' in filename or 'rcon_proxy.ini' in filename:
                        self.log(f"🛡️ [RCON Update] Ignorado archivo de configuración: {filename}")
                        continue
                    
                    # Extraer solo archivos válidos (binarios, logs, etc.)
                    zip_ref.extract(file_info, temp_dir)
            
            # Borrar el ZIP para limpiar espacio
            try: os.remove(zip_path)
            except: pass
            
            self.log("✅ [RCON Update] Archivos de actualización preparados y limpios de configuraciones.")
            return True
            
        except Exception as e:
            self.log(f"❌ [RCON Update] Falló la preparación de la actualización: {e}")
            try: shutil.rmtree(temp_dir)
            except: pass
            return False

    def aplicar_actualizacion(self) -> bool:
        """
        Copia los archivos filtrados de la carpeta temporal a la carpeta oficial de binarios.
        Debe ejecutarse cuando el servidor está APAGADO.
        """
        temp_dir = os.path.join(self.bin_dir, "rcon_update_temp")
        if not os.path.exists(temp_dir):
            return False
            
        self.log("🔧 [RCON Update] Aplicando archivos de actualización...")
        success = True
        try:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    src_file = os.path.join(root, file)
                    # Determinar ruta destino relativa a win64
                    rel_path = os.path.relpath(src_file, temp_dir)
                    dst_file = os.path.join(self.bin_dir, rel_path)
                    
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    try:
                        shutil.copy2(src_file, dst_file)
                        self.log(f"✅ [RCON Update] Actualizado: {rel_path}")
                    except Exception as copy_err:
                        self.log(f"❌ [RCON Update] Error al copiar {rel_path}: {copy_err}")
                        success = False
            
            # Limpiar carpeta temporal
            try: shutil.rmtree(temp_dir)
            except: pass
            
            if success:
                self.log("🎉 [RCON Update] Actualización del RCON aplicada con éxito.")
            return success
        except Exception as e:
            self.log(f"❌ [RCON Update] Error crítico al aplicar actualización: {e}")
            return False
