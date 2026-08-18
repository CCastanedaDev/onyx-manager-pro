"""
stats_shop.py — Sistema de venta de Atributos y Skills para SCUM Server.

Flujo:
  1. Admin ingresa pack desde UI → se guarda como pendiente en stats_subscriptions.json
  2. En el próximo reinicio programado (post_stop_callback) → se aplica a SCUM.db
  3. Al vencer la suscripción → se programa la restauración para el próximo reinicio
"""

import json
import os
import sqlite3
import shutil
import xml.etree.ElementTree as ET
import time
import tempfile
import contextlib
import sys
from datetime import datetime, timedelta
from typing import Optional

# Reconfigure stdout and stderr to UTF-8 to prevent UnicodeEncodeError on Windows
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

SKILLS_DISPONIBLES = [
    "RiflesSkill", "HandgunSkill", "ShotgunSkill", "SnipingSkill",
    "MeleeWeaponsSkill", "ArcherySkill", "BoxingSkill", "DemolitionSkill",
    "DrivingSkill", "MotorcycleSkill", "AviationSkill",
    "RunningSkill", "EnduranceSkill", "ResistanceSkill",
    "SurvivalSkill", "MedicalSkill", "CookingSkill", "FarmingSkill",
    "EngineeringSkill", "ThieverySkill",
    "AwarenessSkill", "StealthSkill", "CamouflageSkill", "TacticsSkill",
]

ATRIBUTOS_DISPONIBLES = ["Strength", "Constitution", "Dexterity", "Intelligence"]


