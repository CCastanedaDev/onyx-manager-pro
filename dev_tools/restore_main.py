part1 = """import customtkinter as ctk
import requests
import threading
import json
import os
import a2s
import socket
import psutil
import webbrowser
import time
from PIL import Image

# --- IMPORTACIONES LOCALES ---
from src.ui.styles import COLORS, FONTS
from src.logic.steam_handler import SteamHandler 
from src.logic.task_scheduler import TaskManager
from src.logic.file_editor import ConfigEditor
from src.logic.user_manager import UserManager
from src.logic.admin_manager import AdminManager
from src.logic.language_manager import LanguageManager
from src.logic.backup_manager import BackupManager
from src.logic.watchdog import SteamWatchdog

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
        
        w, h = 1350, 650 
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = int((ws/2)-(w/2)), int((hs/2)-(h/2)) - 40
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1350, 650)
        
        self.configure(fg_color=COLORS["background"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.gui_settings_file = os.path.join("data", "gui_settings.json")
        self.temp_profile_settings = {} 
        self.cat_translation_map = {}
        self.setting_translation_map = {}

        self.server_is_fully_loaded = False
        self.player_count_log = 0
        self.timer_easter = None 

        idioma_inicial = "es"
        if os.path.exists(self.gui_settings_file):
            try:
                with open(self.gui_settings_file, 'r') as f: 
                    saved_data = json.load(f)
                    if "lang" in saved_data: idioma_inicial = saved_data["lang"]
            except: pass
        
        self.lang = LanguageManager(idioma_inicial)
        self.img_path = os.path.join(os.getcwd(), "favicon_io")

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
        self.frame_logs = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.steam = SteamHandler(self.log_servidor) 
        self.editor = ConfigEditor(self.log_sistema)
        self.users = UserManager(self.log_sistema)
        self.admins = AdminManager(self.log_sistema)
        self.scheduler = TaskManager(self.steam, self.log_sistema, self.editor)
        self.watchdog = SteamWatchdog()

        self.construir_interfaz_completa()
        self.seleccionar_pagina("dashboard")
        self.cargar_memoria_visual()
        self.monitor_loop() 
        
        self.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def construir_interfaz_completa(self):
        self.crear_sidebar()
        self.construir_dashboard() 
        self.construir_logs()
        self.construir_scheduler()
        self.construir_tasks()     
        self.construir_users()     
        self.construir_admins()
        self.construir_ini_editor()

    def log_sistema(self, msg):
        try:
            if hasattr(self, 'console') and self.console.winfo_exists():
                self.console.insert("end", f">> {msg}\\n"); self.console.see("end")
        except: pass

    def log_servidor(self, msg):
        triggers = ["Connected to BE Master", "Match State Changed from WaitingToStart to InProgress", "Server Steam ID", "LogNet: Listen", "LogQuadTree: Warning"]
        for t in triggers:
            if t in msg: 
                self.server_is_fully_loaded = True
                try: self.lbl_status.configure(text=self.lang.get("status_online"), text_color=COLORS["success"])
                except: pass
                break
        msg_lower = msg.lower()
        if "lognet: login:" in msg_lower or ("logbattleeye" in msg_lower and "connected" in msg_lower): 
            self.player_count_log += 1; self.log_sistema(f"{self.lang.get('log_login')}: +1")
            
            # --- WATCHDOG CHECK ---
            if "lognet: login:" in msg_lower and hasattr(self, 'switch_watchdog') and self.switch_watchdog.get() == 1:
                try:
                    parts = msg.split("Login: ")
                    if len(parts) > 1:
                        steam_id = parts[1].strip().split(" ")[0] 
                        def check_and_ban():
                            if self.watchdog.check_player(steam_id, lambda sid: self.admins.es_admin(sid) or self.users.es_vip(sid)):
                                self.log_sistema(f"🛡️ WATCHDOG: JUGADOR {steam_id} DETECTADO CON BANS (VAC/GAME). BANEANDO...")
                                self.users.agregar_usuario("BAN", steam_id, -1, "Auto-Ban: Detectado por ONYX Watchdog")
                        threading.Thread(target=check_and_ban).start()
                except Exception as e:
                    print(f"Watchdog Error: {e}")
            # ----------------------

        if "unetconnection::close:" in msg_lower or ("logbattleeye" in msg_lower and "disconnected" in msg_lower):
            if self.player_count_log > 0: self.player_count_log -= 1
            self.log_sistema(f"{self.lang.get('log_logout')}: -1")
        try:
            if hasattr(self, 'big_console') and self.big_console.winfo_exists():
                self.big_console.insert("end", f"{msg}\\n"); self.big_console.see("end")
        except: pass
        try:
            if hasattr(self, 'big_console_tab') and self.big_console_tab.winfo_exists():
                self.big_console_tab.insert("end", f"{msg}\\n"); self.big_console_tab.see("end")
        except: pass
    
    def log_msg(self, msg): self.log_sistema(msg)
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
        
        self.crear_boton_menu(self.lang.get("menu_dashboard"), "dashboard", 2)
        self.crear_boton_menu(self.lang.get("menu_profiles"), "profiles", 3)
        self.crear_boton_menu(self.lang.get("menu_scheduler"), "tasks", 4)
        self.crear_boton_menu(self.lang.get("menu_users"), "users", 5)
        self.crear_boton_menu(self.lang.get("menu_admins"), "admins", 6)
        self.crear_boton_menu(self.lang.get("menu_editor"), "ini_editor", 7)
        self.crear_boton_menu(self.lang.get("menu_logs"), "logs", 8)
        ctk.CTkLabel(self.sidebar, text="v18.0 STABLE", text_color=COLORS["text_dim"]).grid(row=10, column=0, pady=20, sticky="s")
        self.sidebar.grid_rowconfigure(10, weight=1)
    def crear_boton_menu(self, texto, pagina, fila):
        btn = ctk.CTkButton(self.sidebar, text=texto, fg_color="transparent", text_color=COLORS["text_main"], hover_color=COLORS["hover"], anchor="w", command=lambda: self.seleccionar_pagina(pagina))
        btn.grid(row=fila, column=0, padx=10, pady=5, sticky="ew")

    def seleccionar_pagina(self, nombre):
        self.frame_dashboard.grid_forget(); self.frame_profiles.grid_forget(); self.frame_tasks.grid_forget()
        self.frame_users.grid_forget(); self.frame_logs.grid_forget()
        self.frame_admins.grid_forget(); self.frame_ini_editor.grid_forget()
"""

