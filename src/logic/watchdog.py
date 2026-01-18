import requests
import threading
import time

class SteamWatchdog:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.cache = {}  # {steam_id: {"banned": bool, "timestamp": float}}
        self.cache_ttl = 3600  # 1 hora de caché
        self.lock = threading.Lock()

    def set_api_key(self, key):
        self.api_key = key

    def check_player(self, steam_id, whitelist_checker=None):
        """
        Verifica si un jugador tiene VAC o Game Bans.
        Retorna True si debe ser baneado, False si está limpio o es VIP/Admin.
        """
        if not self.api_key:
            return False  # Fail-open: Si no hay key, dejar pasar

        # 1. Verificar Whitelist (Admin/VIP)
        if whitelist_checker and whitelist_checker(steam_id):
            return False  # Es amigo, no tocar

        # 2. Verificar Caché
        with self.lock:
            if steam_id in self.cache:
                data = self.cache[steam_id]
                if time.time() - data["timestamp"] < self.cache_ttl:
                    return data["banned"]

        # 3. Consultar API de Steam
        is_banned = self._query_steam_api(steam_id)

        # 4. Guardar en Caché
        with self.lock:
            self.cache[steam_id] = {"banned": is_banned, "timestamp": time.time()}

        return is_banned

    def _query_steam_api(self, steam_id):
        url = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
        params = {"key": self.api_key, "steamids": steam_id}
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                players = data.get("players", [])
                if players:
                    p = players[0]
                    # Criterio de Ban: VAC Banned O Game Bans > 0
                    vac_banned = p.get("VACBanned", False)
                    game_bans = p.get("NumberOfGameBans", 0)
                    
                    if vac_banned or game_bans > 0:
                        return True
        except Exception as e:
            print(f"[Watchdog] API Error: {e}")
            return False  # Fail-open en error de red

        return False
