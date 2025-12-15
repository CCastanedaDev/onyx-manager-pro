import threading
import time
import json
import os
import schedule
import uuid
from datetime import datetime
from src.logic.backup_manager import BackupManager

class TaskManager:
    def __init__(self, steam_handler, log_callback, config_editor, base_path=None):
        self.steam = steam_handler
        self.log = log_callback
        self.editor = config_editor
        self.backup_mgr = BackupManager(self.log)
        
        self.running = True
        root_dir = base_path if base_path else os.getcwd()
        self.tasks_file = os.path.join(root_dir, "data", "tasks.json")
        self.profiles_file = os.path.join(root_dir, "data", "profiles.json")
        
        self.tareas = [] 
        self.perfiles = {}
        self.job_auto_update = None 

        # Limpiar cualquier trabajo previo en la librería schedule (Global)
        schedule.clear()
        self.log("🧹 Scheduler: Limpieza de tareas previas completada.")

        self.cargar_perfiles()
        self.cargar_tareas_guardadas()
        
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def run_scheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def programar_tarea(self, hora_str, nombre_perfil, dias=None):
        try: datetime.strptime(hora_str, "%H:%M")
        except ValueError: return None

        # Si dias es None o vacío, asumimos todos los días (comportamiento legacy)
        if not dias: dias = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        # Generar ID único para la tarea lógica
        task_id = str(uuid.uuid4())
        created_jobs = []

        # Mapeo de strings a objetos schedule
        for dia in dias:
            dia = dia.lower()
            job_creator = schedule.every()
            
            if dia == "monday": job_creator = job_creator.monday
            elif dia == "tuesday": job_creator = job_creator.tuesday
            elif dia == "wednesday": job_creator = job_creator.wednesday
            elif dia == "thursday": job_creator = job_creator.thursday
            elif dia == "friday": job_creator = job_creator.friday
            elif dia == "saturday": job_creator = job_creator.saturday
            elif dia == "sunday": job_creator = job_creator.sunday
            
            # Crear el job
            if nombre_perfil == "BACKUP":
                job = job_creator.at(hora_str).do(self._lanzar_hilo_tarea, "BACKUP")
            else:
                job = job_creator.at(hora_str).do(self._lanzar_hilo_tarea, nombre_perfil)
            
            created_jobs.append(job)
        
        tarea_info = { 
            "id": task_id, 
            "hora": hora_str, 
            "perfil": nombre_perfil, 
            "dias": dias,
            "jobs": created_jobs 
        }
        
        self.tareas.append(tarea_info)
        self.guardar_tareas_en_disco()
        
        dias_str = ", ".join([d[:3].title() for d in dias])
        self.log(f"📅 Tarea programada: {nombre_perfil} a las {hora_str} ({dias_str})")
        return tarea_info

    def _lanzar_hilo_tarea(self, nombre_perfil):
        threading.Thread(target=self.ejecutar_tarea, args=(nombre_perfil,)).start()

    def ejecutar_tarea(self, nombre_perfil):
        self.log(f"⚡ [AUTO] EJECUTANDO TAREA: {nombre_perfil}")
        try:
            if nombre_perfil == "BACKUP":
                self.log(">> Iniciando copia de seguridad automática...")
                self.backup_mgr.crear_backup()
            
            elif nombre_perfil == "RESTART":
                # --- LÓGICA DE REINICIO UNIFICADA ---
                # Usamos la misma lógica robusta que el botón manual
                self.steam.reinicio_seguro(self.log)
                
            elif nombre_perfil in self.perfiles:
                self.log(f">> Aplicando perfil de configuración: {nombre_perfil}")
                contenido = self.perfiles[nombre_perfil]
                
                # Detener seguro
                self.steam.detener_servidor()
                
                # Aplicar cambios
                self.editor.guardar_configuracion(contenido)
                
                # Espera de seguridad inteligente (Smart Wait Loop)
                self.log("⏳ Esperando cierre del servidor para aplicar perfil...")
                for i in range(60):
                    if not self.steam.esta_corriendo():
                        break
                    time.sleep(1)
                
                self.steam.iniciar_servidor()
            
            self.log(f"✅ [AUTO] TAREA '{nombre_perfil}' COMPLETADA.")
        except Exception as e:
            self.log(f"❌ [ERROR] Falló la tarea {nombre_perfil}: {e}")

    def eliminar_tarea(self, task_id):
        t = next((t for t in self.tareas if t["id"] == task_id), None)
        if t:
            # Cancelar todos los jobs asociados a esta tarea
            for job in t["jobs"]:
                schedule.cancel_job(job)
            
            self.tareas.remove(t)
            self.guardar_tareas_en_disco()
            self.log("🗑 Tarea eliminada del calendario.")

    def crear_perfil(self, nombre, contenido):
        ajustes = {}
        for linea in contenido.split("\n"):
            if "=" in linea:
                k, v = linea.split("=", 1)
                ajustes[k.strip()] = v.strip()
        self.perfiles[nombre] = ajustes
        self.guardar_perfiles()

    def borrar_perfil(self, nombre):
        if nombre in self.perfiles and nombre != "RESTART":
            del self.perfiles[nombre]
            self.guardar_perfiles()
            return True
        return False

    def guardar_perfiles(self):
        try:
            with open(self.profiles_file, 'w') as f: json.dump(self.perfiles, f, indent=4)
        except: pass

    def cargar_perfiles(self):
        if not os.path.exists(self.profiles_file): return
        try:
            with open(self.profiles_file, 'r') as f: self.perfiles = json.load(f)
        except: self.perfiles = {}

    def guardar_tareas_en_disco(self):
        # Guardamos solo los datos serializables (sin los objetos job)
        l = [{"id": t["id"], "hora": t["hora"], "perfil": t["perfil"], "dias": t["dias"]} for t in self.tareas]
        try:
            with open(self.tasks_file, 'w') as f: json.dump(l, f, indent=4)
        except: pass

    def cargar_tareas_guardadas(self):
        if not os.path.exists(self.tasks_file): return
        try:
            with open(self.tasks_file, 'r') as f:
                lista = json.load(f)
                for t in lista:
                    # Soporte retrocompatibilidad: si no tiene 'dias', asumimos todos
                    dias = t.get("dias", None)
                    # Si no tiene ID (legacy), se generará uno nuevo al programar
                    self.programar_tarea(t["hora"], t["perfil"], dias)
        except: pass

    def activar_tarea_recurrente(self, minutos, funcion_callback):
        self.desactivar_auto_update()
        self.job_auto_update = schedule.every(minutos).minutes.do(lambda: threading.Thread(target=funcion_callback).start())

    def activar_auto_update(self, m): 
        self.activar_tarea_recurrente(m, self.steam.chequeo_auto_update)

    def desactivar_auto_update(self):
        if self.job_auto_update:
            schedule.cancel_job(self.job_auto_update)
            self.job_auto_update = None