missing = """    def cambiar_idioma(self, lang_code):
        self.lang.load_language(lang_code)
        try:
            if os.path.exists(self.gui_settings_file):
                with open(self.gui_settings_file, 'r') as f: datos = json.load(f)
            else: datos = {}
            datos["lang"] = lang_code
            with open(self.gui_settings_file, 'w') as f: json.dump(datos, f)
        except: pass
        self.construir_interfaz_completa()
        self.cargar_memoria_visual()
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
        
        self.switch_watchdog = ctk.CTkSwitch(switches_frame, text="Auto-Ban (VAC/GameBan)", progress_color=COLORS["danger"], text_color="gray", command=self.toggle_watchdog)
        self.switch_watchdog.pack(anchor="w", pady=2)
        
        self.lbl_watchdog_status = ctk.CTkLabel(switches_frame, text="", font=("Roboto", 10))
        self.lbl_watchdog_status.pack(anchor="w")

        # 3. BOTONES DE ACCIÓN (Derecha)
        actions_frame = ctk.CTkFrame(panel_top, fg_color="transparent")
        actions_frame.pack(side="right", padx=20, pady=10)

        # Fila superior (Start, Restart, Stop)
        row_btns_1 = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row_btns_1.pack(side="top", anchor="e", pady=(0, 5))
        
        self.btn_start = ctk.CTkButton(row_btns_1, text=self.lang.get("btn_start"), fg_color=COLORS["success"], text_color="black", hover_color="#2E7D32", width=100, command=self.steam.iniciar_servidor)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_restart = ctk.CTkButton(row_btns_1, text=self.lang.get("btn_restart"), fg_color="#D35400", hover_color="#A04000", width=100, command=self.accion_reiniciar_hilo)
        self.btn_restart.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(row_btns_1, text=self.lang.get("btn_stop"), fg_color=COLORS["danger"], hover_color="#A00000", width=100, command=self.accion_detener_hilo)
        self.btn_stop.pack(side="left", padx=5)

        # Fila inferior (Update, Backup, Lang)
        row_btns_2 = ctk.CTkFrame(actions_frame, fg_color="transparent")
        row_btns_2.pack(side="top", anchor="e")

        self.btn_update = ctk.CTkButton(row_btns_2, text=self.lang.get("btn_update"), fg_color="#E0A800", text_color="black", hover_color="#C69500", width=120, command=lambda: threading.Thread(target=self.steam.instalar_servidor).start())
        self.btn_update.pack(side="left", padx=5)
        
        btn_backup = ctk.CTkButton(row_btns_2, text=self.lang.get("btn_backup"), fg_color="#4a4a4a", width=80, command=self.accion_backup_manual)
        btn_backup.pack(side="left", padx=5)
        
        self.combo_lang = ctk.CTkComboBox(row_btns_2, values=["es", "en", "pt", "fr", "ru", "de", "zh", "hi", "ja"], width=60, command=self.cambiar_idioma)
        self.combo_lang.set(self.lang.current_lang) 
        self.combo_lang.pack(side="left", padx=5)


        # --- RESTO DEL DASHBOARD ---
        middle_container = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent"); middle_container.pack(fill="x", padx=20, pady=5)
        panel_config = ctk.CTkFrame(middle_container, fg_color="transparent"); panel_config.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Header
        header_frame = ctk.CTkFrame(panel_config, fg_color="transparent"); header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header_frame, text=self.lang.get("header_config"), text_color=COLORS["text_dim"], font=("Roboto", 12, "bold")).pack(side="left")
        btn_save = ctk.CTkButton(header_frame, text=self.lang.get("btn_save_changes"), width=100, height=24, fg_color=COLORS["accent"], text_color="black", command=self.accion_guardar); btn_save.pack(side="right")
        
        # Grid System
        grid_frame = ctk.CTkFrame(panel_config, fg_color=COLORS["panel"], corner_radius=10)
        grid_frame.pack(fill="x", pady=2)
        
        # --- RADICAL FIX: Force Row Heights ---
        grid_frame.grid_rowconfigure((0, 1, 2, 3), minsize=70)
        grid_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        # Fila 0: Nombre Servidor (Full Width)
        self.entry_name = self.crear_input(grid_frame, self.lang.get("lbl_name"), "SCUM Server", 0, 0, span=4)
        
        # Fila 1: Descripción y Mensaje (Split)
        self.entry_desc = self.crear_input(grid_frame, self.lang.get("lbl_desc"), "", 1, 0, span=2)
        self.entry_motd = self.crear_input(grid_frame, self.lang.get("lbl_motd"), "", 1, 2, span=2)
        
        # Fila 2: Technical Row (IP, Ports, Slots, Pass)
        tech_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        tech_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        tech_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        self.crear_input_ip(tech_frame, 0, 0)
        self.entry_port = self.crear_input(tech_frame, self.lang.get("lbl_gameport"), "7777", 0, 1)
        self.entry_query = self.crear_input(tech_frame, self.lang.get("lbl_queryport"), "27015", 0, 2)
        self.entry_players = self.crear_input(tech_frame, self.lang.get("lbl_slots"), "64", 0, 3)
        self.entry_pass = self.crear_input(tech_frame, self.lang.get("lbl_pass"), "", 0, 4)
        
        # Fila 3: API Key (Full Width)
        self.entry_api_key = self.crear_input(grid_frame, "Steam Web API Key", "", 3, 0, span=4, show="*")

        # Disable Copy/Cut/Context Menu for API Key
        def disable_event(event): return "break"
        self.entry_api_key.bind("<Control-c>", disable_event)
        self.entry_api_key.bind("<Control-x>", disable_event)
        self.entry_api_key.bind("<Button-3>", disable_event) # Right click

        # --- RADICAL FIX: Shrink Consoles ---
        panel_syslog = ctk.CTkFrame(middle_container, width=300, fg_color=COLORS["panel"]); panel_syslog.pack(side="right", fill="y", padx=(0,0))
        ctk.CTkLabel(panel_syslog, text=self.lang.get("log_title_sys"), text_color="#00FF00", font=("Roboto", 11, "bold")).pack(pady=(5, 2), padx=10)
        # Height reduced to 120
        self.console = ctk.CTkTextbox(panel_syslog, width=280, height=120, fg_color="#111", text_color="#00FF00", font=("Consolas", 10)); self.console.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.log_sistema(self.lang.get("log_init"))
        
        panel_matrix = ctk.CTkFrame(self.frame_dashboard, fg_color="transparent"); panel_matrix.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        ctk.CTkLabel(panel_matrix, text=self.lang.get("log_title_matrix"), text_color=COLORS["text_main"], font=("Roboto", 12, "bold")).pack(anchor="w")
        # Height reduced to 120
        self.big_console = ctk.CTkTextbox(panel_matrix, height=120, fg_color="#000000", text_color="#00FF00", font=("Consolas", 11), activate_scrollbars=True)
        self.big_console.pack(fill="both", expand=True)
        self.big_console.insert("0.0", f"{self.lang.get('log_waiting_server')}")

    def crear_input(self, parent, label, default, r, c, span=1, show=None):
        # 1. Crear un Frame contenedor (Transparente)
        container = ctk.CTkFrame(parent, fg_color="transparent")
        # IMPORTANTE: pady=(0, 15) asegura MUCHO espacio abajo
        container.grid(row=r, column=c, columnspan=span, sticky="new", padx=5, pady=(0, 15))

        # 2. Label (Titulo)
        lbl = ctk.CTkLabel(container, text=label, text_color=COLORS["text_dim"], font=("Roboto", 11, "bold"), anchor="w")
        lbl.pack(fill="x", pady=(0, 2))

        # 3. Entry (Caja de texto)
        entry = ctk.CTkEntry(container, height=28, border_color="#333", fg_color="#111", text_color="white")
        if show: entry.configure(show=show)
        entry.pack(fill="x")

        # 4. Insertar valor y retornar
        entry.insert(0, default)
        return entry

    def crear_input_ip(self, parent, r, c):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        # IMPORTANTE: pady=(0, 15) asegura MUCHO espacio abajo
        container.grid(row=r, column=c, sticky="new", padx=5, pady=(0, 15))
        
        lbl = ctk.CTkLabel(container, text=self.lang.get("lbl_ip"), text_color=COLORS["text_dim"], font=("Roboto", 11, "bold"), anchor="w")
        lbl.pack(fill="x", pady=(0, 2))
        
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.entry_ip = ctk.CTkEntry(input_frame, height=28, border_color="#333", fg_color="#111", text_color="white")
        self.entry_ip.pack(side="left", fill="x", expand=True)
        
        ctk.CTkButton(input_frame, text="🔍", width=30, height=28, fg_color=COLORS["accent"], text_color="black", command=self.autodetectar_ip).pack(side="right", padx=(5, 0))

    def accion_detener_hilo(self): threading.Thread(target=self.steam.detener_servidor).start()
    def accion_backup_manual(self): threading.Thread(target=lambda: self.scheduler.ejecutar_tarea("BACKUP")).start()
    
    def accion_reiniciar_hilo(self):
        self.btn_restart.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text=self.lang.get("status_restarting"), text_color="#FFCC00")
        threading.Thread(target=lambda: self.steam.reinicio_seguro(self.log_sistema)).start()

    def autodetectar_ip(self):
        def buscar():
            try: ip = requests.get('https://api.ipify.org').text; self.entry_ip.delete(0, "end"); self.entry_ip.insert(0, ip); self.log_sistema(f"{self.lang.get('log_ip_detected')} {ip}")
            except: self.log_sistema(self.lang.get("error_ip_search"))
        threading.Thread(target=buscar).start()
        
    def toggle_auto_update(self):
        if self.switch_auto.get() == 1:
            self.log_sistema(self.lang.get("log_autoupdate_on"))
            self.scheduler.activar_auto_update(1) 
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
                self.log_sistema("⚠️ WATCHDOG: Ingresa tu Steam Web API Key en la configuración.")
                self.switch_watchdog.deselect()
                return
            self.watchdog.set_api_key(final_key)
            self.lbl_watchdog_status.configure(text="🛡️ Watchdog Activo", text_color=COLORS["success"])
        else:
            self.lbl_watchdog_status.configure(text="")

    def accion_guardar(self):
        # 1. Guardar configuración del juego (ServerSettings.ini)
        datos = { 
            "scum.ServerName": self.entry_name.get(), 
            "scum.ServerDescription": self.entry_desc.get(), 
            "scum.MessageOfTheDay": self.entry_motd.get(), 
            "scum.ServerPassword": self.entry_pass.get(), 
            "scum.MaxPlayers": self.entry_players.get(), 
        }
        self.editor.guardar_configuracion(datos)
        
        # 2. Guardar estado visual (Inputs, incluyendo puertos y Watchdog)
        self.guardar_memoria_visual_en_disco()
        
        self.log_sistema("✅ Configuración guardada. (Puertos aplicados al reiniciar).")

    def cerrar_aplicacion(self):
        self.guardar_memoria_visual_en_disco()
        self.destroy()

    def guardar_memoria_visual_en_disco(self):
        try:
            gui_data = {
                "ip": self.entry_ip.get(),
                "port": self.entry_port.get(),
                "query": self.entry_query.get(),
                "name": self.entry_name.get(),
                "desc": self.entry_desc.get(),
                "motd": self.entry_motd.get(),
                "pass": self.entry_pass.get(),
                "players": self.entry_players.get(),
                "auto_update": self.switch_auto.get(),
                "lang": self.lang.current_lang,
                "steam_api_key": self.entry_api_key.get().strip(),
                "watchdog_enabled": self.switch_watchdog.get()
            }
            
            # Actualizar Watchdog Key al guardar
            final_key = gui_data["steam_api_key"]
            if not final_key or "TU_API_KEY" in final_key: final_key = STEAM_API_KEY
            
            self.watchdog.set_api_key(final_key)
            if gui_data["watchdog_enabled"] == 1 and (not final_key or "TU_API_KEY" in final_key):
                 self.switch_watchdog.deselect()
                 gui_data["watchdog_enabled"] = 0
                 self.log_sistema("⚠️ Watchdog desactivado. Falta API Key.")

            with open(self.gui_settings_file, 'w') as f: json.dump(gui_data, f)
        except: pass

    def guardar_memoria_visual(self): self.guardar_memoria_visual_en_disco()

    def cargar_memoria_visual(self):
        if not os.path.exists(self.gui_settings_file): return
        try:
            with open(self.gui_settings_file, 'r') as f: datos = json.load(f)
            if "auto_update" in datos and datos["auto_update"] == 1: self.switch_auto.select(); self.toggle_auto_update()
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

            def rellenar(entry, key): 
                if key in datos and datos[key]: entry.delete(0, "end"); entry.insert(0, datos[key])
            rellenar(self.entry_name, "name"); rellenar(self.entry_desc, "desc"); rellenar(self.entry_motd, "motd"); rellenar(self.entry_ip, "ip"); rellenar(self.entry_port, "port"); rellenar(self.entry_query, "query"); rellenar(self.entry_pass, "pass"); rellenar(self.entry_players, "players")
        except: pass
"""

