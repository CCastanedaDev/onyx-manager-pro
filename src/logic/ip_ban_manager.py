"""
ip_ban_manager.py - Deteccion automatica de cuentas alternativas por IP duplicada.

LOGICA CORRECTA:
  - Cuando el jugador B conecta desde la misma IP que el jugador A (ya registrado),
    B se considera una alt account y se banea automaticamente.
  - Excepcion: si la IP esta en la whitelist (familia/misma casa), no se banea.

Registro persistente en: data/ip_registry.json
  { "SteamID64": { "ips": ["1.2.3.4", ...], "nombre": "...", "ultimo_join": "..." }, ... }

Whitelist de IPs: data/ip_whitelist.json
  ["1.2.3.4", "5.6.7.8"]

Al iniciar, escanea automaticamente todos los logs historicos de SCUM para poblar
el registro con todos los jugadores que alguna vez se conectaron.
"""

import json
import os
import re
import threading
from datetime import datetime


class IPBanManager:

    # Patron principal: SteamID + IP en la misma linea del log de SCUM
    # Ej: Begin auth session for user '76561198318834898' (191.253.18.92:51810)
    _RE_AUTH = re.compile(
        r"ProcessAuthenticateUserRequest.*Begin auth session for user '(\d{17})'\s*\(([^)]+)\)",
        re.IGNORECASE
    )
    # BattlEye: "Player #N nombre (IP:PORT) connected"
    _RE_BE_CONN = re.compile(
        r'LogBattlEye: Display: Player #(\d+) (.+?) \((\d+\.\d+\.\d+\.\d+):[^)]+\) connected',
        re.IGNORECASE
    )
    # BattlEye: "Player N SteamID (assumed): STEAMID"
    _RE_BE_STEAM = re.compile(
        r'LogBattlEye: Display: Player (\d+) SteamID \(assumed\): (\d{17})',
        re.IGNORECASE
    )

    def __init__(self, log_callback, appdata_dir=None):
        self.log = log_callback
        self._lock = threading.Lock()

        base = appdata_dir or os.environ.get("ONYX_APPDATA_DIR") or os.getcwd()
        data_dir = os.path.join(base, "data")
        os.makedirs(data_dir, exist_ok=True)

        self.registry_file  = os.path.join(data_dir, "ip_registry.json")
        self.whitelist_file = os.path.join(data_dir, "ip_whitelist.json")

        self.registry     = self._cargar(self.registry_file, {})
        self.ip_whitelist = self._cargar(self.whitelist_file, [])

        # Historial en memoria de detecciones (ultimas 50)
        self.detecciones: list[dict] = []

    # -------------------------------------------------------------------------
    # Carga / guardado
    # -------------------------------------------------------------------------

    def _cargar(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def _guardar_registry(self):
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"⚠️ [IPBan] Error guardando registro: {e}")

    def _guardar_whitelist(self):
        try:
            with open(self.whitelist_file, 'w', encoding='utf-8') as f:
                json.dump(self.ip_whitelist, f, indent=2)
        except Exception as e:
            self.log(f"⚠️ [IPBan] Error guardando whitelist: {e}")

    # -------------------------------------------------------------------------
    # Escaneo historico de logs (se ejecuta al iniciar)
    # -------------------------------------------------------------------------

    def escanear_logs_historicos(self, server_base_path: str):
        """
        Lee TODOS los archivos .log del servidor y popula el registro
        SteamID->IP para todos los jugadores que alguna vez conectaron.
        Corre en background para no bloquear la UI.
        """
        threading.Thread(
            target=self._escanear_hilo, args=(server_base_path,), daemon=True
        ).start()

    def _escanear_hilo(self, server_base_path: str):
        log_dir = os.path.join(server_base_path, "SCUM", "Saved", "Logs")
        if not os.path.isdir(log_dir):
            self.log(f"⚠️ [IPBan] No se encontro directorio de logs: {log_dir}")
            return

        archivos = sorted([
            os.path.join(log_dir, f)
            for f in os.listdir(log_dir) if f.endswith(".log")
        ])

        total_nuevas_ips = 0
        be_pending: dict[str, dict] = {}  # num_jugador -> {nombre, ip}

        for ruta_log in archivos:
            try:
                with open(ruta_log, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        # -- Patron principal: SteamID + IP en 1 sola linea --
                        m = self._RE_AUTH.search(line)
                        if m:
                            sid = m.group(1)
                            ip  = m.group(2).split(":")[0]
                            total_nuevas_ips += self._registrar_interno(sid, ip, "")
                            continue

                        # -- BattlEye: 2 lineas correlacionadas --
                        mb = self._RE_BE_CONN.search(line)
                        if mb:
                            num    = mb.group(1)
                            nombre = mb.group(2).strip()
                            ip     = mb.group(3)
                            be_pending[num] = {"nombre": nombre, "ip": ip}
                            continue

                        ms = self._RE_BE_STEAM.search(line)
                        if ms:
                            num = ms.group(1)
                            sid = ms.group(2)
                            if num in be_pending:
                                p = be_pending.pop(num)
                                total_nuevas_ips += self._registrar_interno(
                                    sid, p["ip"], p["nombre"]
                                )
            except Exception:
                pass

        self._guardar_registry()
        self.log(
            f"📋 [IPBan] Escaneo de historial completado: "
            f"{len(self.registry)} jugadores · {total_nuevas_ips} IPs nuevas registradas."
        )

    def _registrar_interno(self, steam_id: str, ip: str, nombre: str) -> int:
        """Registra sin guardar a disco (para escaneo masivo). Retorna 1 si IP era nueva."""
        if not steam_id or not ip:
            return 0
        with self._lock:
            if steam_id not in self.registry:
                self.registry[steam_id] = {"ips": [], "nombre": nombre, "ultimo_join": ""}
            entry = self.registry[steam_id]
            if nombre and not entry.get("nombre"):
                entry["nombre"] = nombre
            if ip not in entry["ips"]:
                entry["ips"].append(ip)
                return 1
        return 0

    # -------------------------------------------------------------------------
    # API principal — deteccion en tiempo real
    # -------------------------------------------------------------------------

    def registrar_conexion(self, steam_id: str, ip: str, nombre: str = ""):
        """Guarda la relacion SteamID -> IP y actualiza timestamp."""
        steam_id = str(steam_id).strip()
        ip_base  = ip.split(":")[0].strip()
        if not steam_id or not ip_base:
            return
        with self._lock:
            if steam_id not in self.registry:
                self.registry[steam_id] = {"ips": [], "nombre": nombre, "ultimo_join": ""}
            entry = self.registry[steam_id]
            if nombre:
                entry["nombre"] = nombre
            entry["ultimo_join"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if ip_base not in entry["ips"]:
                entry["ips"].append(ip_base)
        self._guardar_registry()

    def buscar_duplicados_ip(self, steam_id_nuevo: str, ip: str) -> list[dict]:
        """
        LOGICA PRINCIPAL: cuando steam_id_nuevo conecta desde 'ip',
        busca si alguna OTRA cuenta ya uso esa misma IP.

        Si la IP esta en whitelist → retorna [] (no hay deteccion).
        Si el jugador ya esta registrado con esa IP → es su propia reconexion → [].
        Si hay otro SteamID con esa misma IP → es una alt account → retorna conflictos.

        El llamador decide si banear o solo alertar segun el switch Auto-Ban.
        """
        ip_base = ip.split(":")[0].strip()

        # IP en whitelist = familia/misma casa → ignorar
        if ip_base in self.ip_whitelist:
            return []

        conflictos = []
        with self._lock:
            for sid, data in self.registry.items():
                if sid == steam_id_nuevo:
                    continue  # es la misma cuenta reconectando
                if ip_base in data.get("ips", []):
                    conflictos.append({
                        "steam_id_original": sid,
                        "nombre_original": data.get("nombre", "?"),
                        "ip": ip_base,
                    })
        return conflictos

    def registrar_deteccion(self, steam_id_nuevo: str, nombre_nuevo: str,
                             ip: str, conflictos: list[dict]):
        """Guarda la deteccion en el historial en memoria."""
        for c in conflictos:
            entry = {
                "ts":                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "steam_id_nuevo":    steam_id_nuevo,
                "nombre_nuevo":      nombre_nuevo or "?",
                "steam_id_original": c["steam_id_original"],
                "nombre_original":   c.get("nombre_original", "?"),
                "ip":                ip.split(":")[0],
            }
            self.detecciones.insert(0, entry)
        self.detecciones = self.detecciones[:50]

    # -------------------------------------------------------------------------
    # Whitelist de IPs (misma casa / familia)
    # -------------------------------------------------------------------------

    def agregar_ip_whitelist(self, ip: str):
        ip_base = ip.split(":")[0].strip()
        if ip_base and ip_base not in self.ip_whitelist:
            self.ip_whitelist.append(ip_base)
            self._guardar_whitelist()
            self.log(f"✅ [IPBan] IP {ip_base} agregada a whitelist (no se auto-baneara).")

    def quitar_ip_whitelist(self, ip: str):
        ip_base = ip.split(":")[0].strip()
        if ip_base in self.ip_whitelist:
            self.ip_whitelist.remove(ip_base)
            self._guardar_whitelist()
            self.log(f"🗑️ [IPBan] IP {ip_base} eliminada de whitelist.")

    # -------------------------------------------------------------------------
    # Utilidades
    # -------------------------------------------------------------------------

    def get_stats(self) -> dict:
        with self._lock:
            total_jugadores = len(self.registry)
            total_ips = sum(len(v.get("ips", [])) for v in self.registry.values())
        return {
            "jugadores":             total_jugadores,
            "ips_registradas":       total_ips,
            "detecciones_recientes": len(self.detecciones),
            "ips_whitelist":         len(self.ip_whitelist),
        }

    def get_ips_de_jugador(self, steam_id: str) -> list[str]:
        with self._lock:
            return list(self.registry.get(steam_id, {}).get("ips", []))

    def limpiar_registro(self):
        with self._lock:
            self.registry   = {}
            self.detecciones = []
        self._guardar_registry()
        self.log("🗑️ [IPBan] Registro de IPs limpiado.")

    def get_detecciones(self) -> list[dict]:
        return list(self.detecciones)
