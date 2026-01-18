import os

file_path = "src/ui/main_window.py"

missing_block = """    def cambiar_idioma(self, lang_code):
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

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Part 1: Lines 0 to 244 (inclusive)
# Line 244 is "        self.frame_admins.grid_forget(); self.frame_ini_editor.grid_forget()"
# In 0-indexed list, line 244 is index 243.
part1 = lines[:244]

# Part 2: Lines 271 to end
# Line 271 is "    def construir_scheduler(self):"
# In 0-indexed list, line 271 is index 270.
part2 = lines[270:]

new_content = "".join(part1) + "\n" + missing_block + "\n" + "".join(part2)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("File reconstructed successfully.")