part2 = """    def construir_scheduler(self):
        for w in self.frame_profiles.winfo_children(): w.destroy()
        
        # --- ZONA A: GESTIÓN DE BIBLIOTECA (Top) ---
        frame_top = ctk.CTkFrame(self.frame_profiles, fg_color=COLORS["panel"], corner_radius=10)
        frame_top.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame_top, text=self.lang.get("prof_library"), font=("Roboto", 14, "bold"), text_color=COLORS["text_main"]).pack(side="left", padx=15, pady=10)
        
        # Combo de perfiles existentes
        self.combo_perfiles_lib = ctk.CTkComboBox(frame_top, values=list(self.scheduler.perfiles.keys()), width=200)
        self.combo_perfiles_lib.pack(side="left", padx=10)

        # --- ZONA B: MESA DE TRABAJO (Centro) ---
        # Aquí se listan las filas editables
        self.frame_workbench = ctk.CTkScrollableFrame(self.frame_profiles, fg_color="#151515", label_text=self.lang.get("prof_workbench"))
        self.frame_workbench.pack(fill="both", expand=True, padx=20, pady=5)

        # Diccionario para rastrear los Entry widgets: { "SettingName": EntryWidget, ... }
        self.workbench_rows = [] 

        # --- ZONA C: AGREGADOR DE REGLAS (Bottom) ---
        frame_adder = ctk.CTkFrame(self.frame_profiles, fg_color=COLORS["panel"])
        frame_adder.pack(fill="x", padx=20, pady=10)
        
        # Lógica de categorías (igual que antes)
        cats_traducidas = []
        self.cat_translation_map = {} 
        for cat_key in DATABASE_SETTINGS.keys():
            texto = self.lang.get(cat_key)
            cats_traducidas.append(texto)
            self.cat_translation_map[texto] = cat_key
            
        self.combo_categoria = ctk.CTkComboBox(frame_adder, values=cats_traducidas, width=200, command=self.actualizar_dropdown_settings)
        self.combo_categoria.pack(side="left", padx=10, pady=10)
        
        self.combo_settings = ctk.CTkComboBox(frame_adder, values=[], width=250)
        self.combo_settings.pack(side="left", padx=10)
        
        if cats_traducidas: self.actualizar_dropdown_settings(cats_traducidas[0])
        
        self.entry_setting_value = ctk.CTkEntry(frame_adder, width=100, placeholder_text="Val")
        self.entry_setting_value.pack(side="left", padx=10)
        
        ctk.CTkButton(frame_adder, text="+", width=40, fg_color=COLORS["success"], text_color="black", command=self.accion_agregar_fila_editable).pack(side="left", padx=10)

        # --- ZONA D: ACCIÓN FINAL (Footer) ---
        frame_footer = ctk.CTkFrame(self.frame_profiles, fg_color="transparent")
        frame_footer.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame_footer, text=self.lang.get("prof_name_lbl")).pack(side="left", padx=5)
        self.entry_perfil_nombre_v2 = ctk.CTkEntry(frame_footer, width=200, placeholder_text="MY_PROFILE")
        self.entry_perfil_nombre_v2.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_footer, text=self.lang.get("prof_save_btn"), width=150, fg_color=COLORS["accent"], text_color="black", command=self.accion_guardar_perfil_v2).pack(side="right", padx=5)

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

    def accion_cargar_mesa_trabajo(self):
        nombre = self.combo_perfiles_lib.get()
        if not nombre or nombre not in self.scheduler.perfiles: return
        
        self.limpiar_mesa_trabajo()
        self.entry_perfil_nombre_v2.insert(0, nombre)
        
        datos = self.scheduler.perfiles[nombre]
        for key, value in datos.items():
            # Intentar buscar el nombre bonito
            nombre_bonito = key 
            for cat, items in DATABASE_SETTINGS.items():
                if key in items:
                    lang_key = items[key]
                    nombre_bonito = self.lang.get(lang_key)
                    break
            self.crear_fila_visual(key, nombre_bonito, value)

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

    def accion_guardar_perfil_v2(self):
        nombre = self.entry_perfil_nombre_v2.get().upper().strip()
        if not nombre: return
        self.combo_perfiles_lib.configure(values=nuevos_valores)
        self.combo_perfiles_lib.set(nombre)
        
        # Actualizar combo en Tasks también si existe
        if hasattr(self, 'combo_perfiles'):
            vals_task = ["RESTART", "BACKUP"] + nuevos_valores
            self.combo_perfiles.configure(values=vals_task)
            self.combo_editar_perfil.configure(values=nuevos_valores)

        self.log_sistema(f"{self.lang.get('success_profile_saved')} '{nombre}'")

    def accion_eliminar_perfil_v2(self):
        nombre = self.combo_perfiles_lib.get()
        if not nombre: return
        
        if self.scheduler.borrar_perfil(nombre):
            self.limpiar_mesa_trabajo()
            nuevos_valores = list(self.scheduler.perfiles.keys())
            self.combo_perfiles_lib.configure(values=nuevos_valores)
            if nuevos_valores: self.combo_perfiles_lib.set(nuevos_valores[0])
            else: self.combo_perfiles_lib.set("")
            
            # Actualizar combo en Tasks
            if hasattr(self, 'combo_perfiles'):
                vals_task = ["RESTART", "BACKUP"] + nuevos_valores
                self.combo_perfiles.configure(values=vals_task)
                self.combo_editar_perfil.configure(values=nuevos_valores)
                
            self.log_sistema(f"{self.lang.get('success_profile_deleted')} ({nombre})")


    def construir_tasks(self):
        for w in self.frame_tasks.winfo_children(): w.destroy()
        ctk.CTkLabel(self.frame_tasks, text=self.lang.get("task_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=20, padx=30, anchor="w")
        frame_prog = ctk.CTkFrame(self.frame_tasks, fg_color=COLORS["panel"]); frame_prog.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(frame_prog, text=self.lang.get("task_new"), font=("Roboto", 14, "bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=15, pady=10)
        row_clock = ctk.CTkFrame(frame_prog, fg_color="transparent"); row_clock.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row_clock, text=self.lang.get("task_at")).pack(side="left", padx=5)
        self.entry_hora = ctk.CTkEntry(row_clock, width=80, placeholder_text="HH:MM"); self.entry_hora.pack(side="left", padx=5)
        ctk.CTkLabel(row_clock, text=self.lang.get("task_run")).pack(side="left", padx=5)
        opciones = ["RESTART", "BACKUP"] + list(self.scheduler.perfiles.keys())
        self.combo_perfiles = ctk.CTkComboBox(row_clock, values=opciones, width=200); self.combo_perfiles.pack(side="left", padx=5)
        btn_del_profile = ctk.CTkButton(row_clock, text=self.lang.get("task_del_btn"), width=100, fg_color=COLORS["danger"], command=self.accion_borrar_perfil_seleccionado); btn_del_profile.pack(side="left", padx=15)
        ctk.CTkButton(row_clock, text=self.lang.get("task_active_btn"), width=140, command=self.accion_programar).pack(side="right", padx=15)
        ctk.CTkLabel(self.frame_tasks, text=self.lang.get("task_list_title"), font=("Roboto", 14)).pack(pady=(20,5), padx=30, anchor="w")
        self.lista_tareas = ctk.CTkScrollableFrame(self.frame_tasks, fg_color="#111", height=300); self.lista_tareas.pack(fill="both", expand=True, padx=20, pady=5)
        for t in self.scheduler.tareas: self.dibujar_tarea_en_lista(t)

    def accion_borrar_perfil_seleccionado(self):
        perfil_a_borrar = self.combo_perfiles.get()
        if perfil_a_borrar in ["RESTART", "BACKUP"]: self.log_sistema("❌ No puedes eliminar funciones del sistema."); return
        if self.scheduler.borrar_perfil(perfil_a_borrar):
            nuevos_valores = ["RESTART", "BACKUP"] + list(self.scheduler.perfiles.keys())
            self.combo_perfiles.configure(values=nuevos_valores); self.combo_perfiles.set(nuevos_valores[0])
            self.combo_editar_perfil.configure(values=list(self.scheduler.perfiles.keys()))
            self.log_sistema(f"{self.lang.get('success_profile_deleted')} ({perfil_a_borrar})")
    def accion_programar(self):
        hora = self.entry_hora.get().strip(); perfil = self.combo_perfiles.get()
        if len(hora) == 4 and hora.isdigit(): hora = f"{hora[:2]}:{hora[2:]}"
        if ":" not in hora: self.log_sistema("❌ Error: Formato de hora inválido. Usa HH:MM"); return
        tarea = self.scheduler.programar_tarea(hora, perfil)
        if tarea: 
            self.dibujar_tarea_en_lista(tarea)
            self.log_sistema(f"{self.lang.get('success_task_saved')} {perfil} @ {hora}")
            self.entry_hora.delete(0, "end")
    def dibujar_tarea_en_lista(self, tarea):
        row = ctk.CTkFrame(self.lista_tareas, fg_color=COLORS["panel"]); row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=f"⏰ {tarea['hora']}", font=("Consolas", 14, "bold"), text_color="#E0A800", width=60).pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"PERFIL: {tarea['perfil']}", font=("Roboto", 12)).pack(side="left", padx=10)
        ctk.CTkButton(row, text="🗑", width=30, fg_color=COLORS["danger"], command=lambda: self.borrar_tarea_visual(row, tarea['id'])).pack(side="right", padx=10, pady=5)
    def borrar_tarea_visual(self, frame, job_id): self.scheduler.eliminar_tarea(job_id); frame.destroy()
    
    def construir_users(self):
        for w in self.frame_users.winfo_children(): w.destroy()
        ctk.CTkLabel(self.frame_users, text=self.lang.get("user_title"), font=("Roboto", 24, "bold"), text_color=COLORS["text_main"]).pack(pady=20, padx=30, anchor="w")
        panel_input = ctk.CTkFrame(self.frame_users, fg_color=COLORS["panel"]); panel_input.pack(fill="x", padx=20, pady=10)
        row1 = ctk.CTkFrame(panel_input, fg_color="transparent"); row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text=self.lang.get("user_steamid")).pack(side="left", padx=5)
        self.entry_user_id = ctk.CTkEntry(row1, width=200, placeholder_text="76561198..."); self.entry_user_id.pack(side="left", padx=5)
        ctk.CTkLabel(row1, text=self.lang.get("user_hours")).pack(side="left", padx=5)
        self.entry_user_hours = ctk.CTkEntry(row1, width=80); self.entry_user_hours.insert(0, "-1"); self.entry_user_hours.pack(side="left", padx=5)
        row2 = ctk.CTkFrame(panel_input, fg_color="transparent"); row2.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(row2, text=self.lang.get("user_notes")).pack(side="left", padx=5)
        self.entry_user_notes = ctk.CTkEntry(row2, width=300, placeholder_text=self.lang.get("placeholder_notes")); self.entry_user_notes.pack(side="left", padx=5)
        btn_ban = ctk.CTkButton(row2, text=self.lang.get("btn_add_ban"), fg_color=COLORS["danger"], command=lambda: self.accion_agregar_usuario("BAN")); btn_ban.pack(side="right", padx=10)
        btn_vip = ctk.CTkButton(row2, text=self.lang.get("btn_add_vip"), fg_color="#FFD700", text_color="black", hover_color="#C6A700", command=lambda: self.accion_agregar_usuario("VIP")); btn_vip.pack(side="right", padx=10)
        panel_listas = ctk.CTkFrame(self.frame_users, fg_color="transparent"); panel_listas.pack(fill="both", expand=True, padx=20, pady=10)
        frame_bans = ctk.CTkFrame(panel_listas, fg_color=COLORS["panel"]); frame_bans.pack(side="left", fill="both", expand=True, padx=(0,5))
        ctk.CTkLabel(frame_bans, text=self.lang.get("list_active_bans"), font=("Roboto", 12, "bold"), text_color=COLORS["danger"]).pack(pady=5)
        self.lista_visual_bans = ctk.CTkScrollableFrame(frame_bans, fg_color="transparent"); self.lista_visual_bans.pack(fill="both", expand=True, padx=5, pady=5)
        frame_vips = ctk.CTkFrame(panel_listas, fg_color=COLORS["panel"]); frame_vips.pack(side="right", fill="both", expand=True, padx=(5,0))
        ctk.CTkLabel(frame_vips, text=self.lang.get("list_active_vips"), font=("Roboto", 12, "bold"), text_color="#FFD700").pack(pady=5)
        self.lista_visual_vips = ctk.CTkScrollableFrame(frame_vips, fg_color="transparent"); self.lista_visual_vips.pack(fill="both", expand=True, padx=5, pady=5)
        self.refrescar_lista_usuarios()

    def accion_agregar_usuario(self, tipo):
        steam_id = self.entry_user_id.get().strip()
        try: horas = int(self.entry_user_hours.get().strip())
        except: self.log_sistema(self.lang.get("error_hours_int")); return
        notas = self.entry_user_notes.get().strip()
        if len(steam_id) < 10: self.log_sistema(self.lang.get("error_steam_id")); return
        self.users.agregar_usuario(tipo, steam_id, horas, notas); self.entry_user_id.delete(0, "end"); self.entry_user_notes.delete(0, "end"); self.refrescar_lista_usuarios()

    def refrescar_lista_usuarios(self):
        for w in self.lista_visual_bans.winfo_children(): w.destroy()
        for w in self.lista_visual_vips.winfo_children(): w.destroy()
        self.users.db = self.users.cargar_db()
        for u in self.users.db:
            target_list = self.lista_visual_bans if u["tipo"] == "BAN" else self.lista_visual_vips
            color_borde = COLORS["danger"] if u["tipo"] == "BAN" else "#FFD700"
            card = ctk.CTkFrame(target_list, fg_color="#1a1a1a", border_width=1, border_color=color_borde); card.pack(fill="x", pady=2, padx=2)
            info_text = f"{u['id']}\\nExpira: {u['expira']}"
            if u['notas']: info_text += f"\\nNote: {u['notas']}"
            lbl = ctk.CTkLabel(card, text=info_text, font=("Consolas", 11), justify="left", anchor="w"); lbl.pack(side="left", padx=5, pady=5)
            btn_del = ctk.CTkButton(card, text="X", width=30, height=20, fg_color="#333", hover_color=COLORS["danger"], command=lambda k=u['tipo'], i=u['id']: self.borrar_usuario_ui(k, i)); btn_del.pack(side="right", padx=5)

    def borrar_usuario_ui(self, tipo, steam_id):
        self.users.remover_usuario(tipo, steam_id); self.refrescar_lista_usuarios()

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

    def construir_logs(self):
        for w in self.frame_logs.winfo_children(): w.destroy()
        ctk.CTkLabel(self.frame_logs, text=self.lang.get("menu_logs"), font=("Roboto", 20, "bold"), text_color=COLORS["text_main"]).pack(pady=(20, 10), padx=20, anchor="w")
        self.big_console_tab = ctk.CTkTextbox(self.frame_logs, fg_color="#000000", text_color="#00FF00", font=("Consolas", 12), activate_scrollbars=True)
        self.big_console_tab.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.big_console_tab.insert("0.0", f"{self.lang.get('log_monitor_started')}\\n")

    def iniciar_conteo_easter(self, event):
        if self.timer_easter: self.after_cancel(self.timer_easter)
        self.timer_easter = self.after(5000, self.mostrar_ventana_creditos)

    def cancelar_conteo_easter(self, event):
        if self.timer_easter: self.after_cancel(self.timer_easter)
        self.timer_easter = None

    def mostrar_ventana_creditos(self):
        self.timer_easter = None
        base_path = os.path.join(os.getcwd(), "favicon_io")
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
            self.consultar_jugadores_reales()
        else:
            self.server_is_fully_loaded = False; self.player_count_log = 0
            self.lbl_status.configure(text=self.lang.get("status_offline"), text_color=COLORS["danger"])
            self.lbl_players.configure(text=f"{self.lang.get('label_players')} ---", text_color="gray")
            self.btn_start.configure(state="normal", fg_color=COLORS["success"], text=f"▶ {self.lang.get('btn_start')}")
            self.btn_stop.configure(state="disabled", fg_color="#2b2b2b", text=self.lang.get("btn_status_stopped"))
        
        self.after(2000, self.monitor_loop)

    def consultar_jugadores_reales(self):
        if not self.server_is_fully_loaded: return
        def _consulta():
            try:
                ip = self.entry_ip.get(); port = int(self.entry_query.get())
                info = a2s.info((ip, port), timeout=2)
                self.lbl_players.configure(text=f"{self.lang.get('label_players')} {info.player_count}/{info.max_players}", text_color="white")
            except: pass
        threading.Thread(target=_consulta).start()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = VoidWindow()
    app.mainloop()
"""

full = part1 + "\n" + missing + "\n" + part2
with open("src/ui/main_window.py", "w", encoding="utf-8") as f:
    f.write(full)
