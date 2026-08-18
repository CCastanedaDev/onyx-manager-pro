import threading
import time
import json
import os
import schedule
import uuid
import subprocess
from datetime import datetime
from src.logic.backup_manager import BackupManager

class TaskManager:
    def __init__(self, steam_handler, log_callback, config_editor, base_path=None, stats_shop=None):
        self.steam = steam_handler
        self.log = log_callback
        self.editor = config_editor
        self.backup_mgr = BackupManager(self.log)
        self.stats_shop = stats_shop
        
        self.running = True
        # Serializa la ejecución de tareas automáticas: NUNCA dos a la vez.
        # Evita que un perfil y un RESTART (o dos tareas a la misma hora) se
        # pisen entre sí y dejen el servidor colgado o el INI corrupto.
        self._task_lock = threading.Lock()
        root_dir = base_path if base_path else os.getcwd()
        self.tasks_file = os.path.join(root_dir, "data", "tasks.json")
        self.profiles_file = os.path.join(root_dir, "data", "profiles.json")
        self.state_file = os.path.join(root_dir, "data", "scheduler_state.json")
        
        self.tareas = [] 
        self.perfiles = {}
        self.job_auto_update = None
        # Último perfil aplicado: persistente en disco para sobrevivir reinicios de la app.
        self.ultimo_perfil_aplicado = self._cargar_estado_perfil()

        # Limpiar cualquier trabajo previo en la librería schedule (Global)
        schedule.clear()
        self.log("🧹 Scheduler: Limpieza de tareas previas completada.")

        self.cargar_perfiles()
        self.cargar_tareas_guardadas()
        
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def run_scheduler(self):
        while self.running:
            try:
                schedule.run_pending()
            except Exception as e:
                # NUNCA dejar morir el hilo del scheduler: si un disparo falla,
                # lo registramos y seguimos para no perder los reinicios futuros.
                self.log(f"⚠️ [Scheduler] Error en run_pending (continuando): {e}")
            time.sleep(1)

    def programar_tarea(self, hora_str, nombre_perfil, dias=None, task_id=None):
        try: datetime.strptime(hora_str, "%H:%M")
        except ValueError: return None

        # Si dias es None o vacío, asumimos todos los días (comportamiento legacy)
        if not dias: dias = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        # Si no nos dan ID (nueva tarea), generamos uno. Si nos dan (carga), lo usamos.
        if not task_id:
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
        threading.Thread(target=self.ejecutar_tarea, args=(nombre_perfil,), daemon=True).start()

    def _cargar_estado_perfil(self):
        """Carga el último perfil aplicado desde disco (persiste entre reinicios de la app)."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return data.get("ultimo_perfil_aplicado", None)
        except: pass
        return None

    def _guardar_estado_perfil(self, nombre_perfil):
        """Persiste el último perfil aplicado en disco."""
        try:
            data = {"ultimo_perfil_aplicado": nombre_perfil}
            with open(self.state_file, 'w') as f:
                json.dump(data, f)
        except: pass

    def ejecutar_tarea(self, nombre_perfil):
        # Serializar: una tarea automática a la vez. Si ya hay otra en curso,
        # esta espera su turno en vez de pisarla (evita races de INI y de
        # arranque/parada que dejaban el servidor colgado).
        with self._task_lock:
            self._ejecutar_tarea_impl(nombre_perfil)

    def _ejecutar_tarea_impl(self, nombre_perfil):
        self.log(f"⚡ [AUTO] EJECUTANDO TAREA: {nombre_perfil}")
        try:
            if nombre_perfil == "BACKUP":
                self.log(">> Iniciando copia de seguridad automática...")
                self.backup_mgr.crear_backup()
            
            elif nombre_perfil == "RESTART":
                # --- LÓGICA DE REINICIO UNIFICADA ---
                # Si se aplicó un perfil antes (incluso en una sesión anterior de la app),
                # lo re-aplicamos DESPUÉS del shutdown para que siempre gane.
                perfil_activo = self.ultimo_perfil_aplicado
                
                def _callback_post_stop():
                    # Si hay perfil activo, re-aplicar
                    if perfil_activo and perfil_activo in self.perfiles:
                        self.log(f"   [Re-Apply] Escribiendo perfil '{perfil_activo}' en el INI...")
                        contenido = dict(self.perfiles[perfil_activo])
                        self.editor.guardar_configuracion(contenido)
                    
                    # Si hay stats shop, verificar vencimientos y procesar pendientes
                    if self.stats_shop:
                        try:
                            self.log("🛒 [StatsShop] Verificando suscripciones vencidas...")
                            self.stats_shop.verificar_vencimientos()
                            self.log("🛒 [StatsShop] Aplicando cambios pendientes en la base de datos...")
                            self.stats_shop.ejecutar_pendientes()
                        except Exception as ex:
                            self.log(f"❌ [StatsShop] Error procesando base de datos: {ex}")

                self.steam.reinicio_seguro(self.log, post_stop_callback=_callback_post_stop)

                # Vigilante dedicado SOLO para reinicios automáticos: confirma que
                # el servidor realmente arrancó (y se sostiene durante la carga) y,
                # si no, lo vuelve a iniciar. El reinicio manual no usa esto.
                self.steam.vigilar_arranque_post_reinicio(self.log)
                
            elif nombre_perfil in self.perfiles:
                self.log(f">> [AUTO] Aplicando perfil de configuración: {nombre_perfil}")
                contenido = self.perfiles[nombre_perfil]
                
                # NUEVA LÓGICA: Solo escribir el INI directamente.
                # El servidor SCUM puede leer algunos cambios de INI en caliente.
                # Si hay un RESTART programado después, él re-aplicará el perfil
                # DESPUÉS del shutdown (garantizando que el INI no sea sobreescrito por SCUM).
                self.log(f">> Escribiendo configuración del perfil '{nombre_perfil}' en el INI...")
                self.editor.guardar_configuracion(contenido)
                
                # Registrar el perfil activo en memoria Y en disco para que RESTART lo sepa
                # incluso si la app se reinicia entre medio.
                self.ultimo_perfil_aplicado = nombre_perfil
                self._guardar_estado_perfil(nombre_perfil)
                self.log(f"✅ Perfil '{nombre_perfil}' aplicado. El próximo RESTART lo re-aplicará post-shutdown.")
            
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
        # Soporte para archivo legado schedule.json (migración automática)
        ruta_a_leer = self.tasks_file
        legacy_file = os.path.join(os.path.dirname(self.tasks_file), "schedule.json")
        if not os.path.exists(self.tasks_file) and os.path.exists(legacy_file):
            self.log("📋 Migrando tareas del formato antiguo (schedule.json) → tasks.json...")
            ruta_a_leer = legacy_file
        
        if not os.path.exists(ruta_a_leer): return
        try:
            with open(ruta_a_leer, 'r') as f:
                lista = json.load(f)
                for t in lista:
                    # Soporte retrocompatibilidad: si no tiene 'dias', asumimos todos
                    dias = t.get("dias", None)
                    t_id = t.get("id", None)
                    perfil = t.get("perfil", "")
                    # Ignorar perfiles vacíos o que no existen (y avisarlo)
                    if not perfil:
                        continue
                    # Pasamos el ID para conservarlo
                    self.programar_tarea(t["hora"], perfil, dias, task_id=t_id)
            
            # Si era el archivo legado, guardar al nuevo formato automáticamente
            if ruta_a_leer == legacy_file:
                self.guardar_tareas_en_disco()
                self.log("✅ Migración completada. Tareas guardadas en tasks.json.")
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