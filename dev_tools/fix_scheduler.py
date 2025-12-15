
import os

file_path = "c:/Users/stink/Desktop/VOID_SCUM_MANAGER/src/ui/main_window.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_scheduler = False
scheduler_replaced = False

scheduler_code = """    def construir_scheduler(self):
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
        
        contenido_ini = ""
        for row in self.workbench_rows:
            k = row["key"]
            v = row["entry"].get().strip()
            contenido_ini += f"{k}={v}\n"
            
        self.scheduler.crear_perfil(nombre, contenido_ini)
        
        # Actualizar combos
        nuevos_valores = list(self.scheduler.perfiles.keys())
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

"""

for line in lines:
    if "def construir_scheduler(self):" in line:
        in_scheduler = True
        if not scheduler_replaced:
            new_lines.append(scheduler_code + "\n")
            scheduler_replaced = True
        continue
    
    if "def construir_tasks(self):" in line:
        in_scheduler = False
        new_lines.append(line)
        continue
        
    if in_scheduler:
        continue
        
    new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("File fixed successfully.")