class StatsShop:
    def __init__(self, db_path: str, data_dir: str, log_fn=None):
        """
        db_path  : ruta completa al SCUM.db del servidor real
        data_dir : carpeta donde guardar stats_subscriptions.json
        log_fn   : función de log (opcional)
        """
        self.db_path = db_path
        self.subs_file = os.path.join(data_dir, "stats_subscriptions.json")
        self.log = log_fn or print
        os.makedirs(data_dir, exist_ok=True)
        self._subs = self._cargar_subs()

    def _check_and_update_cache(self):
        """Verifies if the cached database is up to date, and if not, copies it from Y: drive."""
        temp_dir = tempfile.gettempdir()
        db_path = self.db_path
        wal_path = db_path + "-wal"
        shm_path = db_path + "-shm"

        try:
            if not os.path.exists(db_path):
                return db_path

            # Check if there is already a valid cache file in temp_dir
            now = time.time()
            cache_lifetime = 600
            
            # Find existing cache files on disk
            existing_caches = []
            try:
                for f in os.listdir(temp_dir):
                    if f.startswith("onyx_scum_cache_") and f.endswith(".db"):
                        parts = f.replace("onyx_scum_cache_", "").replace(".db", "").split("_")
                        if parts and parts[0].isdigit():
                            ts = int(parts[0])
                            existing_caches.append((ts, os.path.join(temp_dir, f)))
            except Exception:
                pass
            
            # Sort by timestamp descending (newest first)
            existing_caches.sort(key=lambda x: x[0], reverse=True)
            
            use_existing = False
            cached_db = None
            
            if existing_caches:
                newest_ts, newest_path = existing_caches[0]
                if now - newest_ts < cache_lifetime and os.path.exists(newest_path):
                    use_existing = True
                    cached_db = newest_path
                    self._last_cache_update_time = newest_ts
                    self._current_cached_db = newest_path

            if not use_existing:
                # We will copy to a file named with the current copy timestamp
                new_update_time = int(now)
                cache_id = f"{new_update_time}"
                cached_db = os.path.join(temp_dir, f"onyx_scum_cache_{cache_id}.db")
                cached_wal = cached_db + "-wal"
                cached_shm = cached_db + "-shm"
                
                self.log("⚡ [StatsShop] Cache de base de datos expirado o inexistente. Copiando desde red (esto puede demorar unos segundos)...")
                
                # Copy main DB
                with open(db_path, "rb") as f_src:
                    with open(cached_db, "wb") as f_dst:
                        while True:
                            chunk = f_src.read(65536)
                            if not chunk:
                                break
                            f_dst.write(chunk)

                # Copy WAL
                if os.path.exists(wal_path):
                    try:
                        with open(wal_path, "rb") as f_src:
                            with open(cached_wal, "wb") as f_dst:
                                while True:
                                    chunk = f_src.read(65536)
                                    if not chunk:
                                        break
                                    f_dst.write(chunk)
                    except Exception as e:
                        self.log(f"⚠️ [StatsShop] Error copiando archivo WAL: {e}")

                # Copy SHM
                if os.path.exists(shm_path):
                    try:
                        with open(shm_path, "rb") as f_src:
                            with open(cached_shm, "wb") as f_dst:
                                while True:
                                    chunk = f_src.read(65536)
                                    if not chunk:
                                        break
                                    f_dst.write(chunk)
                    except Exception as e:
                        self.log(f"⚠️ [StatsShop] Error copiando archivo SHM: {e}")

                self.log("✅ [StatsShop] Cache de base de datos actualizado con éxito.")
                
                # Save state
                self._last_cache_update_time = new_update_time
                self._current_cached_db = cached_db
                
                # Clean up older files
                try:
                    for f in os.listdir(temp_dir):
                        if f.startswith("onyx_scum_cache_") and not f.startswith(f"onyx_scum_cache_{cache_id}"):
                            p = os.path.join(temp_dir, f)
                            try: os.remove(p)
                            except: pass
                except Exception:
                    pass
                    
        except Exception as e:
            self.log(f"⚠️ [StatsShop] Error actualizando cache de base de datos: {e}")
            # Fallback if copy failed
            return db_path

        return cached_db

    @contextlib.contextmanager
    def _temp_db_conn(self):
        """Conecta directamente a la base de datos en modo lectura sin bloquear (nolock=1) para evitar lag en el servidor."""
        conn = None
        try:
            db_path = self.db_path
            # Para formato URI de sqlite, las barras invertidas de Windows se deben cambiar a barras normales
            db_path_uri = db_path.replace("\\", "/")
            uri = f"file:{db_path_uri}?mode=ro&nolock=1"
            conn = sqlite3.connect(uri, uri=True)
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # -------------------------------------------------------------------------
    # PERSISTENCIA
    # -------------------------------------------------------------------------

    def _cargar_subs(self):
        if os.path.exists(self.subs_file):
            try:
                with open(self.subs_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _guardar_subs(self):
        with open(self.subs_file, "w", encoding="utf-8") as f:
            json.dump(self._subs, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------------------------------
    # BÚSQUEDA DE JUGADORES
    # -------------------------------------------------------------------------

    def buscar_jugadores(self, query: str) -> list:
        """Busca por SteamID parcial, nombre de Steam, o nombre in-game. Devuelve lista de dicts."""
        results = []
        try:
            with self._temp_db_conn() as con:
                cur = con.cursor()
                q = f"%{query}%"
                cur.execute(
                    """SELECT u.id, u.name, up.id as profile_id, up.prisoner_id, up.fame_points, up.name as ig_name
                       FROM user u
                       JOIN user_profile up ON u.id = up.user_id
                       WHERE u.id LIKE ? OR u.name LIKE ? OR up.name LIKE ?
                       ORDER BY up.last_login_time DESC LIMIT 20""",
                    (q, q, q),
                )
                for row in cur.fetchall():
                    steam_name = row[1]
                    ig_name = row[5]
                    # Mostrar "NombreInGame (NombreSteam)" para mayor claridad
                    display_name = f"{ig_name} ({steam_name})" if ig_name and ig_name != steam_name else (ig_name or steam_name)
                    
                    results.append({
                        "steam_id": row[0],
                        "name": display_name,
                        "profile_id": row[2],
                        "prisoner_id": row[3],
                        "fame": round(row[4] or 0, 1),
                    })
        except Exception as e:
            self.log(f"❌ [StatsShop] Error buscando jugador: {e}")
        return results

    # -------------------------------------------------------------------------
    # LECTURA DE STATS ACTUALES
    # -------------------------------------------------------------------------

    def leer_atributos(self, prisoner_id: int) -> Optional[dict]:
        """Lee Strength/Constitution/Dexterity/Intelligence de body_simulation (con fallback a template_xml)."""
        # 1. Intentar leer desde el BLOB body_simulation
        try:
            with self._temp_db_conn() as con:
                cur = con.cursor()
                cur.execute(
                    "SELECT body_simulation FROM prisoner WHERE user_profile_id = (SELECT id FROM user_profile WHERE prisoner_id = ?)",
                    (prisoner_id,),
                )
                row = cur.fetchone()
            if row and row[0]:
                blob = row[0]
                import struct
                mapping = {
                    "Strength": b"BaseStrength",
                    "Constitution": b"BaseConstitution",
                    "Dexterity": b"BaseDexterity",
                    "Intelligence": b"BaseIntelligence"
                }
                res = {}
                for attr, uprop in mapping.items():
                    idx = blob.find(uprop)
                    if idx != -1:
                        type_str = b"DoubleProperty"
                        type_idx = blob.find(type_str, idx)
                        if type_idx != -1:
                            val_idx = type_idx + len(type_str) + 1 + 8 + 1
                            if val_idx + 8 <= len(blob):
                                double_bytes = blob[val_idx:val_idx+8]
                                res[attr] = struct.unpack("<d", double_bytes)[0]
                if len(res) == 4:
                    return res
        except Exception as e:
            self.log(f"⚠️ [StatsShop] Error leyendo de body_simulation, usando fallback XML: {e}")

        # 2. Fallback XML original
        try:
            with self._temp_db_conn() as con:
                cur = con.cursor()
                cur.execute(
                    "SELECT template_xml FROM user_profile WHERE prisoner_id = ?",
                    (prisoner_id,),
                )
                row = cur.fetchone()
            if not row or not row[0]:
                return None
            xml_str = row[0] if isinstance(row[0], str) else row[0].decode("utf-8")
            root = ET.fromstring(xml_str)
            return {
                attr: float(root.attrib.get(attr, 0.0))
                for attr in ATRIBUTOS_DISPONIBLES
            }
        except Exception as e:
            self.log(f"❌ [StatsShop] Error leyendo atributos: {e}")
            return None

    def leer_skills(self, prisoner_id: int) -> Optional[dict]:
        """Lee todos los skills de prisoner_skill."""
        try:
            with self._temp_db_conn() as con:
                cur = con.cursor()
                cur.execute(
                    "SELECT name, level, experience FROM prisoner_skill WHERE prisoner_id = ?",
                    (prisoner_id,),
                )
                skills = {row[0]: {"level": row[1], "experience": row[2]} for row in cur.fetchall()}
            return skills if skills else None
        except Exception as e:
            self.log(f"❌ [StatsShop] Error leyendo skills: {e}")
            return None

    # -------------------------------------------------------------------------
    # REGISTRAR PACK PENDIENTE
    # -------------------------------------------------------------------------

    def registrar_pack(
        self,
        steam_id: str,
        player_name: str,
        prisoner_id: int,
        dias: int,
        atributos: Optional[dict] = None,
        skills: Optional[dict] = None,
    ) -> bool:
        """
        Guarda un pack como pendiente. Se aplicará en el próximo reinicio.
        atributos: {Strength: 5, Constitution: 4, ...} o None si no se cambian
        skills:    {RiflesSkill: 3, MedicalSkill: 3, ...} o None si no se cambian
        """
        if not atributos and not skills:
            self.log("⚠️ [StatsShop] El pack no tiene atributos ni skills definidos.")
            return False

        # Buscar si ya existe una suscripción activa o pendiente para este jugador
        existing = next((s for s in self._subs if s["steam_id"] == steam_id and s["estado"] in ("activo", "pendiente_aplicar")), None)

        if existing:
            # 1. Conservar los backups originales si ya existen
            backup_attrs = existing.get("backup_atributos")
            backup_skills = existing.get("backup_skills")
            
            # Si no tenía backup de atributos previamente, leerlos ahora
            if not backup_attrs:
                backup_attrs = self.leer_atributos(prisoner_id)
                existing["backup_atributos"] = backup_attrs
            
            # Si no tenía backup de skills, leerlos ahora. Si ya tenía algunos, conservar y opcionalmente combinar nuevos
            if not backup_skills:
                backup_skills = self.leer_skills(prisoner_id)
                existing["backup_skills"] = backup_skills
            elif self.leer_skills(prisoner_id):
                # Combinar backups de skills que falten
                current_skills_in_db = self.leer_skills(prisoner_id)
                if current_skills_in_db:
                    for k, v in current_skills_in_db.items():
                        if k not in backup_skills:
                            backup_skills[k] = v
                    existing["backup_skills"] = backup_skills

            # Si ya estaba activo o si ya se había aplicado, conservar la marca
            if existing.get("estado") == "activo" or existing.get("fue_aplicado"):
                existing["fue_aplicado"] = True

            # 2. Reemplazar atributos nuevos (si se pasan)
            if atributos is not None:
                existing["atributos_nuevos"] = atributos
                
            # 3. Reemplazar skills nuevos (si se pasan)
            if skills is not None:
                existing["skills_nuevos"] = skills

            # 4. Actualizar días y fecha de expiración
            ahora = datetime.now()
            expira = ahora + timedelta(days=dias)
            existing["fecha_expiracion"] = expira.strftime("%Y-%m-%d %H:%M")
            existing["estado"] = "pendiente_aplicar"  # Volver a poner en pendiente para que se aplique en el próximo reinicio
            
            self._guardar_subs()
            self.log(
                f"📋 [StatsShop] Beneficios para {player_name} ({steam_id}) actualizados y fusionados. "
                f"Se aplicarán en el próximo reinicio. Expira: {existing['fecha_expiracion']}"
            )
            return True

        # --- Flujo normal de creación de nueva tarjeta ---
        backup_attrs = self.leer_atributos(prisoner_id)
        backup_skills = self.leer_skills(prisoner_id)

        if backup_attrs is None and backup_skills is None:
            self.log(f"❌ [StatsShop] No se pudo leer el personaje del jugador (prisoner_id={prisoner_id}).")
            return False

        ahora = datetime.now()
        expira = ahora + timedelta(days=dias)

        sub = {
            "steam_id": steam_id,
            "player_name": player_name,
            "prisoner_id": prisoner_id,
            "dias": dias,
            "fecha_compra": ahora.strftime("%Y-%m-%d %H:%M"),
            "fecha_expiracion": expira.strftime("%Y-%m-%d %H:%M"),
            "atributos_nuevos": atributos,
            "skills_nuevos": skills,
            "backup_atributos": backup_attrs,
            "backup_skills": backup_skills,
            "estado": "pendiente_aplicar",  # pendiente_aplicar | activo | pendiente_restaurar | restaurado
        }
        self._subs.append(sub)
        self._guardar_subs()
        self.log(
            f"📋 [StatsShop] Pack registrado para {player_name} ({steam_id}). "
            f"Se aplicará en el próximo reinicio. Expira: {expira.strftime('%Y-%m-%d %H:%M')}"
        )
        return True

    def db_esta_bloqueada(self) -> bool:
        """Retorna True si la base de datos SCUM.db está bloqueada (el servidor está online)."""
        if not os.path.exists(self.db_path):
            return True # Si no existe, consideramos que no está lista para escribir

        # Optimización: si el log del servidor SCUM fue modificado hace menos de 90 segundos,
        # asumimos que el servidor está online sin intentar bloquear la base de datos por red.
        try:
            log_path = os.path.normpath(os.path.join(os.path.dirname(self.db_path), "..", "Logs", "SCUM.log"))
            if os.path.exists(log_path):
                mtime = os.path.getmtime(log_path)
                if time.time() - mtime < 90:
                    return True
        except Exception:
            pass

        con = None
        try:
            # Abrir conexión con timeout corto para no colgar la UI/hilo
            con = sqlite3.connect(self.db_path, timeout=1.0)
            cur = con.cursor()
            # BEGIN IMMEDIATE intenta adquirir un lock de escritura inmediato.
            # Si el servidor SCUM está corriendo y tiene la base de datos bloqueada en modo WAL,
            # esto lanzará sqlite3.OperationalError: database is locked
            cur.execute("BEGIN IMMEDIATE TRANSACTION")
            cur.execute("ROLLBACK")
            return False
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                return True
            return True
        except Exception:
            return True
        finally:
            if con:
                try: con.close()
                except: pass

    # -------------------------------------------------------------------------
    # EJECUTAR PENDIENTES (llamar en post_stop_callback del reinicio)
    # -------------------------------------------------------------------------

    def ejecutar_pendientes(self):
        """
        Aplica todos los packs pendientes y restaura los vencidos.
        Debe llamarse SOLO cuando el servidor está offline (post_stop_callback).
        """
        # Recargar siempre del disco para sincronizar cambios realizados por el panel web o GUI
        self._subs = self._cargar_subs()
        
        pendientes = [s for s in self._subs if s["estado"] in ("pendiente_aplicar", "pendiente_restaurar")]
        if not pendientes:
            return

        if self.db_esta_bloqueada():
            self.log("⚠️ [StatsShop] No se pueden aplicar cambios pendientes: La base de datos está bloqueada (el servidor está online).")
            raise RuntimeError("La base de datos está bloqueada (el servidor está online).")


        self.log(f"🛒 [StatsShop] Procesando {len(pendientes)} operación(es) pendiente(s)...")

        # Hacer backup del SCUM.db antes de cualquier modificación
        self._backup_db()

        for sub in pendientes:
            try:
                if sub["estado"] == "pendiente_aplicar":
                    self._aplicar_pack(sub)
                elif sub["estado"] == "pendiente_restaurar":
                    self._restaurar_pack(sub)
            except Exception as e:
                self.log(f"❌ [StatsShop] Error procesando {sub['player_name']}: {e}")

        self._guardar_subs()

    def _aplicar_pack(self, sub: dict):
        """Aplica los nuevos atributos y/o skills al jugador."""
        pid = sub["prisoner_id"]
        name = sub["player_name"]

        if sub.get("atributos_nuevos"):
            self._escribir_atributos(pid, sub["atributos_nuevos"])
            self.log(f"✅ [StatsShop] Atributos aplicados a {name}: {sub['atributos_nuevos']}")

        if sub.get("skills_nuevos"):
            self._escribir_skills(pid, sub["skills_nuevos"])
            self.log(f"✅ [StatsShop] Skills aplicados a {name}: {list(sub['skills_nuevos'].keys())}")

        sub["estado"] = "activo"
        sub["fue_aplicado"] = True

    def _restaurar_pack(self, sub: dict):
        """Restaura los stats originales al jugador."""
        pid = sub["prisoner_id"]
        name = sub["player_name"]

        if sub.get("backup_atributos"):
            self._escribir_atributos(pid, sub["backup_atributos"])
            self.log(f"🔄 [StatsShop] Atributos restaurados para {name}: {sub['backup_atributos']}")

        if sub.get("backup_skills"):
            # Restaurar solo los skills que fueron modificados
            skills_modificados = sub.get("skills_nuevos") or {}
            skills_a_restaurar = {k: v for k, v in sub["backup_skills"].items() if k in skills_modificados}
            if skills_a_restaurar:
                self._escribir_skills_completos(pid, skills_a_restaurar)
                self.log(f"🔄 [StatsShop] Skills restaurados para {name}")

        sub["estado"] = "restaurado"

    # -------------------------------------------------------------------------
    # VERIFICAR VENCIMIENTOS (llamar diariamente o al ejecutar_pendientes)
    # -------------------------------------------------------------------------

    def verificar_vencimientos(self):
        """
        Detecta suscripciones vencidas y las marca como pendiente_restaurar.
        La restauración se ejecutará en el próximo reinicio.
        """
        # Recargar siempre del disco para sincronizar cambios realizados por el panel web o GUI
        self._subs = self._cargar_subs()
        ahora = datetime.now()
        vencidos = []
        for sub in self._subs:
            if sub["estado"] != "activo":
                continue
            try:
                expira = datetime.strptime(sub["fecha_expiracion"], "%Y-%m-%d %H:%M")
                if ahora >= expira:
                    sub["estado"] = "pendiente_restaurar"
                    vencidos.append(sub["player_name"])
            except Exception:
                pass
        if vencidos:
            self._guardar_subs()
            self.log(f"⚠️ [StatsShop] Suscripciones vencidas: {', '.join(vencidos)}. Se restaurarán en el próximo reinicio.")
        return vencidos

    def revocar_pack(self, steam_id: str, fecha_compra: Optional[str] = None):
        """Revoca manualmente un pack activo (lo marca para restaurar en el próximo reinicio) o lo elimina directamente si aún está pendiente."""
        for i, sub in enumerate(self._subs):
            if sub["steam_id"] == steam_id and (fecha_compra is None or sub["fecha_compra"] == fecha_compra):
                if sub["estado"] == "pendiente_aplicar" and not sub.get("fue_aplicado"):
                    self.log(f"🔴 [StatsShop] Pack pendiente eliminado para {sub['player_name']}.")
                    self._subs.pop(i)
                    self._guardar_subs()
                    return True
                else:
                    sub["estado"] = "pendiente_restaurar"
                    sub["fecha_expiracion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    self._guardar_subs()
                    self.log(f"🔴 [StatsShop] Pack revocado para {sub['player_name']}. Se restaurará en el próximo reinicio.")
                    return True
        return False

    def obtener_subs_activas(self) -> list:
        return [s for s in self._subs if s["estado"] in ("activo", "pendiente_aplicar", "pendiente_restaurar")]

    # -------------------------------------------------------------------------
    # ESCRITURA EN SCUM.db
    # -------------------------------------------------------------------------

    def _escribir_atributos(self, prisoner_id: int, atributos: dict):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        # 1. Modificar XML en user_profile
        cur.execute("SELECT template_xml FROM user_profile WHERE prisoner_id = ?", (prisoner_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            con.close()
            raise ValueError(f"No se encontró template_xml para prisoner_id={prisoner_id}")

        xml_str = row[0] if isinstance(row[0], str) else row[0].decode("utf-8")
        root = ET.fromstring(xml_str)

        for attr, valor in atributos.items():
            if attr in ATRIBUTOS_DISPONIBLES:
                try:
                    f_val = float(valor)
                    root.set(attr, str(f_val))
                except (ValueError, TypeError):
                    root.set(attr, str(valor))

        nuevo_xml = ET.tostring(root, encoding="unicode")
        cur.execute(
            "UPDATE user_profile SET template_xml = ? WHERE prisoner_id = ?",
            (nuevo_xml, prisoner_id),
        )

        # 2. Modificar BLOB en la tabla prisoner (body_simulation)
        cur.execute(
            "SELECT id, body_simulation FROM prisoner WHERE user_profile_id = (SELECT id FROM user_profile WHERE prisoner_id = ?)",
            (prisoner_id,),
        )
        p_row = cur.fetchone()
        if p_row and p_row[1]:
            pid, blob = p_row[0], p_row[1]
            import struct
            
            # Mapear de XML attr a UProperty name
            mapping = {
                "Strength": b"BaseStrength",
                "Constitution": b"BaseConstitution",
                "Dexterity": b"BaseDexterity",
                "Intelligence": b"BaseIntelligence"
            }
            
            modified = False
            for attr, valor in atributos.items():
                uprop = mapping.get(attr)
                if uprop and uprop in blob:
                    try:
                        f_val = float(valor)
                        idx = blob.find(uprop)
                        if idx != -1:
                            type_str = b"DoubleProperty"
                            type_idx = blob.find(type_str, idx)
                            if type_idx != -1:
                                val_idx = type_idx + len(type_str) + 1 + 8 + 1
                                if val_idx + 8 <= len(blob):
                                    new_bytes = struct.pack("<d", f_val)
                                    blob = blob[:val_idx] + new_bytes + blob[val_idx+8:]
                                    modified = True
                    except Exception as e:
                        self.log(f"⚠️ [StatsShop] Error modificando UProperty {attr} en BLOB: {e}")
            
            if modified:
                cur.execute("UPDATE prisoner SET body_simulation = ? WHERE id = ?", (blob, pid))
                self.log(f"💾 [StatsShop] BLOB body_simulation actualizado para el prisionero ID {pid}.")

        con.commit()
        con.close()

    def _escribir_skills(self, prisoner_id: int, skills: dict):
        """Actualiza el level y la experiencia de los skills especificados (no toca los demás) en DB y XML."""
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        
        # 1. Modificar tabla prisoner_skill
        for skill_name, level in skills.items():
            lvl = int(level)
            # Asignar la experiencia mínima requerida para el nivel y evitar demociones por el motor del juego
            xp = 0.0
            if lvl == 1: xp = 10000.0
            elif lvl == 2: xp = 100000.0
            elif lvl == 3: xp = 1000000.0
            elif lvl == 4: xp = 10000000.0
            
            # Capping de SnipingSkill a nivel 3 (Avanzado) en la DB para prevenir el bug de cálculo de distancia de SCUM,
            # pero preservando el XP máximo de 10 Millones correspondiente a Maestro.
            if skill_name == "SnipingSkill" and lvl > 3:
                lvl = 3

            cur.execute(
                "UPDATE prisoner_skill SET level = ?, experience = ? WHERE prisoner_id = ? AND name = ?",
                (lvl, xp, prisoner_id, skill_name),
            )
            if cur.rowcount == 0:
                # El skill no existe para este jugador → insertarlo
                cur.execute(
                    "INSERT INTO prisoner_skill (prisoner_id, name, level, experience, xml) VALUES (?, ?, ?, ?, '')",
                    (prisoner_id, skill_name, lvl, xp),
                )
                
        # 2. Modificar XML en user_profile para mantener coherencia
        try:
            cur.execute("SELECT template_xml FROM user_profile WHERE prisoner_id = ?", (prisoner_id,))
            row = cur.fetchone()
            if row and row[0]:
                xml_str = row[0] if isinstance(row[0], str) else row[0].decode("utf-8")
                root = ET.fromstring(xml_str)
                modified_xml = False
                for skill_name, level in skills.items():
                    lvl = int(level)
                    xp = 0.0
                    if lvl == 1: xp = 10000.0
                    elif lvl == 2: xp = 100000.0
                    elif lvl == 3: xp = 1000000.0
                    elif lvl == 4: xp = 10000000.0
                    
                    if skill_name == "SnipingSkill" and lvl > 3:
                        lvl = 3
                    
                    found = False
                    for skill_el in root.findall("Skill"):
                        if skill_el.attrib.get("ClassName") == skill_name:
                            skill_el.set("Level", str(lvl))
                            skill_el.set("Experience", str(xp))
                            found = True
                            modified_xml = True
                            break
                    if not found:
                        # Crear elemento nuevo si no existía en la plantilla
                        new_el = ET.Element("Skill", Attribute="0", Name="", ClassName=skill_name, Level=str(lvl), Experience=str(xp))
                        root.append(new_el)
                        modified_xml = True
                if modified_xml:
                    nuevo_xml = ET.tostring(root, encoding="unicode")
                    cur.execute("UPDATE user_profile SET template_xml = ? WHERE prisoner_id = ?", (nuevo_xml, prisoner_id))
        except Exception as e:
            self.log(f"⚠️ [StatsShop] Error sincronizando XML de habilidades: {e}")

        con.commit()
        con.close()

    def _escribir_skills_completos(self, prisoner_id: int, skills: dict):
        """Restaura skills con level Y experience originales."""
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        for skill_name, data in skills.items():
            level = data.get("level", 0) if isinstance(data, dict) else data
            xp    = data.get("experience", 0) if isinstance(data, dict) else 0
            cur.execute(
                "UPDATE prisoner_skill SET level = ?, experience = ? WHERE prisoner_id = ? AND name = ?",
                (int(level), float(xp), prisoner_id, skill_name),
            )
        con.commit()
        con.close()

    # -------------------------------------------------------------------------
    # BACKUP DEL SCUM.db
    # -------------------------------------------------------------------------

    def _backup_db(self):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(os.path.dirname(self.subs_file), "db_backups")
            os.makedirs(backup_dir, exist_ok=True)
            dst = os.path.join(backup_dir, f"SCUM_before_stats_{ts}.db")
            shutil.copy2(self.db_path, dst)
            self.log(f"💾 [StatsShop] Backup de SCUM.db creado: {dst}")
        except Exception as e:
            self.log(f"⚠️ [StatsShop] No se pudo crear backup de DB: {e}")
