import customtkinter as ctk
import requests
import threading
import json
import os
import sys
import a2s
import socket
import psutil
import webbrowser
import time
from PIL import Image
from tkinter import messagebox

# ... (imports remain the same)

def resource_path(relative):
    """
    Resuelve la ruta de un recurso de solo lectura (imagens, iconos).
    - onefile (.exe): los assets están en _MEIPASS (bundle temporal)
    - onedir  (.exe): junto al ejecutable
    - desarrollo    : junto a main.py
    """
    # 1. Bundle de PyInstaller onefile
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, relative)
        if os.path.exists(p):
            return p
    # 2. Junto al .exe (onedir) o junto a main.py (desarrollo)
    exe_dir = os.environ.get("ONYX_EXE_DIR") or (
        os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    p = os.path.join(exe_dir, relative)
    if os.path.exists(p):
        return p
    # 3. Fallback: CWD
    return os.path.join(os.getcwd(), relative)


# --- IMPORTACIONES LOCALES ---
from src.ui.styles import COLORS, FONTS
from src.logic.steam_handler import SteamHandler 
from src.logic.database_manager import DatabaseManager 
from src.logic.task_scheduler import TaskManager
from src.logic.stats_shop import StatsShop
from src.logic.rcon_updater import RCONUpdater
from src.logic.file_editor import ConfigEditor
from src.logic.user_manager import UserManager
from src.logic.admin_manager import AdminManager
from src.logic.language_manager import LanguageManager
from src.logic.backup_manager import BackupManager
from src.logic.backup_manager import BackupManager
from src.logic.watchdog import SteamWatchdog
from src.logic.raid_editor import RaidEditor
from src.logic.file_manager import FileManager
from src.logic.txt_watcher import TxtWatcher
from src.logic.log_watcher import SCUMLogWatcher
from src.logic.ip_ban_manager import IPBanManager

# --- CONFIGURACIÓN HARDCODED ---
STEAM_API_KEY = "TU_API_KEY_AQUI" # Reemplaza esto con tu Steam Web API Key

# --- BASE DE DATOS DE CONFIGURACIONES ---
DATABASE_SETTINGS = {
    "cat_world": {
        "scum.TimeOfDaySpeed": "set_time_speed",
        "scum.NighttimeDarkness": "set_night_dark",
        "scum.SunriseTime": "set_sunrise",
        "scum.SunsetTime": "set_sunset",
        "scum.StartTimeOfDay": "set_start_time",
        "scum.ItemDecayDamageMultiplier": "set_decay",
        "scum.AllowMapScreen": "set_map_screen",
    },
    "cat_pve": {
        "scum.DisableSentrySpawning": "set_sentry_spawn",
        "scum.SentryDamageMultiplier": "set_sentry_dmg",
        "scum.ZombieDamageMultiplier": "set_zombie_dmg",
        "scum.MaxAllowedZombies": "set_max_zombies",
        "scum.MaxAllowedAnimals": "set_max_animals",
        "scum.MaxAllowedBirds": "set_max_birds",
        "scum.PuppetsCanOpenDoors": "set_puppets_door",
        "scum.DisableSuicidePuppetSpawning": "set_suicide_puppet",
    },
    "cat_vehicles": {
        "scum.VehicleSpawnGroup.PickupTruck": "set_veh_truck",
        "scum.VehicleSpawnGroup.Quad": "set_veh_quad",
        "scum.VehicleSpawnGroup.Dirtbike": "set_veh_dirtbike",
        "scum.VehicleSpawnGroup.Motorboat": "set_veh_boat",
        "scum.VehicleSpawnGroup.Bicycle": "set_veh_bicycle",
        "scum.FuelDrainFromEngineMultiplier": "set_fuel_drain",
        "scum.BatteryDrainFromEngineMultiplier": "set_batt_drain",
        "scum.MaximumTimeOfVehicleInactivity": "set_veh_inactive",
    },
    "cat_pvp": {
        "scum.HumanToHumanDamageMultiplier": "set_pvp_dmg",
        "scum.AllowFirstPerson": "set_1st_person",
        "scum.AllowThirdPerson": "set_3rd_person",
        "scum.AllowCrosshair": "set_crosshair",
        "scum.AllowKillClaiming": "set_kill_claim",
    },
    "cat_respawn": {
        "scum.RandomRespawnPrice": "set_price_random",
        "scum.SectorRespawnPrice": "set_price_sector",
        "scum.ShelterRespawnPrice": "set_price_shelter",
        "scum.SquadRespawnPrice": "set_price_squad",
        "scum.CommitSuicideCooldown": "set_suicide_cool",
    },
    "cat_general": {
        "scum.ServerName": "set_srv_name",
        "scum.MaxPlayers": "set_max_players",
        "scum.MessageOfTheDay": "set_motd",
        "scum.WelcomeMessage": "set_welcome",
        "scum.ServerDescription": "set_srv_desc",
        "scum.ServerPassword": "set_srv_pass",
        "scum.AllowGlobalChat": "set_chat_global",
        "scum.AllowSquadChat": "set_chat_squad",
        "scum.LogSuicides": "set_log_suicides",
    },
    "cat_building": {
        "scum.DisableBaseBuilding": "set_no_build",
        "scum.UseMapBaseBuildingRestriction": "set_map_restrict",
        "scum.FlagOvertakeDuration": "set_flag_time",
        "scum.MaximumAmountOfElementsPerFlag": "set_max_elements",
    }
}

class VoidWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("ONYX MANAGER - SCUM SERVER ADMIN")
        
        w, h = 1350, 700 
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = int((ws/2)-(w/2)), int((hs/2)-(h/2)) - 40
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1350, 700)
        
        self.configure(fg_color=COLORS["background"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # gui_settings.json debe vivir en ONYX_APPDATA_DIR cuando corre como .exe
        # para que steam_handler._reaplicar_config_gui lea exactamente el mismo archivo.
        _appdata = os.environ.get("ONYX_APPDATA_DIR")
        _settings_base = _appdata if _appdata else os.getcwd()
        self.gui_settings_file = os.path.join(_settings_base, "data", "gui_settings.json")

        self.temp_profile_settings = {} 
        self.cat_translation_map = {}
        self.setting_translation_map = {}
        # Registro de widgets traducibles: [(widget, lang_key)]
        self._i18n_registry: list = []

        self.server_is_fully_loaded = False
        self.player_count_log = 0
        self.battlemetrics_server_id = None
        self.timer_easter = None 

        idioma_inicial = "es"
        if os.path.exists(self.gui_settings_file):
            try:
                with open(self.gui_settings_file, 'r') as f: 
                    saved_data = json.load(f)
                    if "lang" in saved_data: idioma_inicial = saved_data["lang"]
            except: pass
        
        self.lang = LanguageManager(idioma_inicial)
        self.img_path = resource_path("favicon_io")

        self.logo_img = None
        try:
            if os.path.exists(os.path.join(self.img_path, "favicon.ico")): 
                self.iconbitmap(os.path.join(self.img_path, "favicon.ico"))
            if os.path.exists(os.path.join(self.img_path, "Justwhite.png")):
                pil_image = Image.open(os.path.join(self.img_path, "Justwhite.png"))
                target_width = 190
                w_percent = (target_width / float(pil_image.size[0]))
                h_size = int((float(pil_image.size[1]) * float(w_percent)))
                self.logo_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(target_width, h_size))
        except: pass

        self.frame_dashboard = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_scheduler = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_profiles = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_tasks = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_users = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_admins = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_ini_editor = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent") 
        self.frame_raid = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_logs = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_stats_shop = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.steam = SteamHandler(self.log_servidor)
        self.editor = ConfigEditor(self.log_sistema)
        self.users = UserManager(self.log_sistema)
        self.admins = AdminManager(self.log_sistema)
        self.db_manager = DatabaseManager(self.log_sistema, self.steam)
        
        # StatsShop: manual purchase system of stats/skills
        _appdata = os.environ.get("ONYX_APPDATA_DIR", os.getcwd())
        self.stats_shop = StatsShop(self.db_manager.get_db_path(), os.path.join(_appdata, "data"), self.log_sistema)
        
        self.scheduler = TaskManager(self.steam, self.log_sistema, self.editor, stats_shop=self.stats_shop)
        self.watchdog = SteamWatchdog()
        self.raid_editor = RaidEditor(self.log_sistema)
        self.file_manager = FileManager(self.log_sistema)

        # IPBanManager: deteccion de alt accounts por IP duplicada
        _appdata = os.environ.get("ONYX_APPDATA_DIR")
        self.ip_ban_mgr = IPBanManager(self.log_sistema, appdata_dir=_appdata)
        self._ip_ban_activo = False   # se restaura en cargar_memoria_visual

        # Restaurar ruta de servidor guardada previamente
        self._restaurar_ruta_servidor()

        # RCON Updater: actualizador automático de Prisoner RCON
        self.rcon_updater = RCONUpdater(self.steam.server_install_dir, self.log_sistema)

        self.frame_explorer = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.construir_interfaz_completa()
        self.seleccionar_pagina("dashboard")

        # 1. Primero cargamos los valores del .ini como base
        self.sincronizar_todo_con_archivos()
        
        # 2. Luego cargamos la memoria visual del usuario (tiene prioridad sobre el .ini)
        # Así el MOTD y otros valores que el usuario escribió en el panel no se pierden.
        self.cargar_memoria_visual()

        # --- File Watcher: detecta cambios en Ban.txt / Whitelist.txt en tiempo real ---
        self.txt_watcher = TxtWatcher(
            watch_dir = self.users.config_dir,
            after_fn  = self.after,
            callback  = self.accion_sincronizar_usuarios,
            log_fn    = self.log_sistema,
        )
        self.txt_watcher.start()

        # --- Log Watcher: cuenta jugadores desde SCUM.log (fallback a A2S) ---
        self.log_watcher = None
        self._a2s_fail_count = 0  # Contador de fallos A2S para reducir spam
        self._iniciar_log_watcher()
        
        self.monitor_loop()
        
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def construir_interfaz_completa(self):
        # Limpiar el registro al reconstruir la UI (evita referencias a widgets destruidos)
        self._i18n_registry = []
        self.crear_sidebar()
        self.construir_dashboard() 
        self.construir_logs()
        self.construir_scheduler()
        self.construir_tasks()     
        self.construir_users()     
        self.construir_admins()
        self.construir_ini_editor()
        self.construir_raid_editor()
        self.construir_file_explorer()
        self.construir_stats_shop()

    def construir_file_explorer(self):
        for w in self.frame_explorer.winfo_children(): w.destroy()
        
        # --- HEADER ---
        ctk.CTkLabel(self.frame_explorer, text=self.lang.get("explorer_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=20, padx=30, anchor="w")
        
        # --- MAIN CONTAINER (Split View) ---
        main_container = ctk.CTkFrame(self.frame_explorer, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # LEFT: File List
        left_panel = ctk.CTkFrame(main_container, width=300, fg_color=COLORS["panel"])
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        # Navigation Bar
        nav_frame = ctk.CTkFrame(left_panel, fg_color="transparent", height=40)
        nav_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(nav_frame, text="↻", width=30, command=self.refresh_file_list).pack(side="left", padx=2)
        self.lbl_current_path = ctk.CTkLabel(nav_frame, text="/", text_color="gray", anchor="w")
        self.lbl_current_path.pack(side="left", padx=5, fill="x", expand=True)

        self.file_list_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.file_list_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # RIGHT: Editor
        right_panel = ctk.CTkFrame(main_container, fg_color=COLORS["panel"])
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Toolbar
        toolbar = ctk.CTkFrame(right_panel, fg_color="transparent", height=40)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        self.lbl_editing_file = ctk.CTkLabel(toolbar, text="...", font=("Roboto", 12, "bold"), text_color=COLORS["accent"])
        self.lbl_editing_file.pack(side="left")
        
        ctk.CTkButton(toolbar, text=self.lang.get("btn_save_file"), fg_color=COLORS["success"], text_color="black", width=120, command=self.accion_guardar_archivo).pack(side="right", padx=5)
        ctk.CTkButton(toolbar, text=self.lang.get("btn_reload_file"), fg_color=COLORS["accent"], text_color="black", width=100, command=self.accion_recargar_archivo).pack(side="right", padx=5)

        # Text Area
        self.editor_text = ctk.CTkTextbox(right_panel, font=("Consolas", 12), fg_color="#111", text_color="#EEE", undo=True)
        self.editor_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Initial Load
        self.current_explorer_path = ""
        self.refresh_file_list()

    def refresh_file_list(self):
        for w in self.file_list_scroll.winfo_children(): w.destroy()
        
        # Verificar que la ruta raíz del explorador existe
        root = self.file_manager.root_path
        if not os.path.isdir(root):
            ctk.CTkLabel(
                self.file_list_scroll,
                text="⚠️ Ruta del servidor no configurada.\n\nVe al Dashboard y configura\nla carpeta SCUM_Server.",
                text_color="#FFCC00",
                justify="center"
            ).pack(pady=20)
            self.lbl_current_path.configure(text="(sin ruta)")
            return
        
        items = self.file_manager.list_files(self.current_explorer_path)
        self.lbl_current_path.configure(text=f"/{self.current_explorer_path}")
        
        if not items and not self.current_explorer_path:
            ctk.CTkLabel(
                self.file_list_scroll,
                text="📂 Carpeta vacía o sin archivos.",
                text_color="gray"
            ).pack(pady=20)
            return
        
        for item in items:
            self.crear_item_archivo(item)

    def crear_item_archivo(self, item):
        icon = "📁" if item['is_dir'] else "📄"
        color = COLORS["text_main"] if item['is_dir'] else "gray"
        
        btn = ctk.CTkButton(
            self.file_list_scroll, 
            text=f"{icon} {item['name']}", 
            anchor="w", 
            fg_color="transparent", 
            text_color=color, 
            hover_color=COLORS["hover"],
            command=lambda: self.on_file_click(item)
        )
        btn.pack(fill="x", pady=1)

    def on_file_click(self, item):
        if item['name'] == "..":
            self.current_explorer_path = os.path.dirname(self.current_explorer_path)
            self.refresh_file_list()
        elif item['is_dir']:
            self.current_explorer_path = item['path']
            self.refresh_file_list()
        else:
            self.cargar_archivo_editor(item['path'])

    def cargar_archivo_editor(self, path):
        content = self.file_manager.read_file(path)
        if content is not None:
            self.editor_text.delete("0.0", "end")
            self.editor_text.insert("0.0", content)
            self.lbl_editing_file.configure(text=os.path.basename(path))
            self.current_editing_file = path
        else:
            self.log_sistema(self.lang.get("error_read_file"))

    def accion_guardar_archivo(self):
        if not hasattr(self, 'current_editing_file') or not self.current_editing_file: return
        
        content = self.editor_text.get("0.0", "end-1c") # Remove trailing newline added by Text widget
        if self.file_manager.save_file(self.current_editing_file, content):
            self.log_sistema(f"{self.lang.get('msg_file_saved')} ({os.path.basename(self.current_editing_file)})")
        else:
            self.log_sistema("❌ Error guardando archivo.")

    def accion_recargar_archivo(self):
        if hasattr(self, 'current_editing_file') and self.current_editing_file:
            self.cargar_archivo_editor(self.current_editing_file)

    def log_sistema(self, msg):
        try:
            if hasattr(self, 'console') and self.console.winfo_exists():
                self.console.insert("end", f">> {msg}\n"); self.console.see("end")
        except: pass

    def accion_detener(self):
        # Desactivar guardian ANTES: es un stop intencional del admin
        self.steam.detener_guardian()

        self.btn_stop.configure(state="disabled")
        self.log_sistema("🔌 Desconectando servidor...")
        self.steam.detener_servidor()
        self.lbl_status.configure(text=self.lang.get("status_offline"), text_color=COLORS["danger"])
        self.lbl_players.configure(text=f"{self.lang.get('label_players')} ---", text_color="gray")
        self.btn_start.configure(state="normal", fg_color=COLORS["success"], text=f"▶ {self.lang.get('btn_start')}")
        self.btn_stop.configure(state="disabled", text=self.lang.get("btn_status_stopped"))
        self.log_sistema("✅ Servidor desconectado.")

    def _accion_iniciar_con_guardian(self):
        """Inicia el servidor y activa el guardian de proceso automaticamente."""
        self.steam.iniciar_servidor()
        # Dar 5s al proceso para que arranque antes de activar el guardian
        self.after(5000, lambda: self.steam.iniciar_guardian(self.log_sistema))


    def log_servidor(self, msg):
        # --- STATUS UPDATES ---
        if "SOLICITANDO CIERRE" in msg:
            try: self.lbl_status.configure(text=self.lang.get("status_stopping"), text_color=COLORS["danger"])
            except: pass
        elif "Servidor cerrado correctamente" in msg or "Cierre seguro completado" in msg:
            try: self.lbl_status.configure(text=self.lang.get("status_offline"), text_color=COLORS["danger"])
            except: pass
        elif "ENFRIAMIENTO" in msg:
            try: self.lbl_status.configure(text=self.lang.get("status_cooldown"), text_color="#E0A800")
            except: pass
        elif "LANZANDO SERVIDOR" in msg:
            try: self.lbl_status.configure(text=self.lang.get("status_loading"), text_color=COLORS["accent"])
            except: pass
        elif "Cierre seguro NO disponible" in msg:
             try: self.lbl_status.configure(text="UNSAFE SHUTDOWN", text_color=COLORS["danger"])
             except: pass

        triggers = ["Connected to BE Master", "Match State Changed from WaitingToStart to InProgress", "Server Steam ID", "LogNet: Listen", "LogQuadTree: Warning"]
        for t in triggers:
            if t in msg: 
                self.server_is_fully_loaded = True
                try: self.lbl_status.configure(text=self.lang.get("status_online"), text_color=COLORS["success"])
                except: pass
                break
        try:
            if hasattr(self, 'big_console') and self.big_console.winfo_exists():
                self.big_console.insert("end", f"{msg}\n"); self.big_console.see("end")
        except: pass

        try:
            if hasattr(self, 'big_console_tab') and self.big_console_tab.winfo_exists():
                self.big_console_tab.insert("end", f"{msg}\n"); self.big_console_tab.see("end")
        except: pass
    
    def accion_backup_manual(self):
        self.log_sistema(self.lang.get("status_backup"))
        threading.Thread(target=lambda: self.backup_manager.crear_backup(self.log_sistema)).start()

    def accion_detener_hilo(self):
        threading.Thread(target=self.accion_detener).start()

    def accion_reiniciar_hilo(self):
        self.btn_restart.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text=self.lang.get("status_restarting"), text_color="#FFCC00")
        def _reiniciar_y_reactivar_guardian():
            def _callback_post_stop():
                if hasattr(self, 'stats_shop') and self.stats_shop:
                    try:
                        self.log_sistema("🛒 [StatsShop] Verificando suscripciones vencidas...")
                        self.stats_shop.verificar_vencimientos()
                        self.log_sistema("🛒 [StatsShop] Aplicando cambios pendientes en la base de datos...")
                        self.stats_shop.ejecutar_pendientes()
                        self.after(0, self.refrescar_lista_stats_shop)
                    except Exception as ex:
                        self.log_sistema(f"❌ [StatsShop] Error procesando base de datos: {ex}")
            self.steam.reinicio_seguro(self.log_sistema, post_stop_callback=_callback_post_stop)
            # Reactivar guardian 15s despues del reinicio para darle tiempo al servidor de arrancar
            time.sleep(15)
            self.steam.iniciar_guardian(self.log_sistema)

        threading.Thread(target=_reiniciar_y_reactivar_guardian, daemon=True).start()


    def log_msg(self, msg): self.log_sistema(msg)

    # ---------------------------------------------------------------
    # SISTEMA DE TRADUCCIÓN EN CALIENTE
    # ---------------------------------------------------------------
    def _t(self, widget, lang_key: str, attr: str = "text"):
        """Registra un widget para actualizaciones de idioma. Devuelve el widget."""
        self._i18n_registry.append((widget, lang_key, attr))
        return widget

    def _apply_translations(self):
        """Actualiza el texto de todos los widgets registrados con el idioma actual.
        Opera SOLO con .configure() — sin destruir ni crear widgets."""
        for item in self._i18n_registry:
            try:
                widget = item[0]
                key = item[1]
                attr = item[2] if len(item) > 2 else "text"
                if widget.winfo_exists():
                    if attr == "text":
                        widget.configure(text=self.lang.get(key))
                    elif attr == "placeholder_text":
                        widget.configure(placeholder_text=self.lang.get(key))
            except Exception:
                pass

    # ---------------------------------------------------------------

    def crear_sidebar(self):
        if not hasattr(self, 'sidebar'):
            self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["sidebar"])
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.sidebar.grid_columnconfigure(0, weight=1)
        for w in self.sidebar.winfo_children(): w.destroy()
        if self.logo_img:
            lbl_logo = ctk.CTkLabel(self.sidebar, text="", image=self.logo_img)
            lbl_logo.grid(row=0, column=0, padx=15, pady=(5, 5))
            lbl_logo.bind("<ButtonPress-1>", self.iniciar_conteo_easter)
            lbl_logo.bind("<ButtonRelease-1>", self.cancelar_conteo_easter)

        # Sidebar buttons — registrados para traducción en caliente
        self.crear_boton_menu("menu_dashboard", "dashboard", 2)
        self.crear_boton_menu("menu_profiles",  "profiles",  3)
        self.crear_boton_menu("menu_scheduler", "tasks",     4)
        self.crear_boton_menu("menu_users",     "users",     5)
        self.crear_boton_menu("menu_admins",    "admins",    6)
        self.crear_boton_menu("menu_editor",    "ini_editor",7)
        self.crear_boton_menu("menu_raid",      "raid",      8)
        self.crear_boton_menu("menu_explorer",  "explorer",  9)
        self.crear_boton_menu("menu_logs",      "logs",      10)
        self.crear_boton_menu("menu_stats_shop", "stats_shop", 11)
        ctk.CTkLabel(self.sidebar, text="v1.0 PRO", text_color=COLORS["text_dim"]).grid(row=12, column=0, pady=20, sticky="s")
        self.sidebar.grid_rowconfigure(12, weight=1)

    def crear_boton_menu(self, lang_key: str, pagina: str, fila: int):
        """Crea un botón de menú y lo registra para traducción en caliente."""
        btn = ctk.CTkButton(
            self.sidebar, text=self.lang.get(lang_key),
            fg_color="transparent", text_color=COLORS["text_main"],
            hover_color=COLORS["hover"], anchor="w",
            command=lambda p=pagina: self.seleccionar_pagina(p)
        )
        btn.grid(row=fila, column=0, padx=10, pady=5, sticky="ew")
        self._t(btn, lang_key)

    def seleccionar_pagina(self, nombre):
        self.frame_dashboard.grid_forget(); self.frame_profiles.grid_forget(); self.frame_tasks.grid_forget()
        self.frame_users.grid_forget(); self.frame_logs.grid_forget()
        self.frame_admins.grid_forget(); self.frame_ini_editor.grid_forget()
        self.frame_raid.grid_forget(); self.frame_explorer.grid_forget()
        self.frame_stats_shop.grid_forget()

        if nombre == "dashboard": self.frame_dashboard.grid(row=0, column=1, sticky="nsew")
        elif nombre == "profiles": self.frame_profiles.grid(row=0, column=1, sticky="nsew")
        elif nombre == "tasks": self.frame_tasks.grid(row=0, column=1, sticky="nsew")
        elif nombre == "users": self.frame_users.grid(row=0, column=1, sticky="nsew"); self.refrescar_lista_usuarios()
        elif nombre == "admins": self.frame_admins.grid(row=0, column=1, sticky="nsew"); self.refrescar_listas_admins()
        elif nombre == "ini_editor": self.frame_ini_editor.grid(row=0, column=1, sticky="nsew")
        elif nombre == "raid": self.frame_raid.grid(row=0, column=1, sticky="nsew")
        elif nombre == "explorer": self.frame_explorer.grid(row=0, column=1, sticky="nsew")
        elif nombre == "logs": self.frame_logs.grid(row=0, column=1, sticky="nsew")
        elif nombre == "stats_shop": self.frame_stats_shop.grid(row=0, column=1, sticky="nsew"); self.refrescar_lista_stats_shop()

    # ─── GESTIÓN DINÁMICA DE RUTA DEL SERVIDOR ───────────────────────────────

    def _restaurar_ruta_servidor(self):
        """Al iniciar, recupera la ruta del servidor guardada o la autodetecta y re-apunta todos los módulos."""
        ruta = ""
        try:
            if os.path.exists(self.gui_settings_file):
                with open(self.gui_settings_file, 'r') as f:
                    datos = json.load(f)
                ruta = datos.get("server_path", "")
        except Exception:
            pass

        # Si no hay ruta guardada o no es válida, intentar autodetectar
        if not ruta or not os.path.isdir(ruta):
            try:
                from src.logic.path_manager import find_server_directory
                ruta = find_server_directory()
            except ImportError:
                pass

        if ruta and os.path.isdir(ruta):
            self._aplicar_ruta_servidor(ruta, silencioso=True)

    def _aplicar_ruta_servidor(self, ruta_base, silencioso=False):
        """
        Re-inicializa editor, file_manager, users, admins y steam
        para que todos apunten a 'ruta_base' (la carpeta SCUM_Server).
        """
        # Guardar la ruta en disco
        try:
            datos = {}
            if os.path.exists(self.gui_settings_file):
                with open(self.gui_settings_file, 'r') as f:
                    datos = json.load(f)
            datos["server_path"] = ruta_base
            with open(self.gui_settings_file, 'w') as f:
                json.dump(datos, f)
        except Exception:
            pass

        # Re-apuntar cada módulo
        self.editor      = ConfigEditor(self.log_sistema, base_path=ruta_base)
        self.file_manager = FileManager(self.log_sistema, base_path=ruta_base)
        self.users       = UserManager(self.log_sistema, base_path=ruta_base)
        self.admins      = AdminManager(self.log_sistema, base_path=ruta_base)
        self.steam.server_install_dir = ruta_base
        self.steam.server_exe = os.path.join(
            ruta_base, "SCUM", "Binaries", "Win64", "SCUMServer.exe"
        )

        # Actualizar base de datos de StatsShop y RCON Updater
        if hasattr(self, 'stats_shop') and self.stats_shop:
            self.stats_shop.db_path = self.db_manager.get_db_path()
        if hasattr(self, 'rcon_updater') and self.rcon_updater:
            self.rcon_updater.server_dir = ruta_base
            self.rcon_updater.bin_dir = os.path.join(ruta_base, "SCUM", "Binaries", "Win64")

        # CRITICO: Actualizar el editor en el scheduler tambien.
        # Sin esto, las automatizaciones (perfiles) escriben al editor viejo
        # que apunta a una ruta incorrecta o inexistente.
        if hasattr(self, 'scheduler'):
            self.scheduler.editor = self.editor

        # Actualizar raid_editor para que RaidTimes.json se escriba en el servidor correcto
        self.raid_editor = RaidEditor(self.log_sistema, base_path=ruta_base)

        # Reiniciar el LogWatcher con la nueva ruta
        self._iniciar_log_watcher(ruta_base)

        # Actualizar label de ruta en la UI y el indicador de color
        if hasattr(self, 'lbl_server_path'):
            self.lbl_server_path.configure(text=ruta_base)
        self._actualizar_indicador_ruta()

        if not silencioso:
            self.log_sistema(f"\u2705 Servidor cambiado a: {ruta_base}")
            # Sincronizar UI con la nueva carpeta
            self.sincronizar_todo_con_archivos()
            self.refrescar_listas_admins()
            self.refrescar_lista_usuarios()


    def cambiar_carpeta_servidor(self):
        """Abre un selector de carpeta y cambia la carpeta activa del servidor."""
        from tkinter import filedialog
        ruta = filedialog.askdirectory(
            title="Selecciona la carpeta SCUM_Server",
            initialdir=os.environ.get("ONYX_EXE_DIR", os.getcwd())
        )
        if not ruta:
            return  # Cancelado
        # Verificar que tenga aspecto de servidor SCUM
        ini_path = os.path.join(ruta, "SCUM", "Saved", "Config", "WindowsServer", "ServerSettings.ini")
        exe_path = os.path.join(ruta, "SCUM", "Binaries", "Win64", "SCUMServer.exe")
        if not os.path.exists(ini_path) and not os.path.exists(exe_path):
            from tkinter import messagebox as _mb
            if not _mb.askyesno(
                "Carpeta sin servidor SCUM",
                "No se encontró una instalación de SCUM en esa carpeta.\n"
                "\u00bfSeguro que quieres usar esta ruta?"
            ):
                return
        self._aplicar_ruta_servidor(ruta)

    def _accion_cambiar_ruta_servidor(self):
        """Wrapper: abre el diálogo de selección y luego actualiza el indicador visual."""
        self.cambiar_carpeta_servidor()
        self._actualizar_indicador_ruta()

    def _actualizar_indicador_ruta(self):
        """Actualiza el punto de color y el label de ruta según si la ruta es válida."""
        try:
            ruta = self.file_manager.root_path if hasattr(self, 'file_manager') else ""
            # Buscar la ruta real del servidor (subimos desde WindowsServer hasta SCUM_Server)
            srv_root = ""
            if ruta:
                # root_path es .../SCUM_Server/SCUM/Saved/Config/WindowsServer
                # Subimos 4 niveles para llegar a SCUM_Server
                p = ruta
                for _ in range(4):
                    p = os.path.dirname(p)
                srv_root = p

            valida = srv_root and os.path.isdir(srv_root)

            if hasattr(self, 'lbl_server_path'):
                display = srv_root if valida else "(sin configurar — haz clic en 'Cambiar Ruta')"
                self.lbl_server_path.configure(text=display)

            if hasattr(self, 'lbl_server_status_dot'):
                color = "#4CAF50" if valida else "#F44336"
                self.lbl_server_status_dot.configure(text_color=color)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────

    def _iniciar_log_watcher(self, server_path=None):
        """Arranca (o reinicia) el SCUMLogWatcher con la ruta correcta del servidor."""
        # Detener el anterior si existe (usar getattr por si se llama antes de __init__ completo)
        existing = getattr(self, 'log_watcher', None)
        if existing:
            existing.stop()
        self.log_watcher = None

        # Obtener la ruta del servidor
        ruta = server_path
        if not ruta:
            try:
                if os.path.exists(self.gui_settings_file):
                    with open(self.gui_settings_file, 'r') as f:
                        ruta = json.load(f).get("server_path", "")
            except: pass

        if not ruta:
            ruta = self.steam.server_install_dir

        if ruta and os.path.isdir(ruta):
            self.log_watcher = SCUMLogWatcher(
                ruta,
                log_callback=self.log_sistema,
                on_player_join=self._on_player_join_handler
            )
            self.log_watcher.start()
            # Escanear logs historicos para poblar el registro de IPs
            self.ip_ban_mgr.escanear_logs_historicos(ruta)

    def sincronizar_todo_con_archivos(self):
        """FUERZA la sincronización de la UI con los archivos reales del disco"""
        self.log_sistema("\U0001f504 Sincronizando con archivos del servidor...")

        # 1. Configuración del Servidor (.ini)
        datos_ini = self.editor.cargar_configuracion()
        if datos_ini:
            def rellenar(entry, key):
                # CORRECTO: Solo rellenar si el campo está VACÍO en la UI.
                # Si el usuario ya escribió algo, NO pisar con lo que está en el .ini
                # (SCUM borra el MOTD/contraseña del .ini en su shutdown, y no debemos reflejarlo aquí).
                campo_actual = entry.get().strip()
                if campo_actual:   # Ya tiene contenido → no tocar
                    return
                val = datos_ini.get(key) or datos_ini.get(key.lower())
                if val:            # Solo rellenar si el .ini tiene algo
                    entry.delete(0, "end")
                    entry.insert(0, val)

            rellenar(self.entry_name,    "scum.ServerName")
            rellenar(self.entry_welcome,  "scum.WelcomeMessage")
            rellenar(self.entry_motd,     "scum.MessageOfTheDay")
            rellenar(self.entry_pass,     "scum.ServerPassword")
            rellenar(self.entry_players,  "scum.MaxPlayers")
            nombre_real = (datos_ini.get("scum.ServerName")
                          or datos_ini.get("scum.servername") or "(no encontrado)")
            self.log_sistema(f"\U0001f4dd Servidor: {nombre_real}")
        else:
            self.log_sistema("\u26a0\ufe0f ServerSettings.ini no encontrado — instala el servidor primero.")

        # 2. Usuarios (Ban / VIP)
        self.users.sincronizar_con_archivos()

        # 3. Admins
        self.refrescar_listas_admins()

        # 4. Refrescar explorador de archivos
        if hasattr(self, 'file_list_scroll'):
            self.current_explorer_path = ""
            self.refresh_file_list()

        self.log_sistema("\u2705 Sincronización completada.")

    def cambiar_idioma(self, lang_code):
        """Cambia el idioma SIN reconstruir la UI — solo actualiza textos."""
        self.lang.load_language(lang_code)
        # Persistir en disco
        try:
            if os.path.exists(self.gui_settings_file):
                with open(self.gui_settings_file, 'r') as f: datos = json.load(f)
            else: datos = {}
            datos["lang"] = lang_code
            with open(self.gui_settings_file, 'w') as f: json.dump(datos, f)
        except: pass
        # Actualizar solo los textos — sin destruir ni crear widgets → sin flash
        self._apply_translations()
        if hasattr(self, 'frame_subs_list') and self.frame_subs_list.winfo_exists():
            self.refrescar_lista_stats_shop()
        if hasattr(self, 'lbl_stats_player_info') and self.lbl_stats_player_info.winfo_exists():
            if not self.stats_selected_player:
                self.lbl_stats_player_info.configure(text=self.lang.get("stats_shop_no_player_selected"))
            else:
                p = self.stats_selected_player
                prefix = self.lang.get("stats_shop_selected")
                self.lbl_stats_player_info.configure(
                    text=f"{prefix}: {p['name']} ({p['steam_id']})\nPrisoner ID: {p['prisoner_id']}"
                )
        if hasattr(self, 'frame_added_skills') and self.frame_added_skills.winfo_exists():
            self._refrescar_visual_skills_agregados()
        self.log_sistema(f"{self.lang.get('log_lang_changed')} {lang_code.upper()}")

    def construir_dashboard(self):
        for w in self.frame_dashboard.winfo_children(): w.destroy()
        
        # --- PANEL SUPERIOR (ESTADO Y CONTROLES) ---
        panel_top = ctk.CTkFrame(self.frame_dashboard, fg_color=COLORS["panel"], corner_radius=10)
        panel_top.pack(fill="x", padx=20, pady=10)
        
        # 1. INFO BOX (Izquierda)
        info_box = ctk.CTkFrame(panel_top, fg_color="transparent")
        info_box.pack(side="left", padx=20, pady=10)
        
        self.lbl_status = ctk.CTkLabel(info_box, text=self.lang.get("status_offline"), text_color=COLORS["danger"], font=("Roboto", 20, "bold"))
        self.lbl_status.pack(anchor="w")
        
        self.lbl_players = ctk.CTkLabel(info_box, text=f"{self.lang.get('label_players')} ---", text_color="gray", font=("Roboto", 14))
        self.lbl_players.pack(anchor="w")
        
        stats_frame = ctk.CTkFrame(info_box, fg_color="transparent")
        stats_frame.pack(anchor="w")
        self.lbl_cpu = ctk.CTkLabel(stats_frame, text=f"{self.lang.get('cpu')} 0%", text_color=COLORS["text_dim"], font=("Roboto", 11))
        self.lbl_cpu.pack(side="left", padx=(0, 10))
        self.lbl_ram = ctk.CTkLabel(stats_frame, text=f"{self.lang.get('ram')} 0%", text_color=COLORS["text_dim"], font=("Roboto", 11))
        self.lbl_ram.pack(side="left")

        # 2. SWITCHES (Centro-Izquierda)
        switches_frame = ctk.CTkFrame(panel_top, fg_color="transparent")
        switches_frame.pack(side="left", padx=20, pady=10)
        
        self.switch_auto = ctk.CTkSwitch(switches_frame, text=self.lang.get("auto_update"), progress_color=COLORS["success"], text_color="gray", command=self.toggle_auto_update)
        self.switch_auto.pack(anchor="w", pady=2)
        self._t(self.switch_auto, "auto_update")
        
        self.switch_watchdog = ctk.CTkSwitch(switches_frame, text="Auto-Ban (VAC/GameBan)", progress_color=COLORS["danger"], text_color="gray", command=self.toggle_watchdog)
        self.switch_watchdog.pack(anchor="w", pady=2)
        
        self.switch_nobattleye = ctk.CTkSwitch(switches_frame, text=self.lang.get("toggle_nobattleye"), progress_color=COLORS["danger"], text_color="gray")
        self.switch_nobattleye.pack(anchor="w", pady=2)
        self._t(self.switch_nobattleye, "toggle_nobattleye")
        
        self.lbl_watchdog_status = ctk.CTkLabel(switches_frame, text="", font=("Roboto", 10))
        self.lbl_watchdog_status.pack(anchor="w")

        self.lbl_rcon_version = ctk.CTkLabel(switches_frame, text="RCON: ...", font=("Roboto", 10), text_color="gray")
        self.lbl_rcon_version.pack(anchor="w", pady=(2, 0))

        # 3. BOTONES DE ACCIÓN (Derecha)
        actions_frame = ctk.CTkFrame(panel_top, fg_color="transparent")
        actions_frame.pack(side="right", padx=20, pady=10)

        # Fila superior (Start, Restart, Stop)
        row_btns_1 = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row_btns_1.pack(side="top", anchor="e", pady=(0, 5))
        
        self.btn_start = ctk.CTkButton(row_btns_1, text=self.lang.get("btn_start"), fg_color=COLORS["success"], text_color="black", hover_color="#2E7D32", width=100, command=self._accion_iniciar_con_guardian)

        self.btn_start.pack(side="left", padx=5)
        self._t(self.btn_start, "btn_start")
        
        self.btn_restart = ctk.CTkButton(row_btns_1, text=self.lang.get("btn_restart"), fg_color="#D35400", hover_color="#A04000", width=100, command=self.accion_reiniciar_hilo)
        self.btn_restart.pack(side="left", padx=5)
        self._t(self.btn_restart, "btn_restart")
        
        self.btn_stop = ctk.CTkButton(row_btns_1, text=self.lang.get("btn_stop"), fg_color=COLORS["danger"], hover_color="#A00000", width=100, command=self.accion_detener_hilo)
        self.btn_stop.pack(side="left", padx=5)
        self._t(self.btn_stop, "btn_stop")

        # Fila inferior (Update, Backup, Lang)
        row_btns_2 = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row_btns_2.pack(side="top", anchor="e")

        self.btn_update = ctk.CTkButton(row_btns_2, text=self.lang.get("btn_update"), fg_color="#E0A800", text_color="black", hover_color="#C69500", width=120, command=self._accion_actualizar_manual)
        self.btn_update.pack(side="left", padx=5)
        self._t(self.btn_update, "btn_update")
        
        btn_backup = ctk.CTkButton(row_btns_2, text=self.lang.get("btn_backup"), fg_color="#4a4a4a", width=80, command=self.accion_backup_manual)
        btn_backup.pack(side="left", padx=5)
        self._t(btn_backup, "btn_backup")
        
        self.combo_lang = ctk.CTkComboBox(row_btns_2, values=["es", "en", "pt", "fr", "ru", "de", "zh", "hi", "ja"], width=60, command=self.cambiar_idioma)
        self.combo_lang.set(self.lang.current_lang)
        self.combo_lang.pack(side="left", padx=5)

        # ─── Barra de ruta del servidor ───────────────────────────────────────
        server_bar = ctk.CTkFrame(
            self.frame_dashboard,
            fg_color="#141414",
            corner_radius=8,
            border_width=1,
            border_color="#2a2a2a"
        )
        server_bar.pack(fill="x", padx=20, pady=(0, 6))

        # Icono + label izquierdo
        lbl_srv_title = ctk.CTkLabel(
            server_bar,
            text="📂  Carpeta Servidor:",
            text_color="#888",
            font=("Roboto", 11, "bold")
        )
        lbl_srv_title.pack(side="left", padx=(12, 6), pady=6)

        # Indicador de estado (●)
        self.lbl_server_status_dot = ctk.CTkLabel(
            server_bar,
            text="●",
            font=("Roboto", 14, "bold"),
            text_color="#555"
        )
        self.lbl_server_status_dot.pack(side="left", padx=(0, 4))

        # Label con la ruta actual
        ruta_actual = getattr(self, '_server_path_display', "(sin configurar)")
        self.lbl_server_path = ctk.CTkLabel(
            server_bar,
            text=ruta_actual,
            text_color="#CCCCCC",
            font=("Consolas", 11),
            anchor="w"
        )
        self.lbl_server_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Botón Sincronizar
        btn_sync_srv = ctk.CTkButton(
            server_bar,
            text="🔄 Sincronizar",
            width=110,
            height=28,
            fg_color="#1a3a5c",
            hover_color="#1d4a78",
            text_color="white",
            font=("Roboto", 11),
            command=self.sincronizar_todo_con_archivos
        )
        btn_sync_srv.pack(side="right", padx=5, pady=5)

        # Botón Cambiar carpeta
        btn_cambiar_srv = ctk.CTkButton(
            server_bar,
            text="📁 Cambiar Ruta",
            width=120,
            height=28,
            fg_color=COLORS["accent"],
            hover_color="#C69500",
            text_color="black",
            font=("Roboto", 11, "bold"),
            command=self._accion_cambiar_ruta_servidor
        )
        btn_cambiar_srv.pack(side="right", padx=(0, 5), pady=5)

        # Actualizar el indicador de color según si la ruta es válida
        self._actualizar_indicador_ruta()

        # --- RESTO DEL DASHBOARD ---
        middle_container = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent"); middle_container.pack(fill="x", padx=20, pady=5)
        panel_config = ctk.CTkFrame(middle_container, fg_color="transparent"); panel_config.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Header
        header_frame = ctk.CTkFrame(panel_config, fg_color="transparent"); header_frame.pack(fill="x", pady=(0, 5))
        self._t(ctk.CTkLabel(header_frame, text=self.lang.get("header_config"), text_color=COLORS["text_dim"], font=("Roboto", 12, "bold")), "header_config").pack(side="left")
        btn_save = ctk.CTkButton(header_frame, text=self.lang.get("btn_save_changes"), width=100, height=24, fg_color=COLORS["accent"], text_color="black", command=self.accion_guardar)
        btn_save.pack(side="right")
        self._t(btn_save, "btn_save_changes")
        
        # Grid System
        grid_frame = ctk.CTkFrame(panel_config, fg_color=COLORS["panel"], corner_radius=10)
        grid_frame.pack(fill="x", pady=2)
        
        # --- RADICAL FIX: Force Row Heights ---
        # grid_frame.grid_rowconfigure((0, 1, 2, 3), minsize=45) # REMOVED to fix spacing issue
        grid_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        # Fila 0: Nombre Servidor (Full Width)
        self.entry_name = self.crear_input(grid_frame, self.lang.get("lbl_name"), "SCUM Server", 0, 0, span=4, lang_key="lbl_name")
        
        # Fila 1: Descripción y Mensaje (Split)
        self.entry_welcome = self.crear_input(grid_frame, self.lang.get("lbl_welcome_msg"), "", 1, 0, span=2, lang_key="lbl_welcome_msg")
        self.entry_motd = self.crear_input(grid_frame, self.lang.get("lbl_motd"), "", 1, 2, span=2, lang_key="lbl_motd")
        
        # Fila 2: Technical Row (IP, Ports, Slots, Pass)
        tech_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        tech_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=2)
        tech_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        self.crear_input_ip(tech_frame, 0, 0)
        self.entry_port    = self.crear_input(tech_frame, self.lang.get("lbl_gameport"),  "7777",  0, 1, lang_key="lbl_gameport")
        self.entry_query   = self.crear_input(tech_frame, self.lang.get("lbl_queryport"), "27015", 0, 2, lang_key="lbl_queryport")
        self.entry_players = self.crear_input(tech_frame, self.lang.get("lbl_slots"),     "64",    0, 3, lang_key="lbl_slots")
        self.entry_pass    = self.crear_input(tech_frame, self.lang.get("lbl_pass"),      "",      0, 4, lang_key="lbl_pass")
        
        # Fila 3: API Key (Full Width)
        self.entry_api_key = self.crear_input(grid_frame, "Steam Web API Key", "", 3, 0, span=4, show="*")

        # Disable Copy/Cut/Context Menu for API Key
        def disable_event(event): return "break"
        self.entry_api_key.bind("<Control-c>", disable_event)
        self.entry_api_key.bind("<Control-x>", disable_event)
        self.entry_api_key.bind("<Button-3>", disable_event) # Right click

        # Fila 4: RCON Download URL and Auto Update Switch
        self.entry_rcon_url = self.crear_input(grid_frame, "URL de Descarga RCON (ZIP de Galo)", "", 4, 0, span=3)
        
        container_switch = ctk.CTkFrame(grid_frame, fg_color="transparent")
        container_switch.grid(row=4, column=3, columnspan=1, sticky="new", padx=5, pady=(0, 5))
        lbl_switch = ctk.CTkLabel(container_switch, text="Actualizar RCON", text_color=COLORS["text_dim"], font=("Roboto", 11, "bold"), anchor="w")
        lbl_switch.pack(fill="x", pady=(0, 2))
        self.switch_rcon_auto = ctk.CTkSwitch(container_switch, text="", progress_color=COLORS["success"], text_color="gray")
        self.switch_rcon_auto.pack(anchor="w", pady=2)

        # --- RADICAL FIX: Shrink Consoles ---
        panel_syslog = ctk.CTkFrame(middle_container, width=300, fg_color=COLORS["panel"]); panel_syslog.pack(side="right", fill="y", padx=(0,0))
        self._t(ctk.CTkLabel(panel_syslog, text=self.lang.get("log_title_sys"), text_color="#00FF00", font=("Roboto", 11, "bold")), "log_title_sys").pack(pady=(5, 2), padx=10)
        # Height reduced to 120
        self.console = ctk.CTkTextbox(panel_syslog, width=280, height=120, fg_color="#111", text_color="#00FF00", font=("Consolas", 10)); self.console.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.log_sistema(self.lang.get("log_init"))
        
        panel_matrix = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent"); panel_matrix.pack(fill="both", expand=True, padx=20, pady=(2, 5))
        ctk.CTkLabel(panel_matrix, text=self.lang.get("log_title_matrix"), text_color=COLORS["text_main"], font=("Roboto", 12, "bold")).pack(anchor="w")
        # Height reduced to 120
        self.big_console = ctk.CTkTextbox(panel_matrix, height=120, fg_color="#000000", text_color="#00FF00", font=("Consolas", 11), activate_scrollbars=True)
        self.big_console.pack(fill="both", expand=True)
        self.big_console.insert("0.0", f"{self.lang.get('log_waiting_server')}")

    def crear_input(self, parent, label, default, r, c, span=1, show=None, lang_key=None):
        # 1. Crear un Frame contenedor (Transparente)
        container = ctk.CTkFrame(parent, fg_color="transparent")
        # IMPORTANTE: pady=(0, 5) asegura espacio justo
        container.grid(row=r, column=c, columnspan=span, sticky="new", padx=5, pady=(0, 5))

        # 2. Label (Titulo)
        lbl = ctk.CTkLabel(container, text=label, text_color=COLORS["text_dim"], font=("Roboto", 11, "bold"), anchor="w")
        lbl.pack(fill="x", pady=(0, 2))
        if lang_key:
            self._t(lbl, lang_key)

        # 3. Entry (Caja de texto)
        entry = ctk.CTkEntry(container, height=28, border_color="#333", fg_color="#111", text_color="white")
        if show: entry.configure(show=show)
        entry.pack(fill="x")

        # 4. Insertar valor y retornar
        entry.insert(0, default)
        return entry

    def crear_input_ip(self, parent, r, c):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=r, column=c, sticky="new", padx=5, pady=(0, 5))
        
        lbl = ctk.CTkLabel(container, text=self.lang.get("lbl_ip"), text_color=COLORS["text_dim"], font=("Roboto", 11, "bold"), anchor="w")
        lbl.pack(fill="x", pady=(0, 2))
        self._t(lbl, "lbl_ip")
        
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.entry_ip = ctk.CTkEntry(input_frame, height=28, border_color="#333", fg_color="#111", text_color="white")
        self.entry_ip.pack(side="left", fill="x", expand=True)
        
        btn_detect = ctk.CTkButton(input_frame, text="Auto", width=40, height=28, fg_color=COLORS["accent"], text_color="black", command=self.autodetectar_ip)
        btn_detect.pack(side="right", padx=(5, 0))
        
        self.entry_ip.insert(0, "")

    def autodetectar_ip(self):
        def buscar():
            try: ip = requests.get('https://api.ipify.org').text; self.entry_ip.delete(0, "end"); self.entry_ip.insert(0, ip); self.log_sistema(f"{self.lang.get('log_ip_detected')} {ip}")
            except: self.log_sistema(self.lang.get("error_ip_search"))
        threading.Thread(target=buscar).start()
        
    def _accion_actualizar_manual(self):
        """Lanza instalar_servidor en un thread, protegido contra doble-click."""
        if getattr(self, '_update_running', False):
            self.log_sistema("⚠️ Ya hay una actualizacion en curso. Espera a que termine.")
            return
        self._update_running = True
        self.btn_update.configure(state="disabled", text="⏳ Actualizando...")
        def _run():
            try:
                self.steam.instalar_servidor()
            finally:
                self._update_running = False
                try:
                    self.after(0, lambda: self.btn_update.configure(
                        state="normal", text=self.lang.get("btn_update")
                    ))
                except: pass
        threading.Thread(target=_run, daemon=True).start()

    def toggle_auto_update(self):
        if self.switch_auto.get() == 1:
            self.log_sistema(self.lang.get("log_autoupdate_on"))
            # Siempre desactivar primero para evitar jobs duplicados
            self.scheduler.desactivar_auto_update()
            self.scheduler.activar_auto_update(15)  # Cada 15 minutos
        else:
            self.log_sistema(self.lang.get("log_autoupdate_off"))
            self.scheduler.desactivar_auto_update()

    def toggle_watchdog(self):
        if self.switch_watchdog.get() == 1:
            # Prioritize UI input, fallback to global if UI is empty/placeholder
            ui_key = self.entry_api_key.get().strip()
            code_key = STEAM_API_KEY
            
            final_key = ui_key if len(ui_key) > 10 else code_key
            
            if not final_key or "TU_API_KEY" in final_key:
                self.log_sistema(self.lang.get("watchdog_missing_key"))
                self.switch_watchdog.deselect()
                return
            self.watchdog.set_api_key(final_key)
            self.lbl_watchdog_status.configure(text=self.lang.get("watchdog_active"), text_color=COLORS["success"])
        else:
            self.lbl_watchdog_status.configure(text="")

    def accion_guardar(self):
        # 1. Guardar configuración del juego (ServerSettings.ini)
        datos = { 
            "scum.ServerName": self.entry_name.get(), 
            "scum.WelcomeMessage": self.entry_welcome.get(),
            "scum.MessageOfTheDay": self.entry_motd.get(),
            "scum.ServerPassword": self.entry_pass.get(),
            "scum.MaxPlayers": self.entry_players.get(),
        }
        self.editor.guardar_configuracion(datos)

        # 2. Guardar estado visual (Inputs, incluyendo puertos y Watchdog)
        self.guardar_memoria_visual_en_disco()

        self.log_sistema("✅ Configuración guardada. (Puertos aplicados al reiniciar).")

    def cerrar_aplicacion(self):
        # 1. Guardar estado visual
        self.guardar_memoria_visual_en_disco()

        # 2. Detener File Watcher antes de cerrar
        if hasattr(self, 'txt_watcher'):
            self.txt_watcher.stop()

        # 3. Detener servidor si está corriendo
        if self.steam.esta_corriendo():
            self.steam.detener_servidor()

        # 4. Forzar salida inmediata
        self.destroy()
        os._exit(0)

    def guardar_memoria_visual_en_disco(self):
        try:
            gui_data = {
                "ip": self.entry_ip.get(),
                "port": self.entry_port.get(),
                "query": self.entry_query.get(),
                "name": self.entry_name.get(),
                "welcome": self.entry_welcome.get(),
                "motd": self.entry_motd.get(),
                "pass": self.entry_pass.get(),
                "players": self.entry_players.get(),
                "auto_update": self.switch_auto.get(),
                "lang": self.lang.current_lang,
                "steam_api_key": self.entry_api_key.get().strip(),
                "watchdog_enabled": self.switch_watchdog.get(),
                "nobattleye": self.switch_nobattleye.get(),
                "rcon_download_url": self.entry_rcon_url.get().strip() if hasattr(self, "entry_rcon_url") else "",
                "rcon_auto_update": self.switch_rcon_auto.get() if hasattr(self, "switch_rcon_auto") else 0
            }

            # Actualizar Watchdog Key al guardar
            final_key = gui_data["steam_api_key"]
            if not final_key or "TU_API_KEY" in final_key: final_key = STEAM_API_KEY

            self.watchdog.set_api_key(final_key)
            if gui_data["watchdog_enabled"] == 1 and (not final_key or "TU_API_KEY" in final_key):
                self.switch_watchdog.deselect()
                gui_data["watchdog_enabled"] = 0
                self.log_sistema(self.lang.get("watchdog_disabled_no_key"))

            # Crear directorio si no existe (primera ejecucion o ruta nueva)
            os.makedirs(os.path.dirname(self.gui_settings_file), exist_ok=True)
            with open(self.gui_settings_file, 'w', encoding='utf-8') as f:
                json.dump(gui_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.log_sistema(f"⚠️ Error guardando configuracion visual: {e}")

    def guardar_memoria_visual(self): self.guardar_memoria_visual_en_disco()


    def cargar_memoria_visual(self):
        if not os.path.exists(self.gui_settings_file): return
        try:
            with open(self.gui_settings_file, 'r') as f: datos = json.load(f)
            if "auto_update" in datos and datos["auto_update"] == 1: self.switch_auto.select(); self.toggle_auto_update()
            if "nobattleye" in datos and datos["nobattleye"] == 1: self.switch_nobattleye.select()
            if "lang" in datos: self.combo_lang.set(datos["lang"]) 
            
            # Cargar API Key
            if "steam_api_key" in datos: 
                self.entry_api_key.delete(0, "end")
                self.entry_api_key.insert(0, datos["steam_api_key"])
            
            # Cargar Watchdog
            key_to_use = self.entry_api_key.get().strip()
            if not key_to_use: key_to_use = STEAM_API_KEY
            self.watchdog.set_api_key(key_to_use)
            
            if "watchdog_enabled" in datos and datos["watchdog_enabled"] == 1:
                if key_to_use and "TU_API_KEY" not in key_to_use:
                    self.switch_watchdog.select()
                    self.toggle_watchdog()

            # Restaurar estado de auto-ban por IP
            if "ip_ban_activo" in datos:
                self._ip_ban_activo = bool(datos["ip_ban_activo"])


            def rellenar(entry, key):
                # CRITICO: comprobar presencia de clave SEPARADO del valor
                # Si el valor es "" (contraseña borrada), hay que rellenarlo igual
                # para que el campo se vacíe correctamente.
                if key in datos:
                    entry.delete(0, "end")
                    if datos[key]:  # solo insertar si no es vacío
                        entry.insert(0, datos[key])
            rellenar(self.entry_name, "name"); rellenar(self.entry_welcome, "welcome"); rellenar(self.entry_motd, "motd"); rellenar(self.entry_ip, "ip"); rellenar(self.entry_port, "port"); rellenar(self.entry_query, "query"); rellenar(self.entry_pass, "pass"); rellenar(self.entry_players, "players")
        except: pass

    def construir_scheduler(self):
        for w in self.frame_profiles.winfo_children(): w.destroy()
        self.workbench_rows = []

        self._t(ctk.CTkLabel(self.frame_profiles, text=self.lang.get("prof_title"),
                     font=("Roboto", 22, "bold"), text_color=COLORS["text_main"]), "prof_title").pack(pady=(15, 5), padx=25, anchor="w")

        # --- SPLIT: izquierda editor, derecha cards ---
        split = ctk.CTkFrame(self.frame_profiles, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        split.grid_columnconfigure(0, weight=1)
        split.grid_columnconfigure(1, weight=1)
        split.grid_rowconfigure(0, weight=1)

        # ===== PANEL IZQUIERDO: EDITOR =====
        panel_ed = ctk.CTkFrame(split, fg_color=COLORS["panel"], corner_radius=10)
        panel_ed.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self._t(ctk.CTkLabel(panel_ed, text=self.lang.get("prof_create_hdr"),
                     font=("Roboto", 13, "bold"), text_color=COLORS["accent"]), "prof_create_hdr").pack(anchor="w", padx=15, pady=(15, 8))

        # Nombre
        row_name = ctk.CTkFrame(panel_ed, fg_color="transparent")
        row_name.pack(fill="x", padx=15, pady=(0, 8))
        self._t(ctk.CTkLabel(row_name, text=self.lang.get("prof_name_lbl_ui"), text_color=COLORS["text_dim"], width=65), "prof_name_lbl_ui").pack(side="left")
        self.entry_perfil_nombre_v2 = ctk.CTkEntry(row_name, placeholder_text="MI_PERFIL", height=30)
        self.entry_perfil_nombre_v2.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Separador
        self._t(ctk.CTkLabel(panel_ed, text=self.lang.get("prof_add_setting"),
                     text_color=COLORS["text_dim"], font=("Roboto", 11, "bold")), "prof_add_setting").pack(anchor="w", padx=15, pady=(4, 3))

        # Fila categoría + ajuste
        cats_traducidas = []
        self.cat_translation_map = {}
        for cat_key in DATABASE_SETTINGS.keys():
            texto = self.lang.get(cat_key)
            cats_traducidas.append(texto)
            self.cat_translation_map[texto] = cat_key

        row_cats = ctk.CTkFrame(panel_ed, fg_color="transparent")
        row_cats.pack(fill="x", padx=15, pady=2)
        self.combo_categoria = ctk.CTkComboBox(row_cats, values=cats_traducidas, command=self.actualizar_dropdown_settings)
        self.combo_categoria.pack(side="left", fill="x", expand=True)
        self.combo_settings = ctk.CTkComboBox(row_cats, values=[])
        self.combo_settings.pack(side="left", fill="x", expand=True, padx=(5, 0))
        if cats_traducidas: self.actualizar_dropdown_settings(cats_traducidas[0])

        # Fila valor + botón +
        row_val = ctk.CTkFrame(panel_ed, fg_color="transparent")
        row_val.pack(fill="x", padx=15, pady=(3, 8))
        self.entry_setting_value = ctk.CTkEntry(row_val, placeholder_text="Valor", height=30)
        self.entry_setting_value.pack(side="left", fill="x", expand=True)
        btn_agregar = ctk.CTkButton(row_val, text="+ Agregar", width=95, height=30,
                      fg_color=COLORS["success"], text_color="black",
                      command=self.accion_agregar_fila_editable)
        btn_agregar.pack(side="left", padx=(8, 0))

        # Lista de ajustes del perfil actual
        self._t(ctk.CTkLabel(panel_ed, text=self.lang.get("prof_settings_list"),
                     text_color=COLORS["text_dim"], font=("Roboto", 11, "bold")), "prof_settings_list").pack(anchor="w", padx=15, pady=(2, 3))
        self.frame_workbench = ctk.CTkScrollableFrame(panel_ed, fg_color="#151515")
        self.frame_workbench.pack(fill="both", expand=True, padx=15, pady=(0, 8))

        # Footer editor
        footer_ed = ctk.CTkFrame(panel_ed, fg_color="transparent")
        footer_ed.pack(fill="x", padx=15, pady=(0, 15))
        btn_clear = ctk.CTkButton(footer_ed, text=self.lang.get("prof_clear_btn"), width=80, height=32,
                      fg_color="#333", command=self.limpiar_mesa_trabajo)
        btn_clear.pack(side="left")
        self._t(btn_clear, "prof_clear_btn")
        btn_save = ctk.CTkButton(footer_ed, text=self.lang.get("prof_save_full"), height=32,
                      fg_color=COLORS["accent"], text_color="black",
                      command=self.accion_guardar_perfil_v2)
        btn_save.pack(side="right")
        self._t(btn_save, "prof_save_full")

        # ===== PANEL DERECHO: CARDS =====
        panel_cards = ctk.CTkFrame(split, fg_color=COLORS["panel"], corner_radius=10)
        panel_cards.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._t(ctk.CTkLabel(panel_cards, text=self.lang.get("prof_my_profiles"),
                     font=("Roboto", 13, "bold"), text_color=COLORS["text_main"]), "prof_my_profiles").pack(anchor="w", padx=15, pady=(15, 10))

        self.frame_lista_perfiles = ctk.CTkScrollableFrame(panel_cards, fg_color="transparent")
        self.frame_lista_perfiles.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self._refrescar_lista_perfiles()

    def actualizar_dropdown_settings(self, categoria_traducida):
        cat_key = self.cat_translation_map.get(categoria_traducida)
        if not cat_key: return
        ajustes_dict = DATABASE_SETTINGS.get(cat_key, {})
        opciones_traducidas = []
        self.setting_translation_map = {} 
        for ini_key, lang_key in ajustes_dict.items():
            texto_ajuste = self.lang.get(lang_key)
            opciones_traducidas.append(texto_ajuste)
            self.setting_translation_map[texto_ajuste] = ini_key 
        self.combo_settings.configure(values=opciones_traducidas)
        if opciones_traducidas: self.combo_settings.set(opciones_traducidas[0])

    def limpiar_mesa_trabajo(self):
        for w in self.frame_workbench.winfo_children(): w.destroy()
        self.workbench_rows = []
        self.entry_perfil_nombre_v2.delete(0, "end")


    def accion_agregar_fila_editable(self):
        nombre_bonito = self.combo_settings.get()
        valor = self.entry_setting_value.get().strip()
        if not valor: return
        
        clave_real = self.setting_translation_map.get(nombre_bonito)
        if not clave_real: return 
        
        # Verificar si ya existe para no duplicar visualmente (opcional, pero recomendado)
        for row in self.workbench_rows:
            if row["key"] == clave_real:
                # Si existe, actualizamos el valor del entry
                row["entry"].delete(0, "end")
                row["entry"].insert(0, valor)
                return

        self.crear_fila_visual(clave_real, nombre_bonito, valor)
        self.entry_setting_value.delete(0, "end")

    def crear_fila_visual(self, key, display_name, value):
        row_frame = ctk.CTkFrame(self.frame_workbench, fg_color="#222", height=35)
        row_frame.pack(fill="x", pady=2)
        
        # Label (Nombre)
        ctk.CTkLabel(row_frame, text=display_name, anchor="w", width=250).pack(side="left", padx=10)
        
        # Entry (Valor Editable)
        entry = ctk.CTkEntry(row_frame, fg_color="#111", border_color="#444", width=150)
        entry.insert(0, value)
        entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Botón Eliminar
        btn_del = ctk.CTkButton(row_frame, text="X", width=30, fg_color=COLORS["danger"], command=lambda: self.eliminar_fila_visual(row_frame))
        btn_del.pack(side="right", padx=5)
        
        # Guardamos referencia
        self.workbench_rows.append({
            "frame": row_frame,
            "key": key,
            "entry": entry
        })

    def eliminar_fila_visual(self, frame):
        # Eliminar de la lista de rastreo
        self.workbench_rows = [r for r in self.workbench_rows if r["frame"] != frame]
        frame.destroy()

    def _refrescar_lista_perfiles(self):
        if not hasattr(self, 'frame_lista_perfiles'): return
        for w in self.frame_lista_perfiles.winfo_children(): w.destroy()

        if not self.scheduler.perfiles:
            ctk.CTkLabel(self.frame_lista_perfiles,
                         text="No hay perfiles guardados.\nCrea uno en el panel izquierdo.",
                         text_color="gray", justify="center",
                         font=("Roboto", 12)).pack(expand=True, pady=50)
            return

        for nombre, ajustes in self.scheduler.perfiles.items():
            self._crear_card_perfil(nombre, ajustes)

    def _crear_card_perfil(self, nombre, ajustes):
        card = ctk.CTkFrame(self.frame_lista_perfiles, fg_color="#1a1a2e",
                            border_width=1, border_color="#333", corner_radius=8)
        card.pack(fill="x", pady=5, padx=2)

        # Header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 3))
        ctk.CTkLabel(hdr, text=f"⚙  {nombre}", font=("Roboto", 13, "bold"),
                     text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(hdr, text=f"{len(ajustes)} ajuste(s)", font=("Roboto", 10),
                     text_color="gray").pack(side="left", padx=8)

        # Preview (máx 3 ajustes)
        items = list(ajustes.items())
        preview = "\n".join([f"  • {k.split('.')[-1]} = {v}" for k, v in items[:3]])
        if len(items) > 3: preview += f"\n  ... y {len(items)-3} más"
        ctk.CTkLabel(card, text=preview, font=("Consolas", 10), text_color="#777",
                     justify="left", anchor="w").pack(fill="x", padx=12, pady=(0, 8))

        # Botones
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 10))
        btn_apply = ctk.CTkButton(btn_row, text=self.lang.get("prof_apply_btn"), height=28, width=130,
                      fg_color=COLORS["success"], text_color="black",
                      command=lambda n=nombre: self._aplicar_perfil(n))
        btn_apply.pack(side="left", padx=(0, 5))
        self._t(btn_apply, "prof_apply_btn")
        btn_edit = ctk.CTkButton(btn_row, text=self.lang.get("prof_edit_btn"), height=28, width=80,
                      fg_color="#444",
                      command=lambda n=nombre: self._editar_perfil(n))
        btn_edit.pack(side="left", padx=5)
        self._t(btn_edit, "prof_edit_btn")
        ctk.CTkButton(btn_row, text="🗑", height=28, width=35,
                      fg_color=COLORS["danger"],
                      command=lambda n=nombre, c=card: self._eliminar_perfil(n, c)).pack(side="right")

    def _aplicar_perfil(self, nombre):
        self.log_sistema(f"⚡ Aplicando perfil '{nombre}'...")
        threading.Thread(target=self.scheduler.ejecutar_tarea, args=(nombre,), daemon=True).start()

    def _editar_perfil(self, nombre):
        self.limpiar_mesa_trabajo()
        self.entry_perfil_nombre_v2.insert(0, nombre)
        for key, value in self.scheduler.perfiles[nombre].items():
            nombre_bonito = key
            for cat, items in DATABASE_SETTINGS.items():
                if key in items:
                    nombre_bonito = self.lang.get(items[key])
                    break
            self.crear_fila_visual(key, nombre_bonito, value)

    def _eliminar_perfil(self, nombre, card):
        if self.scheduler.borrar_perfil(nombre):
            card.destroy()
            if hasattr(self, 'combo_perfiles'):
                vals = ["RESTART", "BACKUP"] + list(self.scheduler.perfiles.keys())
                self.combo_perfiles.configure(values=vals)
            self.log_sistema(f"🗑 Perfil '{nombre}' eliminado.")

    def accion_guardar_perfil_v2(self):
        nombre = self.entry_perfil_nombre_v2.get().upper().strip()
        if not nombre:
            self.log_sistema("❌ Escribe un nombre para el perfil.")
            return
        if not self.workbench_rows:
            self.log_sistema("❌ Agrega al menos un ajuste antes de guardar.")
            return

        contenido = {row["key"]: row["entry"].get() for row in self.workbench_rows}
        self.scheduler.perfiles[nombre] = contenido
        self.scheduler.guardar_perfiles()

        # Actualizar combo de Tasks si existe
        if hasattr(self, 'combo_perfiles'):
            vals = ["RESTART", "BACKUP"] + list(self.scheduler.perfiles.keys())
            self.combo_perfiles.configure(values=vals)

        self._refrescar_lista_perfiles()
        self.limpiar_mesa_trabajo()
        self.log_sistema(f"✅ Perfil '{nombre}' guardado con {len(contenido)} ajuste(s).")


    def construir_tasks(self):
        for w in self.frame_tasks.winfo_children(): w.destroy()
        self._t(ctk.CTkLabel(self.frame_tasks, text=self.lang.get("task_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]), "task_title").pack(pady=20, padx=30, anchor="w")
        
        frame_prog = ctk.CTkFrame(self.frame_tasks, fg_color=COLORS["panel"]); frame_prog.pack(fill="x", padx=20, pady=10)
        self._t(ctk.CTkLabel(frame_prog, text=self.lang.get("task_new"), font=("Roboto", 14, "bold"), text_color=COLORS["accent"]), "task_new").pack(anchor="w", padx=15, pady=10)
        
        # Fila de Hora y Perfil
        row_clock = ctk.CTkFrame(frame_prog, fg_color="transparent"); row_clock.pack(fill="x", padx=10, pady=5)
        self._t(ctk.CTkLabel(row_clock, text=self.lang.get("task_at")), "task_at").pack(side="left", padx=5)
        self.entry_hora = ctk.CTkEntry(row_clock, width=80, placeholder_text="HH:MM"); self.entry_hora.pack(side="left", padx=5)
        
        self._t(ctk.CTkLabel(row_clock, text=self.lang.get("task_run")), "task_run").pack(side="left", padx=5)
        opciones = ["RESTART", "BACKUP"] + list(self.scheduler.perfiles.keys())
        self.combo_perfiles = ctk.CTkComboBox(row_clock, values=opciones, width=200); self.combo_perfiles.pack(side="left", padx=5)
        
        btn_del_profile = ctk.CTkButton(row_clock, text=self.lang.get("task_del_btn"), width=100, fg_color=COLORS["danger"], command=self.accion_borrar_perfil_seleccionado)
        btn_del_profile.pack(side="left", padx=15)
        self._t(btn_del_profile, "task_del_btn")
        
        btn_active = ctk.CTkButton(row_clock, text=self.lang.get("task_active_btn"), width=140, command=self.accion_programar)
        btn_active.pack(side="right", padx=15)
        self._t(btn_active, "task_active_btn")

        # Fila de Días de la Semana
        row_days = ctk.CTkFrame(frame_prog, fg_color="transparent"); row_days.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(row_days, text="Días:", font=("Roboto", 12)).pack(side="left", padx=5)
        
        self.chk_dias_vars = {}
        dias_semana  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dias_keys    = ["day_Monday", "day_Tuesday", "day_Wednesday", "day_Thursday", "day_Friday", "day_Saturday", "day_Sunday"]
        dias_labels  = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        
        for i, dia in enumerate(dias_semana):
            var = ctk.BooleanVar(value=True)
            self.chk_dias_vars[dia] = var
            # Usar traducción completa del día si existe, si no usar abreviación
            dia_texto = self.lang.get(dias_keys[i])
            if dias_keys[i] in dia_texto:   # clave no encontrada → usar abreviación
                dia_texto = dias_labels[i]
            chk = ctk.CTkCheckBox(row_days, text=dia_texto, variable=var, width=50, checkbox_width=20, checkbox_height=20)
            chk.pack(side="left", padx=5)
            self._t(chk, dias_keys[i])

        self._t(ctk.CTkLabel(self.frame_tasks, text=self.lang.get("task_list_title"), font=("Roboto", 14)), "task_list_title").pack(pady=(20,5), padx=30, anchor="w")
        self.lista_tareas = ctk.CTkScrollableFrame(self.frame_tasks, fg_color="#111", height=300); self.lista_tareas.pack(fill="both", expand=True, padx=20, pady=5)
        for t in self.scheduler.tareas: self.dibujar_tarea_en_lista(t)

    def accion_borrar_perfil_seleccionado(self):
        perfil_a_borrar = self.combo_perfiles.get()
        if perfil_a_borrar in ["RESTART", "BACKUP"]:
            self.log_sistema("❌ No puedes eliminar funciones del sistema.")
            return
        if self.scheduler.borrar_perfil(perfil_a_borrar):
            nuevos_valores = ["RESTART", "BACKUP"] + list(self.scheduler.perfiles.keys())
            self.combo_perfiles.configure(values=nuevos_valores)
            self.combo_perfiles.set(nuevos_valores[0])
            self._refrescar_lista_perfiles()
            self.log_sistema(f"{self.lang.get('success_profile_deleted')} ({perfil_a_borrar})")

    def accion_programar(self):
        hora = self.entry_hora.get().strip(); perfil = self.combo_perfiles.get()
        if len(hora) == 4 and hora.isdigit(): hora = f"{hora[:2]}:{hora[2:]}"
        if ":" not in hora: self.log_sistema("❌ Error: Formato de hora inválido. Usa HH:MM"); return
        
        # Obtener días seleccionados
        dias_seleccionados = [dia for dia, var in self.chk_dias_vars.items() if var.get()]
        if not dias_seleccionados:
            self.log_sistema("❌ Error: Debes seleccionar al menos un día.")
            return

        tarea = self.scheduler.programar_tarea(hora, perfil, dias_seleccionados)
        if tarea: 
            self.dibujar_tarea_en_lista(tarea)
            self.log_sistema(f"{self.lang.get('success_task_saved')} {perfil} @ {hora}")
            self.entry_hora.delete(0, "end")

    def dibujar_tarea_en_lista(self, tarea):
        row = ctk.CTkFrame(self.lista_tareas, fg_color=COLORS["panel"]); row.pack(fill="x", pady=2)
        
        # Hora
        ctk.CTkLabel(row, text=f"⏰ {tarea['hora']}", font=("Consolas", 14, "bold"), text_color="#E0A800", width=60).pack(side="left", padx=5)
        
        # Perfil
        ctk.CTkLabel(row, text=f"PERFIL: {tarea['perfil']}", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        
        # Días
        dias_str = "Todos"
        if "dias" in tarea and tarea["dias"]:
            # Mapeo rápido para mostrar en español corto
            mapa_dias = {
                "monday": "Lun", "tuesday": "Mar", "wednesday": "Mie", "thursday": "Jue", 
                "friday": "Vie", "saturday": "Sab", "sunday": "Dom"
            }
            lista_corta = [mapa_dias.get(d.lower(), d[:3]) for d in tarea["dias"]]
            if len(lista_corta) == 7: dias_str = "Todos"
            else: dias_str = ", ".join(lista_corta)
            
        ctk.CTkLabel(row, text=f"({dias_str})", font=("Roboto", 11), text_color="gray").pack(side="left", padx=5)
        
        # Botón Borrar
        ctk.CTkButton(row, text="🗑", width=30, fg_color=COLORS["danger"], command=lambda: self.borrar_tarea_visual(row, tarea['id'])).pack(side="right", padx=10, pady=5)

    def borrar_tarea_visual(self, frame, job_id): self.scheduler.eliminar_tarea(job_id); frame.destroy()
    
    def construir_users(self):
        for w in self.frame_users.winfo_children(): w.destroy()
        self._t(ctk.CTkLabel(self.frame_users, text=self.lang.get("user_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]), "user_title").pack(pady=20, padx=30, anchor="w")
        panel_input = ctk.CTkFrame(self.frame_users, fg_color=COLORS["panel"]); panel_input.pack(fill="x", padx=20, pady=10)
        row1 = ctk.CTkFrame(panel_input, fg_color="transparent"); row1.pack(fill="x", padx=10, pady=5)
        self._t(ctk.CTkLabel(row1, text=self.lang.get("user_steamid")), "user_steamid").pack(side="left", padx=5)
        self.entry_user_id = ctk.CTkEntry(row1, width=200, placeholder_text="76561198..."); self.entry_user_id.pack(side="left", padx=5)
        self._t(ctk.CTkLabel(row1, text=self.lang.get("user_hours")), "user_hours").pack(side="left", padx=5)
        self.entry_user_hours = ctk.CTkEntry(row1, width=80); self.entry_user_hours.insert(0, "-1"); self.entry_user_hours.pack(side="left", padx=5)
        row2 = ctk.CTkFrame(panel_input, fg_color="transparent"); row2.pack(fill="x", padx=10, pady=10)
        self._t(ctk.CTkLabel(row2, text=self.lang.get("user_notes")), "user_notes").pack(side="left", padx=5)
        self.entry_user_notes = ctk.CTkEntry(row2, width=300, placeholder_text=self.lang.get("placeholder_notes")); self.entry_user_notes.pack(side="left", padx=5)
        btn_ban = ctk.CTkButton(row2, text=self.lang.get("btn_add_ban"), fg_color=COLORS["danger"], command=lambda: self.accion_agregar_usuario("BAN")); btn_ban.pack(side="right", padx=10)
        self._t(btn_ban, "btn_add_ban")
        btn_vip = ctk.CTkButton(row2, text=self.lang.get("btn_add_vip"), fg_color="#FFD700", text_color="black", hover_color="#C6A700", command=lambda: self.accion_agregar_usuario("VIP")); btn_vip.pack(side="right", padx=10)
        self._t(btn_vip, "btn_add_vip")
        
        # Botón de Recarga Manual
        btn_reload = ctk.CTkButton(row2, text="🔄 Sincronizar TXT", width=120, fg_color="#444", command=self.accion_sincronizar_usuarios); btn_reload.pack(side="right", padx=10)
        
        panel_listas = ctk.CTkFrame(self.frame_users, fg_color="transparent"); panel_listas.pack(fill="both", expand=True, padx=20, pady=10)
        frame_bans = ctk.CTkFrame(panel_listas, fg_color=COLORS["panel"]); frame_bans.pack(side="left", fill="both", expand=True, padx=(0,5))
        self._t(ctk.CTkLabel(frame_bans, text=self.lang.get("list_active_bans"), font=("Roboto", 12, "bold"), text_color=COLORS["danger"]), "list_active_bans").pack(pady=5)
        self.lista_visual_bans = ctk.CTkScrollableFrame(frame_bans, fg_color="transparent"); self.lista_visual_bans.pack(fill="both", expand=True, padx=5, pady=5)
        frame_vips = ctk.CTkFrame(panel_listas, fg_color=COLORS["panel"]); frame_vips.pack(side="right", fill="both", expand=True, padx=(5,0))
        self._t(ctk.CTkLabel(frame_vips, text=self.lang.get("list_active_vips"), font=("Roboto", 12, "bold"), text_color="#FFD700"), "list_active_vips").pack(pady=5)
        self.lista_visual_vips = ctk.CTkScrollableFrame(frame_vips, fg_color="transparent"); self.lista_visual_vips.pack(fill="both", expand=True, padx=5, pady=5)
        self.refrescar_lista_usuarios()

        # ── Panel Alt-Account / IP Duplicada ──────────────────────────────────
        self._construir_panel_ip_ban()

    def accion_agregar_usuario(self, tipo):
        steam_id = self.entry_user_id.get().strip()
        try: horas = int(self.entry_user_hours.get().strip())
        except: self.log_sistema(self.lang.get("error_hours_int")); return
        notas = self.entry_user_notes.get().strip()
        if len(steam_id) < 10: self.log_sistema(self.lang.get("error_steam_id")); return
        self.users.agregar_usuario(tipo, steam_id, horas, notas); self.entry_user_id.delete(0, "end"); self.entry_user_notes.delete(0, "end"); self.refrescar_lista_usuarios()

    def accion_sincronizar_usuarios(self):
        self.users.sincronizar_con_archivos()
        self.refrescar_lista_usuarios()
        self.log_sistema("🔄 Sincronización manual de usuarios completada.")

    def refrescar_lista_usuarios(self):
        for w in self.lista_visual_bans.winfo_children(): w.destroy()
        for w in self.lista_visual_vips.winfo_children(): w.destroy()
        self.users.db = self.users.cargar_db()
        for u in self.users.db:
            target_list = self.lista_visual_bans if u["tipo"] == "BAN" else self.lista_visual_vips
            color_borde = COLORS["danger"] if u["tipo"] == "BAN" else "#FFD700"
            card = ctk.CTkFrame(target_list, fg_color="#1a1a1a", border_width=1, border_color=color_borde); card.pack(fill="x", pady=2, padx=2)
            info_text = f"{u['id']}\nExpira: {u['expira']}"
            if u['notas']: info_text += f"\nNote: {u['notas']}"
            lbl = ctk.CTkLabel(card, text=info_text, font=("Consolas", 11), justify="left", anchor="w"); lbl.pack(side="left", padx=5, pady=5)
            btn_del = ctk.CTkButton(card, text="X", width=30, height=20, fg_color="#333", hover_color=COLORS["danger"], command=lambda k=u['tipo'], i=u['id']: self.borrar_usuario_ui(k, i)); btn_del.pack(side="right", padx=5)

    def borrar_usuario_ui(self, tipo, steam_id):
        self.users.remover_usuario(tipo, steam_id); self.refrescar_lista_usuarios()

    # ─────────────────────────────────────────────────────────────────────────
    # ALT-ACCOUNT DETECTION — Handler y UI
    # ─────────────────────────────────────────────────────────────────────────

    def _on_player_join_handler(self, steam_id: str, ip: str):
        """
        Llamado por SCUMLogWatcher en cada autenticacion detectada en el log.

        LOGICA:
          1. Registra la IP del jugador.
          2. Si Auto-Ban esta ON: busca si alguna OTRA cuenta ya uso esa misma IP.
             Si hay coincidencia → la cuenta nueva es una alt → se banea automaticamente.
          3. IP en whitelist = familia/misma casa → no se banea nunca.
        """
        nombre = self.ip_ban_mgr.registry.get(steam_id, {}).get("nombre", "")

        # 1. Registrar la conexion ANTES de verificar (para guardar el nombre actual)
        self.ip_ban_mgr.registrar_conexion(steam_id, ip, nombre)

        if not self._ip_ban_activo:
            return

        # 2. Buscar si esta IP ya fue usada por CUALQUIER otra cuenta
        conflictos = self.ip_ban_mgr.buscar_duplicados_ip(steam_id, ip)
        if not conflictos:
            return

        # 3. Es una alt account → banear y registrar la deteccion
        nombre_nuevo = self.ip_ban_mgr.registry.get(steam_id, {}).get("nombre", steam_id)
        self.ip_ban_mgr.registrar_deteccion(steam_id, nombre_nuevo, ip, conflictos)

        ya_baneado = any(u["id"] == steam_id and u["tipo"] == "BAN" for u in self.users.db)
        if not ya_baneado:
            for c in conflictos:
                motivo = (f"Auto-ban: misma IP ({c['ip']}) que "
                          f"{c['nombre_original']} [{c['steam_id_original']}]")
                self.users.agregar_usuario("BAN", steam_id, -1, motivo)
                self.log_sistema(
                    f"🚨 ALT ACCOUNT: '{nombre_nuevo}' ({steam_id}) "
                    f"comparte IP {c['ip']} con '{c['nombre_original']}' "
                    f"→ BANEADO AUTOMATICAMENTE"
                )
                break  # Un ban es suficiente

        # Actualizar UI desde hilo principal
        try:
            self.after(0, self.refrescar_lista_usuarios)
            self.after(0, self._refrescar_panel_ip_ban)
        except Exception:
            pass

    def _construir_panel_ip_ban(self):
        """Construye el panel de detección de alt-accounts en el frame de usuarios."""
        panel = ctk.CTkFrame(self.frame_users, fg_color=COLORS["panel"], corner_radius=10)
        panel.pack(fill="x", padx=20, pady=(5, 15))
        self._ip_ban_panel = panel

        # ── Encabezado ──────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            hdr, text="🛡️  Detección de Alt Accounts (IP Duplicada)",
            font=("Roboto", 13, "bold"), text_color=COLORS["text_main"]
        ).pack(side="left")

        # Switch auto-ban
        self._switch_ip_ban = ctk.CTkSwitch(
            hdr, text="Auto-Ban activado",
            font=("Roboto", 12),
            progress_color=COLORS["danger"],
            command=self._toggle_ip_ban
        )
        self._switch_ip_ban.pack(side="right", padx=10)
        if self._ip_ban_activo:
            self._switch_ip_ban.select()

        # ── Stats y controles ────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(panel, fg_color="transparent")
        ctrl.pack(fill="x", padx=12, pady=2)

        self._lbl_ip_stats = ctk.CTkLabel(
            ctrl, text="Cargando estadísticas...",
            font=("Roboto", 11), text_color=COLORS.get("text_secondary", "#888")
        )
        self._lbl_ip_stats.pack(side="left")

        ctk.CTkButton(
            ctrl, text="🗑️ Limpiar Registro", width=130, height=26,
            fg_color="#444", hover_color="#666",
            command=self._accion_limpiar_registro_ip
        ).pack(side="right", padx=4)

        # ── Whitelist de IPs ─────────────────────────────────────────────────
        wl_frame = ctk.CTkFrame(panel, fg_color="#1a1a1a", corner_radius=6)
        wl_frame.pack(fill="x", padx=12, pady=(6, 2))

        ctk.CTkLabel(
            wl_frame,
            text="🏠 IPs en Whitelist (misma casa/familia — nunca se auto-banean):",
            font=("Roboto", 11, "bold"), text_color="#FFD700"
        ).pack(anchor="w", padx=8, pady=(6, 2))

        wl_input_row = ctk.CTkFrame(wl_frame, fg_color="transparent")
        wl_input_row.pack(fill="x", padx=8, pady=4)

        self._entry_ip_whitelist = ctk.CTkEntry(
            wl_input_row, width=160, placeholder_text="1.2.3.4"
        )
        self._entry_ip_whitelist.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            wl_input_row, text="+ Agregar", width=90, height=28,
            fg_color="#2a6a2a", hover_color="#3a9a3a",
            command=self._accion_agregar_ip_whitelist
        ).pack(side="left")

        self._frame_whitelist_list = ctk.CTkFrame(wl_frame, fg_color="transparent")
        self._frame_whitelist_list.pack(fill="x", padx=8, pady=(0, 6))

        # ── Detecciones recientes ─────────────────────────────────────────────
        ctk.CTkLabel(
            panel, text="🚨 Detecciones recientes:",
            font=("Roboto", 11, "bold"), text_color=COLORS["danger"]
        ).pack(anchor="w", padx=12, pady=(8, 2))

        self._frame_detecciones = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", height=120
        )
        self._frame_detecciones.pack(fill="x", padx=12, pady=(0, 10))

        self._refrescar_panel_ip_ban()

    def _toggle_ip_ban(self):
        self._ip_ban_activo = bool(self._switch_ip_ban.get())
        estado = "ACTIVADO" if self._ip_ban_activo else "DESACTIVADO"
        self.log_sistema(f"🛡️ Auto-Ban por IP duplicada: {estado}")
        # Persistir en gui_settings.json
        try:
            datos = {}
            if os.path.exists(self.gui_settings_file):
                with open(self.gui_settings_file, 'r') as f:
                    datos = json.load(f)
            datos["ip_ban_activo"] = self._ip_ban_activo
            with open(self.gui_settings_file, 'w') as f:
                json.dump(datos, f)
        except Exception:
            pass

    def _refrescar_panel_ip_ban(self):
        """Actualiza estadísticas, whitelist y detecciones en el panel."""
        try:
            stats = self.ip_ban_mgr.get_stats()
            self._lbl_ip_stats.configure(
                text=(f"📊  {stats['jugadores']} jugadores registrados · "
                      f"{stats['ips_registradas']} IPs · "
                      f"{stats['detecciones_recientes']} detecciones · "
                      f"{stats['ips_whitelist']} IPs en whitelist")
            )

            # ── Whitelist ────────────────────────────────────────────────
            for w in self._frame_whitelist_list.winfo_children():
                w.destroy()
            for ip in self.ip_ban_mgr.ip_whitelist:
                row = ctk.CTkFrame(self._frame_whitelist_list, fg_color="transparent")
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(
                    row, text=f"✅ {ip}", font=("Consolas", 11),
                    text_color="#88cc88"
                ).pack(side="left", padx=4)
                ctk.CTkButton(
                    row, text="Quitar", width=60, height=22,
                    fg_color="#555", hover_color=COLORS["danger"],
                    command=lambda i=ip: self._accion_quitar_ip_whitelist(i)
                ).pack(side="right", padx=4)

            # ── Detecciones ──────────────────────────────────────────────
            for w in self._frame_detecciones.winfo_children():
                w.destroy()

            detecciones = self.ip_ban_mgr.get_detecciones()
            if not detecciones:
                ctk.CTkLabel(
                    self._frame_detecciones,
                    text="Sin detecciones aún.",
                    font=("Roboto", 11), text_color="#555"
                ).pack(anchor="w", padx=4)
            else:
                for d in detecciones[:20]:
                    card = ctk.CTkFrame(
                        self._frame_detecciones, fg_color="#1a0a0a",
                        border_width=1, border_color=COLORS["danger"], corner_radius=5
                    )
                    card.pack(fill="x", pady=2)

                    ctk.CTkLabel(
                        card,
                        text=(f"🚨 [{d['ts']}]  "
                              f"{d.get('nombre_nuevo') or d.get('steam_id_nuevo','?')} "
                              f"({d.get('steam_id_nuevo','?')})\n"
                              f"    misma IP que: "
                              f"{d.get('nombre_original') or d.get('steam_id_original','?')} "
                              f"— IP: {d['ip']}"),
                        font=("Consolas", 10), justify="left", anchor="w",
                        text_color="#ffaaaa"
                    ).pack(side="left", padx=6, pady=4)


                    btn_row = ctk.CTkFrame(card, fg_color="transparent")
                    btn_row.pack(side="right", padx=4)

                    # Botón desbanear (quitar ban)
                    ctk.CTkButton(
                        btn_row, text="🔓 Desbanear", width=90, height=24,
                        fg_color="#2a4a2a", hover_color="#3a8a3a",
                        command=lambda sid=d['steam_id_nuevo']: self._accion_desbanear_ip(sid)
                    ).pack(pady=2)

                    # Botón agregar IP a whitelist
                    ctk.CTkButton(
                        btn_row, text="🏠 Whitelist IP", width=90, height=24,
                        fg_color="#4a4a2a", hover_color="#8a8a3a",
                        command=lambda ip=d['ip']: self._accion_agregar_ip_whitelist(ip)
                    ).pack(pady=2)

        except Exception as e:
            self.log_sistema(f"⚠️ Error refrescando panel IP: {e}")

    def _accion_agregar_ip_whitelist(self, ip_param=None):
        ip = ip_param or self._entry_ip_whitelist.get().strip()
        if not ip:
            self.log_sistema("⚠️ Escribe una IP válida.")
            return
        self.ip_ban_mgr.agregar_ip_whitelist(ip)
        if not ip_param:
            self._entry_ip_whitelist.delete(0, "end")
        self._refrescar_panel_ip_ban()

    def _accion_quitar_ip_whitelist(self, ip: str):
        self.ip_ban_mgr.quitar_ip_whitelist(ip)
        self._refrescar_panel_ip_ban()

    def _accion_desbanear_ip(self, steam_id: str):
        self.users.remover_usuario("BAN", steam_id)
        self.refrescar_lista_usuarios()
        self.log_sistema(f"🔓 Desbaneado manualmente: {steam_id}")
        self._refrescar_panel_ip_ban()

    def _accion_limpiar_registro_ip(self):
        self.ip_ban_mgr.limpiar_registro()
        self._refrescar_panel_ip_ban()

    # --- NUEVA ESTRUCTURA DE ADMINS (EDITOR DIRECTO) ---
    def construir_admins(self):

        for w in self.frame_admins.winfo_children(): w.destroy()
        
        # Título
        ctk.CTkLabel(self.frame_admins, text=self.lang.get("admin_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=(20, 10), padx=30, anchor="w")

        # Texto Traducciones
        txt_save = self.lang.get("btn_save_direct")
        if "btn_save_direct" in txt_save: txt_save = "GUARDAR / SAVE"
        
        lbl_main = self.lang.get("admin_header_main")
        if "admin_header_main" in lbl_main: lbl_main = "AdminUsers.ini (God/Regular)"

        lbl_set = self.lang.get("admin_header_settings")
        if "admin_header_settings" in lbl_set: lbl_set = "ServerSettingsAdminUsers.ini (Permissions)"

        # --- BLOQUE 1: AdminUsers.ini ---
        frame_main = ctk.CTkFrame(self.frame_admins, fg_color="transparent")
        frame_main.pack(fill="both", expand=True, padx=20, pady=5)
        
        header_main = ctk.CTkFrame(frame_main, fg_color="transparent")
        header_main.pack(fill="x")
        ctk.CTkLabel(header_main, text=lbl_main, font=("Roboto", 14, "bold")).pack(side="left")
        ctk.CTkButton(header_main, text=txt_save, width=120, fg_color=COLORS["success"], text_color="black", command=self.accion_guardar_main_manual).pack(side="right")
        
        self.txt_admin_main = ctk.CTkTextbox(frame_main, font=("Consolas", 12), fg_color="#111", activate_scrollbars=True)
        self.txt_admin_main.pack(fill="both", expand=True, pady=(5, 10))

        # --- BLOQUE 2: ServerSettingsAdminUsers.ini ---
        frame_sets = ctk.CTkFrame(self.frame_admins, fg_color="transparent")
        frame_sets.pack(fill="both", expand=True, padx=20, pady=5)
        
        header_sets = ctk.CTkFrame(frame_sets, fg_color="transparent")
        header_sets.pack(fill="x")
        ctk.CTkLabel(header_sets, text=lbl_set, font=("Roboto", 14, "bold")).pack(side="left")
        ctk.CTkButton(header_sets, text=txt_save, width=120, fg_color=COLORS["success"], text_color="black", command=self.accion_guardar_settings_manual).pack(side="right")
        
        self.txt_admin_settings = ctk.CTkTextbox(frame_sets, font=("Consolas", 12), fg_color="#111", activate_scrollbars=True)
        self.txt_admin_settings.pack(fill="both", expand=True, pady=(5, 10))

        self.txt_admin_settings.pack(fill="both", expand=True, pady=(5, 10))

        # --- BLOQUE 3: SUPER ADMIN (INYECCIÓN SQL) ---
        frame_super = ctk.CTkFrame(self.frame_admins, fg_color=COLORS["panel"], border_width=1, border_color=COLORS["danger"])
        frame_super.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame_super, text="Gestión de Usuario Elevado (Super Admin)", font=("Roboto", 14, "bold"), text_color=COLORS["danger"]).pack(pady=(10, 5))
        ctk.CTkLabel(frame_super, text="⚠ ADVERTENCIA: Esta operación requiere manipular la base de datos. El servidor debe estar APAGADO.", text_color="#FFCC00", font=("Roboto", 11)).pack(pady=(0, 10))
        
        row_sa = ctk.CTkFrame(frame_super, fg_color="transparent")
        row_sa.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(row_sa, text="Steam64 ID:").pack(side="left", padx=5)
        self.entry_super_admin_id = ctk.CTkEntry(row_sa, width=200, placeholder_text="7656119...")
        self.entry_super_admin_id.pack(side="left", padx=5)
        
        ctk.CTkButton(row_sa, text="Inyectar Privilegios", fg_color=COLORS["danger"], hover_color="#8B0000", command=self.accion_inyectar_super_admin).pack(side="left", padx=15)

        # Cargar contenido inicial
        self.refrescar_listas_admins()

    def refrescar_listas_admins(self):
        # Cargar contenido del disco a las cajas de texto
        cont_main = self.admins.leer_main()
        self.txt_admin_main.delete("0.0", "end")
        self.txt_admin_main.insert("0.0", cont_main)
        
        cont_sets = self.admins.leer_settings()
        self.txt_admin_settings.delete("0.0", "end")
        self.txt_admin_settings.insert("0.0", cont_sets)

    def accion_guardar_main_manual(self):
        contenido = self.txt_admin_main.get("0.0", "end")
        if self.admins.guardar_texto_main(contenido):
            self.refrescar_listas_admins()

    def accion_guardar_settings_manual(self):
        contenido = self.txt_admin_settings.get("0.0", "end")
        if self.admins.guardar_texto_settings(contenido):
             self.refrescar_listas_admins()

    def accion_inyectar_super_admin(self):
        steam_id = self.entry_super_admin_id.get().strip()
        if not steam_id:
            self.log_sistema("❌ Error: Debes ingresar un SteamID.")
            return
        
        # Validar formato básico (números)
        if not steam_id.isdigit() or len(steam_id) < 10:
            self.log_sistema("❌ Error: SteamID inválido (debe ser numérico y largo).")
            return

        # Confirmación extra
        if not messagebox.askyesno("Confirmar Inyección", f"¿Estás seguro de inyectar al usuario {steam_id} como Super Admin?\n\nEsto modificará la base de datos SCUM.db."):
            return

        # Ejecutar
        success, code = self.db_manager.inject_super_admin(steam_id)
        
        if success:
            if code == "SUCCESS":
                messagebox.showinfo("Éxito", f"Usuario {steam_id} añadido correctamente como Super Admin.\nYa puedes iniciar el servidor.")
            elif code == "ALREADY_EXISTS":
                messagebox.showinfo("Aviso", f"El usuario {steam_id} ya era Super Admin.")
            self.entry_super_admin_id.delete(0, "end")
        else:
            if code == "SERVER_RUNNING":
                messagebox.showerror("Error Crítico", "¡PELIGRO! El servidor está CORRIENDO.\n\nDebes detener el servidor antes de tocar la base de datos para evitar corrupción.")
            elif code == "DB_NOT_FOUND":
                messagebox.showerror("Error", "No se encontró el archivo SCUM.db.\n¿El servidor se ha iniciado al menos una vez?")
            else:
                messagebox.showerror("Error", f"Ocurrió un error al inyectar: {code}")

    def construir_ini_editor(self):
        for w in self.frame_ini_editor.winfo_children(): w.destroy()
        panel_top = ctk.CTkFrame(self.frame_ini_editor, fg_color="transparent"); panel_top.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(panel_top, text=self.lang.get("ini_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(side="left")
        btn_save = ctk.CTkButton(panel_top, text=self.lang.get("ini_save"), fg_color=COLORS["success"], text_color="black", command=self.accion_guardar_ini); btn_save.pack(side="right", padx=5)
        btn_reload = ctk.CTkButton(panel_top, text=self.lang.get("ini_reload"), fg_color=COLORS["accent"], text_color="black", command=self.accion_cargar_ini); btn_reload.pack(side="right", padx=5)
        ctk.CTkLabel(self.frame_ini_editor, text=self.lang.get("ini_warn"), text_color="#FFCC00").pack(padx=20, anchor="w")
        self.txt_ini = ctk.CTkTextbox(self.frame_ini_editor, font=("Consolas", 12), fg_color="#1a1a1a", text_color="#CCCCCC", wrap="none"); self.txt_ini.pack(fill="both", expand=True, padx=20, pady=10)
    def accion_cargar_ini(self):
        path = self.editor.config_path
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f: contenido = f.read()
                self.txt_ini.delete("0.0", "end"); self.txt_ini.insert("0.0", contenido); self.log_sistema(self.lang.get("log_ini_loaded"))
            except Exception as e: self.log_sistema(f"{self.lang.get('error_ini_read')} {e}")
        else: self.log_sistema(self.lang.get("error_ini_not_found"))
    def accion_guardar_ini(self):
        path = self.editor.config_path
        contenido = self.txt_ini.get("0.0", "end")
        try:
            with open(path, 'w', encoding='utf-8') as f: f.write(contenido)
            self.log_sistema(self.lang.get("log_ini_saved"))
        except Exception as e: self.log_sistema(f"{self.lang.get('error_ini_save')} {e}")


    def construir_raid_editor(self):
        for w in self.frame_raid.winfo_children(): w.destroy()
        
        # Header
        ctk.CTkLabel(self.frame_raid, text=self.lang.get("raid_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=20, padx=30, anchor="w")
        
        # Controls
        panel_controls = ctk.CTkFrame(self.frame_raid, fg_color=COLORS["panel"])
        panel_controls.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(panel_controls, text=self.lang.get("raid_reload"), fg_color=COLORS["accent"], text_color="black", command=self.cargar_raid_times).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(panel_controls, text=self.lang.get("raid_save"), fg_color=COLORS["success"], text_color="black", command=self.guardar_raid_times).pack(side="left", padx=10, pady=10)

        # List
        self.scroll_raid = ctk.CTkScrollableFrame(self.frame_raid, fg_color="transparent")
        self.scroll_raid.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.raid_rows = {} # Key: DayName, Value: { widgets... }
        self.cargar_raid_times()

    def cargar_raid_times(self):
        for w in self.scroll_raid.winfo_children(): w.destroy()
        self.raid_rows = {}
        
        # Load normalized data: { "Monday": { "active": True, ... }, ... }
        data = self.raid_editor.load_raid_times()
        
        ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day in ordered_days:
            day_data = data.get(day, {"active": False, "time": "00:00-00:00", "start-announcement-time": "30", "end-announcement-time": "30"})
            self.crear_fila_raid_dia(day, day_data)

    def crear_fila_raid_dia(self, day_name, item_data):
        row = ctk.CTkFrame(self.scroll_raid, fg_color="#222")
        row.pack(fill="x", pady=5)
        
        # Switch Active
        is_active = item_data.get("active", False)
        switch_var = ctk.IntVar(value=1 if is_active else 0)
        
        # Translate day name
        display_day = self.lang.get(f"day_{day_name}")
        if not display_day or "day_" in display_day: display_day = day_name

        switch = ctk.CTkSwitch(row, text=display_day, variable=switch_var, font=("Roboto", 12, "bold"), width=150, command=lambda: self.toggle_raid_row(day_name))
        switch.pack(side="left", padx=10)
        
        # Container for inputs (to hide/show)
        input_frame = ctk.CTkFrame(row, fg_color="transparent")
        input_frame.pack(side="left", fill="x", expand=True)
        
        # Time
        ctk.CTkLabel(input_frame, text=self.lang.get("raid_time"), text_color="gray", font=("Roboto", 10)).pack(side="left", padx=(10, 2))
        entry_time = ctk.CTkEntry(input_frame, width=100)
        entry_time.insert(0, item_data.get("time", "00:00-00:00"))
        entry_time.pack(side="left", padx=5)
        
        # Start Announce
        ctk.CTkLabel(input_frame, text=self.lang.get("raid_start_ann"), text_color="gray", font=("Roboto", 10)).pack(side="left", padx=(10, 2))
        entry_start = ctk.CTkEntry(input_frame, width=50)
        entry_start.insert(0, item_data.get("start-announcement-time", "30"))
        entry_start.pack(side="left", padx=5)
    
        # End Announce
        ctk.CTkLabel(input_frame, text=self.lang.get("raid_end_ann"), text_color="gray", font=("Roboto", 10)).pack(side="left", padx=(10, 2))
        entry_end = ctk.CTkEntry(input_frame, width=50)
        entry_end.insert(0, item_data.get("end-announcement-time", "30"))
        entry_end.pack(side="left", padx=5)
        
        self.raid_rows[day_name] = {
            "switch": switch_var,
            "input_frame": input_frame,
            "time": entry_time,
            "start": entry_start,
            "end": entry_end
        }
        
        # Initial state
        self.toggle_raid_row(day_name)

    def toggle_raid_row(self, day_name):
        row_data = self.raid_rows.get(day_name)
        if not row_data: return
        
        if row_data["switch"].get() == 1:
            # Show inputs
            for child in row_data["input_frame"].winfo_children():
                try: child.configure(state="normal")
                except: pass
        else:
            # Disable inputs visualy
             for child in row_data["input_frame"].winfo_children():
                try: child.configure(state="disabled")
                except: pass
        
    def agregar_raid_time_ui(self):
        pass # Not used in 7-day mode
        
    def guardar_raid_times(self):
        data_to_save = {}
        for day, widgets in self.raid_rows.items():
            is_active = (widgets["switch"].get() == 1)
            data_to_save[day] = {
                "active": is_active,
                "time": widgets["time"].get(),
                "start-announcement-time": widgets["start"].get(),
                "end-announcement-time": widgets["end"].get()
            }
            
        self.raid_editor.save_raid_times(data_to_save)

    def construir_logs(self):
        for w in self.frame_logs.winfo_children(): w.destroy()
        ctk.CTkLabel(self.frame_logs, text=self.lang.get("menu_logs"), font=("Roboto", 20, "bold"), text_color=COLORS["text_main"]).pack(pady=(20, 10), padx=20, anchor="w")
        self.big_console_tab = ctk.CTkTextbox(self.frame_logs, fg_color="#000000", text_color="#00FF00", font=("Consolas", 12), activate_scrollbars=True)
        self.big_console_tab.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.big_console_tab.insert("0.0", f"{self.lang.get('log_monitor_started')}\n")

    def iniciar_conteo_easter(self, event):
        if self.timer_easter: self.after_cancel(self.timer_easter)
        self.timer_easter = self.after(5000, self.mostrar_ventana_creditos)

    def cancelar_conteo_easter(self, event):
        if self.timer_easter: self.after_cancel(self.timer_easter)
        self.timer_easter = None

    def mostrar_ventana_creditos(self):
        self.timer_easter = None
        base_path = resource_path("favicon_io")
        img_path = os.path.join(base_path, "Cratedbyrerree.png")
        if not os.path.exists(img_path): img_path = os.path.join(base_path, "Cratedbyrerree.jpg")
        webbrowser.open("https://drive.google.com/file/d/1hQzy03OW9lsqU56Pp692r624HynT2t_o/view?usp=drive_link")

        if not os.path.exists(img_path):
            self.log_sistema("Easter egg activado... pero falta la imagen :(")
            return

        top = ctk.CTkToplevel(self)
        top.title("CREDITS")
        icon_path = os.path.join(base_path, "favicon.ico")
        if os.path.exists(icon_path): top.after(200, lambda: top.iconbitmap(icon_path))
        top.resizable(False, False)
        top.attributes("-topmost", True)
        try:
            pil_img = Image.open(img_path)
            target_width = 150
            w_percent = (target_width / float(pil_img.size[0]))
            h_size = int((float(pil_img.size[1]) * float(w_percent)))
            pil_resized = pil_img.resize((target_width, h_size), Image.Resampling.LANCZOS)
            tk_img = ctk.CTkImage(light_image=pil_resized, dark_image=pil_resized, size=(target_width, h_size))
            top.geometry(f"{target_width}x{h_size}")
            lbl = ctk.CTkLabel(top, text="", image=tk_img)
            lbl.pack(expand=True, fill="both")
            self.bell()
        except Exception as e: self.log_sistema(f"Error créditos: {e}")

    def monitor_loop(self):
        # --- SYSTEM STATS ---
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            if hasattr(self, 'lbl_cpu'): self.lbl_cpu.configure(text=f"{self.lang.get('cpu')} {cpu}%")
            if hasattr(self, 'lbl_ram'): self.lbl_ram.configure(text=f"{self.lang.get('ram')} {ram}%")
        except: pass

        # --- AUTO-SYNC PERIODIC (Cada ~30 segundos si el monitor corre a 2s) ---
        if not hasattr(self, 'sync_counter'): self.sync_counter = 0
        self.sync_counter += 1
        if self.sync_counter >= 15: # 15 * 2s = 30s
            self.sync_counter = 0
            # Sincronización silenciosa de fondo
            self.users.sincronizar_con_archivos()
            # Si estamos en la página de usuarios, refrescar visualmente
            if self.frame_users.winfo_viewable():
                self.refrescar_lista_usuarios()

        esta_on = self.steam.esta_corriendo()
        if self.steam.is_stopping: 
            self.lbl_status.configure(text=self.lang.get("status_stopping"), text_color="#FF0000")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="disabled")
        elif self.steam.is_restarting: 
            self.lbl_status.configure(text=self.lang.get("status_restarting"), text_color="#FFCC00")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="disabled")
        elif esta_on: 
            self.btn_start.configure(state="disabled", fg_color="#2b2b2b", text=self.lang.get("btn_already_on"))
            self.btn_stop.configure(state="normal", fg_color=COLORS["danger"], text=f"⏹ {self.lang.get('btn_stop')}")
            if hasattr(self, 'btn_restart'): self.btn_restart.configure(state="normal")
            if self.server_is_fully_loaded: self.lbl_status.configure(text=self.lang.get("status_online"), text_color=COLORS["success"])
            
            # --- A2S Query: corre siempre que el servidor esté corriendo ---
            # Si el A2S responde, automáticamente marca server_is_fully_loaded=True
            self.actualizar_jugadores_a2s()
            
        else:
            self.server_is_fully_loaded = False; self.player_count_log = 0
            self.lbl_status.configure(text=self.lang.get("status_offline"), text_color=COLORS["danger"])
            self.lbl_players.configure(text=f"{self.lang.get('label_players')} ---", text_color="gray")
            self.btn_start.configure(state="normal", fg_color=COLORS["success"], text=f"▶ {self.lang.get('btn_start')}")
            self.btn_stop.configure(state="disabled", fg_color="#2b2b2b", text=self.lang.get("btn_status_stopped"))
        
        self.after(2000, self.monitor_loop)

    def actualizar_jugadores_a2s(self):
        """Lanza el query A2S en background. Throttled: solo 1 query a la vez."""
        if getattr(self, '_a2s_running', False):
            return
        self._a2s_running = True
        threading.Thread(target=self._query_a2s_thread, daemon=True).start()

    def _query_a2s_thread(self):
        try:
            q_port_str = self.entry_query.get().strip()
            g_port_str = self.entry_port.get().strip() if hasattr(self, 'entry_port') else "7777"

            q_port = int(q_port_str) if q_port_str.isdigit() else 27015
            g_port = int(g_port_str) if g_port_str.isdigit() else 7777

            pub_ip = self.entry_ip.get().strip() or None

            # IPs a intentar
            ips = ["127.0.0.1"]
            if pub_ip and pub_ip not in ips:
                ips.append(pub_ip)

            # Puertos a intentar: query port primero, luego game port
            ports = list(dict.fromkeys([q_port, g_port]))  # sin duplicados

            info = None
            ok_addr = None
            for ip in ips:
                for port in ports:
                    try:
                        info = a2s.info((ip, port), timeout=2.5)
                        ok_addr = f"{ip}:{port}"
                        break
                    except Exception:
                        continue
                if info is not None:
                    break

            if info is not None:
                # A2S respondio — resetear contador de fallos y mostrar datos reales
                self._a2s_fail_count = 0
                count_text = f"{info.player_count}/{info.max_players}"
                self.after(0, lambda c=count_text: self.lbl_players.configure(
                    text=f"{self.lang.get('label_players')} {c}",
                    text_color=COLORS["success"]
                ))
                self.player_count_log = info.player_count
                if not self.server_is_fully_loaded:
                    self.server_is_fully_loaded = True
                    self.after(0, lambda: self.lbl_status.configure(
                        text=self.lang.get("status_online"), text_color=COLORS["success"]
                    ))
            else:
                # A2S fallo — intentar usar el LogWatcher como fallback
                self._a2s_fail_count += 1

                # Solo loguear el warning las primeras 3 veces, luego silenciar
                if self._a2s_fail_count <= 3:
                    self.log_sistema(
                        f"⚠️ [A2S] Sin respuesta en {ips} × puertos {ports}. "
                        f"Usando LogWatcher como fallback."
                    )

                # Mostrar conteo del LogWatcher si esta disponible
                if self.log_watcher:
                    lw_count = self.log_watcher.get_count()
                    count_text = f"~{lw_count} (log)"
                    self.after(0, lambda c=count_text: self.lbl_players.configure(
                        text=f"{self.lang.get('label_players')} {c}",
                        text_color="#FFCC00"  # Amarillo para indicar dato aproximado
                    ))

        except Exception as e:
            self.log_sistema(f"❌ [A2S] Error inesperado: {e}")
        finally:
            self._a2s_running = False



    def consultar_jugadores_reales(self):
        if not self.server_is_fully_loaded: return
        def _consulta():
            try:
                ip = self.entry_ip.get(); port = int(self.entry_query.get())
                info = a2s.info((ip, port), timeout=2)
                self.lbl_players.configure(text=f"{self.lang.get('label_players')} {info.player_count}/{info.max_players}", text_color="white")
            except: pass
        threading.Thread(target=_consulta).start()

    def construir_stats_shop(self):
        for w in self.frame_stats_shop.winfo_children(): w.destroy()
        
        self.stats_selected_player = None
        self.stats_skills_package = {}
        
        self._t(ctk.CTkLabel(self.frame_stats_shop, text=self.lang.get("stats_shop_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]), "stats_shop_title").pack(pady=15, padx=30, anchor="w")
        
        split = ctk.CTkFrame(self.frame_stats_shop, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=20, pady=5)
        
        # --- COLUMNA IZQUIERDA: Formulario de Compra (Scrollable para evitar recortes) ---
        col_left = ctk.CTkScrollableFrame(split, fg_color=COLORS["panel"])
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 1. BÚSQUEDA DE JUGADOR
        lbl_search = self._t(ctk.CTkLabel(col_left, text=self.lang.get("stats_shop_search_lbl"), font=("Roboto", 12, "bold")), "stats_shop_search_lbl")
        lbl_search.pack(anchor="w", padx=15, pady=(10, 2))
        
        search_row = ctk.CTkFrame(col_left, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=2)
        
        self.entry_stats_search = self._t(ctk.CTkEntry(search_row, placeholder_text=self.lang.get("stats_shop_search_placeholder")), "stats_shop_search_placeholder", "placeholder_text")
        self.entry_stats_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_search = self._t(ctk.CTkButton(search_row, text=self.lang.get("stats_shop_btn_search"), width=80, fg_color=COLORS["accent"], text_color="black", command=self.buscar_jugador_stats_shop), "stats_shop_btn_search")
        btn_search.pack(side="right")
        
        self.frame_stats_search_results = ctk.CTkScrollableFrame(col_left, height=100, fg_color="#151515")
        self.frame_stats_search_results.pack(fill="x", padx=15, pady=5)
        
        self.lbl_stats_player_info = self._t(ctk.CTkLabel(col_left, text=self.lang.get("stats_shop_no_player_selected"), font=("Roboto", 12, "italic"), text_color="#aaaaaa"), "stats_shop_no_player_selected")
        self.lbl_stats_player_info.pack(anchor="w", padx=15, pady=5)
        
        # Separador visual
        ctk.CTkFrame(col_left, height=2, fg_color="#444").pack(fill="x", padx=15, pady=10)
        
        # 2. OPCIÓN A: COMPRA DE ATRIBUTOS (STATS)
        lbl_attr_sec = self._t(ctk.CTkLabel(col_left, text=self.lang.get("stats_shop_attr_sec"), font=("Roboto", 14, "bold"), text_color=COLORS["accent"]), "stats_shop_attr_sec")
        lbl_attr_sec.pack(anchor="w", padx=15, pady=(5, 2))
        
        attr_title = self._t(ctk.CTkLabel(col_left, text=self.lang.get("stats_shop_attr_title"), font=("Roboto", 11, "italic"), text_color="#aaa"), "stats_shop_attr_title")
        attr_title.pack(anchor="w", padx=15, pady=(0, 5))
        
        attr_grid = ctk.CTkFrame(col_left, fg_color="transparent")
        attr_grid.pack(fill="x", padx=15, pady=5)
        
        self._t(ctk.CTkLabel(attr_grid, text=self.lang.get("stats_shop_attr_str")), "stats_shop_attr_str").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_stats_str = ctk.CTkEntry(attr_grid, width=60, placeholder_text="0-5")
        self.entry_stats_str.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        self._t(ctk.CTkLabel(attr_grid, text=self.lang.get("stats_shop_attr_con")), "stats_shop_attr_con").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_stats_con = ctk.CTkEntry(attr_grid, width=60, placeholder_text="0-5")
        self.entry_stats_con.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        self._t(ctk.CTkLabel(attr_grid, text=self.lang.get("stats_shop_attr_dex")), "stats_shop_attr_dex").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_stats_dex = ctk.CTkEntry(attr_grid, width=60, placeholder_text="0-5")
        self.entry_stats_dex.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        self._t(ctk.CTkLabel(attr_grid, text=self.lang.get("stats_shop_attr_int")), "stats_shop_attr_int").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.entry_stats_int = ctk.CTkEntry(attr_grid, width=60, placeholder_text="0-5")
        self.entry_stats_int.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        attr_footer = ctk.CTkFrame(col_left, fg_color="transparent")
        attr_footer.pack(fill="x", padx=15, pady=10)
        
        self._t(ctk.CTkLabel(attr_footer, text=self.lang.get("stats_shop_days_attr")), "stats_shop_days_attr").pack(side="left", padx=5)
        self.entry_stats_days_attr = ctk.CTkEntry(attr_footer, width=65)
        self.entry_stats_days_attr.insert(0, "30")
        self.entry_stats_days_attr.pack(side="left", padx=5)
        
        btn_reg_attrs = self._t(ctk.CTkButton(attr_footer, text=self.lang.get("stats_shop_btn_save_attrs"), fg_color=COLORS["success"], text_color="black", font=("Roboto", 12, "bold"), command=self.registrar_atributos_stats_shop), "stats_shop_btn_save_attrs")
        btn_reg_attrs.pack(side="right", padx=5)
        
        # Separador visual
        ctk.CTkFrame(col_left, height=2, fg_color="#444").pack(fill="x", padx=15, pady=10)
        
        # 3. OPCIÓN B: COMPRA DE HABILIDADES (SKILLS)
        lbl_skills_sec = self._t(ctk.CTkLabel(col_left, text=self.lang.get("stats_shop_skills_sec"), font=("Roboto", 14, "bold"), text_color=COLORS["accent"]), "stats_shop_skills_sec")
        lbl_skills_sec.pack(anchor="w", padx=15, pady=(5, 2))
        
        skills_row = ctk.CTkFrame(col_left, fg_color="transparent")
        skills_row.pack(fill="x", padx=15, pady=5)
        
        from src.logic.stats_shop import SKILLS_DISPONIBLES
        self.combo_stats_skills = ctk.CTkComboBox(skills_row, values=SKILLS_DISPONIBLES, width=200)
        self.combo_stats_skills.pack(side="left", padx=(0, 5))
        
        self.entry_stats_skill_level = ctk.CTkEntry(skills_row, width=50, placeholder_text="1-5")
        self.entry_stats_skill_level.insert(0, "3")
        self.entry_stats_skill_level.pack(side="left", padx=(0, 5))
        
        btn_add_skill = self._t(ctk.CTkButton(skills_row, text=self.lang.get("stats_shop_btn_add_skill"), width=80, fg_color="#333", command=self.agregar_skill_stats_shop), "stats_shop_btn_add_skill")
        btn_add_skill.pack(side="left", padx=(0, 5))
        
        btn_add_all_skills = self._t(ctk.CTkButton(skills_row, text=self.lang.get("stats_shop_btn_add_all"), width=110, fg_color="#444", hover_color="#555", command=self.agregar_todos_skills_stats_shop), "stats_shop_btn_add_all")
        btn_add_all_skills.pack(side="left")
        
        self.frame_added_skills = ctk.CTkScrollableFrame(col_left, height=100, fg_color="#151515")
        self.frame_added_skills.pack(fill="x", padx=15, pady=5)
        
        skills_footer = ctk.CTkFrame(col_left, fg_color="transparent")
        skills_footer.pack(fill="x", padx=15, pady=10)
        
        self._t(ctk.CTkLabel(skills_footer, text=self.lang.get("stats_shop_days_skills")), "stats_shop_days_skills").pack(side="left", padx=5)
        self.entry_stats_days_skills = ctk.CTkEntry(skills_footer, width=65)
        self.entry_stats_days_skills.insert(0, "30")
        self.entry_stats_days_skills.pack(side="left", padx=5)
        
        btn_reg_skills = self._t(ctk.CTkButton(skills_footer, text=self.lang.get("stats_shop_btn_save_skills"), fg_color=COLORS["success"], text_color="black", font=("Roboto", 12, "bold"), command=self.registrar_skills_stats_shop), "stats_shop_btn_save_skills")
        btn_reg_skills.pack(side="right", padx=5)
        
        # --- COLUMNA DERECHA: Suscripciones ---
        col_right = ctk.CTkFrame(split, fg_color=COLORS["panel"])
        col_right.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        lbl_subs = self._t(ctk.CTkLabel(col_right, text=self.lang.get("stats_shop_subs_title"), font=("Roboto", 14, "bold"), text_color=COLORS["text_main"]), "stats_shop_subs_title")
        lbl_subs.pack(pady=10)
        
        # Buscador/Filtro de suscripciones
        search_subs_frame = ctk.CTkFrame(col_right, fg_color="transparent")
        search_subs_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.entry_stats_subs_search = self._t(ctk.CTkEntry(search_subs_frame, placeholder_text=self.lang.get("stats_shop_subs_filter_ph"), font=("Roboto", 12)), "stats_shop_subs_filter_ph", "placeholder_text")
        self.entry_stats_subs_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_stats_subs_search.bind("<KeyRelease>", lambda event: self.refrescar_lista_stats_shop())
        
        btn_clear_subs_search = ctk.CTkButton(search_subs_frame, text="X", width=30, fg_color="#333333", text_color="white", command=self.clear_stats_subs_search)
        btn_clear_subs_search.pack(side="right")
        
        self.frame_subs_list = ctk.CTkScrollableFrame(col_right, fg_color="transparent")
        self.frame_subs_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.refrescar_lista_stats_shop()

    def buscar_jugador_stats_shop(self):
        query = self.entry_stats_search.get().strip()
        if not query:
            return
            
        for w in self.frame_stats_search_results.winfo_children(): w.destroy()
        
        resultados = self.stats_shop.buscar_jugadores(query)
        if not resultados:
            lbl = ctk.CTkLabel(self.frame_stats_search_results, text=self.lang.get("stats_shop_no_players_found"), text_color="#ff5555")
            lbl.pack(pady=5)
            return
            
        for p in resultados:
            btn = ctk.CTkButton(
                self.frame_stats_search_results, 
                text=f"{p['name']} ({p['steam_id']}) - Fame: {p['fame']}",
                fg_color="#1a1a1a",
                hover_color="#333333",
                anchor="w",
                command=lambda player=p: self.seleccionar_jugador_stats_shop(player)
            )
            btn.pack(fill="x", pady=2, padx=2)

    def seleccionar_jugador_stats_shop(self, player):
        self.stats_selected_player = player
        prefix = self.lang.get("stats_shop_selected")
        self.lbl_stats_player_info.configure(
            text=f"{prefix}: {player['name']} ({player['steam_id']})\nPrisoner ID: {player['prisoner_id']}",
            text_color="#00FF00"
        )
        attrs = self.stats_shop.leer_atributos(player['prisoner_id'])
        if attrs:
            self.entry_stats_str.delete(0, "end"); self.entry_stats_str.insert(0, str(attrs.get("Strength", 0)))
            self.entry_stats_con.delete(0, "end"); self.entry_stats_con.insert(0, str(attrs.get("Constitution", 0)))
            self.entry_stats_dex.delete(0, "end"); self.entry_stats_dex.insert(0, str(attrs.get("Dexterity", 0)))
            self.entry_stats_int.delete(0, "end"); self.entry_stats_int.insert(0, str(attrs.get("Intelligence", 0)))

    def agregar_todos_skills_stats_shop(self):
        from src.logic.stats_shop import SKILLS_DISPONIBLES
        level_str = self.entry_stats_skill_level.get().strip()
        if not level_str.isdigit():
            return
        level = int(level_str)
        if level < 0 or level > 5:
            return
            
        for skill in SKILLS_DISPONIBLES:
            self.stats_skills_package[skill] = level
        self._refrescar_visual_skills_agregados()

    def agregar_skill_stats_shop(self):
        skill = self.combo_stats_skills.get()
        level_str = self.entry_stats_skill_level.get().strip()
        if not skill or not level_str.isdigit():
            return
        
        level = int(level_str)
        if level < 0 or level > 5:
            return
            
        self.stats_skills_package[skill] = level
        self._refrescar_visual_skills_agregados()

    def eliminar_skill_stats_shop(self, skill):
        if skill in self.stats_skills_package:
            del self.stats_skills_package[skill]
            self._refrescar_visual_skills_agregados()

    def _refrescar_visual_skills_agregados(self):
        for w in self.frame_added_skills.winfo_children(): w.destroy()
        
        if not self.stats_skills_package:
            lbl = ctk.CTkLabel(self.frame_added_skills, text=self.lang.get("stats_shop_no_skills_added"), text_color="#aaaaaa", font=("Roboto", 11, "italic"))
            lbl.pack(pady=5)
            return
            
        for skill, level in self.stats_skills_package.items():
            row = ctk.CTkFrame(self.frame_added_skills, fg_color="#222")
            row.pack(fill="x", pady=2, padx=2)
            
            lvl_text = self.lang.get("stats_shop_level")
            lbl = ctk.CTkLabel(row, text=f"{skill} -> {lvl_text} {level}", font=("Consolas", 11))
            lbl.pack(side="left", padx=5)
            
            btn_del = ctk.CTkButton(row, text=self.lang.get("stats_shop_btn_delete"), width=60, height=20, fg_color=COLORS["danger"], text_color="white", command=lambda s=skill: self.eliminar_skill_stats_shop(s))
            btn_del.pack(side="right", padx=5)

    def registrar_atributos_stats_shop(self):
        if not self.stats_selected_player:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_select_player"))
            return
            
        try:
            dias = int(self.entry_stats_days_attr.get().strip())
        except:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_days_int"))
            return
            
        attrs = {}
        def read_attr(entry, name):
            val = entry.get().strip().replace(',', '.')
            if val:
                try:
                    f_val = float(val)
                    if f_val > 0:
                        attrs[name] = f_val
                except ValueError:
                    pass
                
        read_attr(self.entry_stats_str, "Strength")
        read_attr(self.entry_stats_con, "Constitution")
        read_attr(self.entry_stats_dex, "Dexterity")
        read_attr(self.entry_stats_int, "Intelligence")
        
        if not attrs:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_at_least_one_attr"))
            return
            
        success = self.stats_shop.registrar_pack(
            steam_id=self.stats_selected_player['steam_id'],
            player_name=self.stats_selected_player['name'],
            prisoner_id=self.stats_selected_player['prisoner_id'],
            dias=dias,
            atributos=attrs,
            skills=None
        )
        
        if success:
            msg = self.lang.get("stats_shop_succ_attrs").replace("{player}", self.stats_selected_player['name'])
            messagebox.showinfo("OK", msg)
            self.entry_stats_str.delete(0, "end")
            self.entry_stats_con.delete(0, "end")
            self.entry_stats_dex.delete(0, "end")
            self.entry_stats_int.delete(0, "end")
            self.refrescar_lista_stats_shop()
        else:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_save_attrs"))

    def registrar_skills_stats_shop(self):
        if not self.stats_selected_player:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_select_player"))
            return
            
        try:
            dias = int(self.entry_stats_days_skills.get().strip())
        except:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_days_int"))
            return
            
        if not self.stats_skills_package:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_at_least_one_skill"))
            return
            
        success = self.stats_shop.registrar_pack(
            steam_id=self.stats_selected_player['steam_id'],
            player_name=self.stats_selected_player['name'],
            prisoner_id=self.stats_selected_player['prisoner_id'],
            dias=dias,
            atributos=None,
            skills=self.stats_skills_package
        )
        
        if success:
            msg = self.lang.get("stats_shop_succ_skills").replace("{player}", self.stats_selected_player['name'])
            messagebox.showinfo("OK", msg)
            self.stats_skills_package = {}
            self._refrescar_visual_skills_agregados()
            self.refrescar_lista_stats_shop()
        else:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_save_skills"))

    def refrescar_lista_stats_shop(self):
        for w in self.frame_subs_list.winfo_children(): w.destroy()
        
        self.stats_shop._subs = self.stats_shop._cargar_subs()
        suscripciones = self.stats_shop.obtener_subs_activas()
        
        query = ""
        if hasattr(self, 'entry_stats_subs_search'):
            query = self.entry_stats_subs_search.get().strip().lower()
            
        if query:
            suscripciones = [
                s for s in suscripciones
                if query in s["player_name"].lower() or query in s["steam_id"].lower()
            ]
            
        if not suscripciones:
            lbl = ctk.CTkLabel(self.frame_subs_list, text=self.lang.get("stats_shop_no_active_subs"), text_color="#aaaaaa", font=("Roboto", 12, "italic"))
            lbl.pack(pady=20)
            return
            
        for sub in suscripciones:
            color_border = "#FFD700" if sub["estado"] == "activo" else "#FF8800"
            card = ctk.CTkFrame(self.frame_subs_list, fg_color="#1a1a1a", border_width=1, border_color=color_border)
            card.pack(fill="x", pady=4, padx=2)
            
            desc = []
            if sub.get("atributos_nuevos"):
                desc.append("Attrs: " + ", ".join([f"{k}={v}" for k, v in sub["atributos_nuevos"].items()]))
            if sub.get("skills_nuevos"):
                desc.append("Skills: " + ", ".join([f"{k[:10]}={v}" for k, v in sub["skills_nuevos"].items()]))
            
            exp_text = self.lang.get("stats_shop_expires")
            state_text = self.lang.get("stats_shop_state")
            info_text = (
                f"👤 {sub['player_name']} ({sub['steam_id']})\n"
                f"📅 {exp_text}: {sub['fecha_expiracion']}\n"
                f"🏷️ {state_text}: {sub['estado'].upper()}\n"
                f"📦 {', '.join(desc)}"
            )
            
            if sub["estado"] in ("activo", "pendiente_aplicar"):
                btn_rev = ctk.CTkButton(
                    card, 
                    text=self.lang.get("stats_shop_btn_revoke"), 
                    width=70, 
                    height=24, 
                    fg_color=COLORS["danger"], 
                    text_color="white",
                    font=("Roboto", 11, "bold"),
                    command=lambda sid=sub["steam_id"], fc=sub["fecha_compra"]: self.revocar_pack_stats_shop(sid, fc)
                )
                btn_rev.pack(side="right", padx=(5, 10), pady=10)

                btn_edit = ctk.CTkButton(
                    card,
                    text=self.lang.get("stats_shop_btn_edit"),
                    width=60,
                    height=24,
                    fg_color=COLORS["accent"],
                    text_color="white",
                    font=("Roboto", 11, "bold"),
                    command=lambda s=sub: self.cargar_suscripcion_para_editar(s)
                )
                btn_edit.pack(side="right", padx=(10, 5), pady=10)

            lbl = ctk.CTkLabel(card, text=info_text, font=("Consolas", 11), justify="left", anchor="w")
            lbl.pack(side="left", padx=10, pady=5, fill="x", expand=True)

    def revocar_pack_stats_shop(self, steam_id, fecha_compra):
        sub = next((s for s in self.stats_shop.obtener_subs_activas() if s["steam_id"] == steam_id and s["fecha_compra"] == fecha_compra), None)
        if not sub:
            return
            
        es_pendiente = sub["estado"] == "pendiente_aplicar"
        if es_pendiente:
            if not messagebox.askyesno("Confirm", self.lang.get("stats_shop_confirm_del_pending")):
                return
        else:
            if not messagebox.askyesno("Confirm", self.lang.get("stats_shop_confirm_revoke_active")):
                return
            
        if self.stats_shop.revocar_pack(steam_id, fecha_compra):
            if es_pendiente:
                messagebox.showinfo("OK", self.lang.get("stats_shop_succ_del_pending"))
            else:
                messagebox.showinfo("OK", self.lang.get("stats_shop_succ_revoke_active"))
            self.refrescar_lista_stats_shop()
        else:
            messagebox.showerror(self.lang.get("log_title_sys"), self.lang.get("stats_shop_err_revoke"))

    def clear_stats_subs_search(self):
        if hasattr(self, 'entry_stats_subs_search'):
            self.entry_stats_subs_search.delete(0, "end")
        self.refrescar_lista_stats_shop()

    def cargar_suscripcion_para_editar(self, sub):
        self.stats_selected_player = {
            'steam_id': sub['steam_id'],
            'name': sub['player_name'],
            'prisoner_id': sub['prisoner_id']
        }
        prefix = self.lang.get("stats_shop_selected")
        self.lbl_stats_player_info.configure(
            text=f"{prefix}: {sub['player_name']} ({sub['steam_id']})\nPrisoner ID: {sub['prisoner_id']}",
            text_color="#00FF00"
        )
        
        attrs = sub.get("atributos_nuevos") or {}
        self.entry_stats_str.delete(0, "end"); self.entry_stats_str.insert(0, str(attrs.get("Strength", "")))
        self.entry_stats_con.delete(0, "end"); self.entry_stats_con.insert(0, str(attrs.get("Constitution", "")))
        self.entry_stats_dex.delete(0, "end"); self.entry_stats_dex.insert(0, str(attrs.get("Dexterity", "")))
        self.entry_stats_int.delete(0, "end"); self.entry_stats_int.insert(0, str(attrs.get("Intelligence", "")))
        
        self.stats_skills_package = dict(sub.get("skills_nuevos") or {})
        self._refrescar_visual_skills_agregados()
        
        dias_str = str(sub.get("dias", 30))
        self.entry_stats_days_attr.delete(0, "end"); self.entry_stats_days_attr.insert(0, dias_str)
        self.entry_stats_days_skills.delete(0, "end"); self.entry_stats_days_skills.insert(0, dias_str)
        
        msg = self.lang.get("stats_shop_edit_benefits_msg").replace("{player}", sub['player_name'])
        messagebox.showinfo(self.lang.get("stats_shop_edit_benefits_title"), msg)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = VoidWindow()
    app.mainloop()
