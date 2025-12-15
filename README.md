# VOID SCUM MANAGER (ONYX MANAGER)

**VOID SCUM MANAGER** es una herramienta administrativa avanzada y completa diseñada para facilitar la instalación, configuración y gestión de servidores dedicados de **SCUM** en entornos Windows. Desarrollada en Python con una interfaz gráfica moderna (CustomTkinter), esta aplicación permite a los administradores de servidores controlar cada aspecto de su servidor sin necesidad de interactuar con scripts de consola complejos o editar manualmente archivos de configuración propensos a errores.

## 🚀 Características Principales

### 1. Gestión Automática del Servidor
*   **Instalación y Actualización Simplificada**: Descarga e instala automáticamente el servidor dedicado de SCUM utilizando SteamCMD integrado. Detecta nuevas versiones y permite actualizar con un solo clic.
*   **Control Total**: Botones intuitivos para **Iniciar**, **Detener** y **Reiniciar** el servidor.
*   **Cierre Seguro (Safe Shutdown)**: Implementa un sistema avanzado de cierre que inyecta señales de terminación (Ctrl+C) directamente en el proceso del servidor, garantizando que el servidor guarde la base de datos de jugadores antes de cerrarse, evitando la corrupción de datos y pérdidas de progreso ("rollbacks").
*   **Watchdog (Guardián)**: Sistema de monitoreo constante que reinicia automáticamente el servidor si detecta que el proceso se ha cerrado inesperadamente (crashes).

### 2. Editor de Configuración Visual
*   Adiós a la edición manual de `ServerSettings.ini`. El gestor ofrece una interfaz visual organizada por categorías (Mundo, PvP, Vehículos, etc.) para modificar variables del servidor.
*   **Ajustes Soportados**:
    *   Multiplicadores de experiencia y daño.
    *   Configuración de ciclo día/noche.
    *   Restricciones de construcción y zonas.
    *   Ajustes de vehículos (consumo de combustible, batería).
    *   Y mucho más.

### 3. Programador de Raideos (Raid Scheduler)
*   Editor gráfico dedicado para el archivo `RaidTimes.json`.
*   Permite configurar horarios de raideo permitidos para cada día de la semana de forma individual.
*   Interfaz simple para activar/desactivar días y definir ventanas de tiempo (Ej: "18:00-22:00").

### 4. Interfaz Moderna y Multi-idioma
*   **UI Oscura (Dark Mode)**: Diseñada con `customtkinter` para una experiencia visual agradable y moderna.
*   **Multi-idioma**: Soporte para múltiples idiomas (Español, Inglés, Ruso, etc.), permitiendo cambiar el idioma de la interfaz al instante.
*   **Consola en Vivo**: Visualización en tiempo real de los logs del servidor y del sistema dentro de la aplicación, facilitando la depuración y el monitoreo.

### 5. Herramientas Avanzadas
*   **Gestión de Backups**: Sistema para gestionar copias de seguridad de los datos del servidor.
*   **Detección de IP**: Utilidad para autodetectar la IP pública del servidor.
*   **Multi-hilo**: La interfaz no se congela mientras el servidor carga o actualiza gracias al uso de threading.

## 🛠 Requisitos del Sistema

*   **Sistema Operativo**: Windows 10/11 (64-bit).
*   **Juego**: Licencia de SCUM dedicada (AppID 3792580).
*   **Conexión a Internet**: Para descargar archivos de SteamCMD y actualizaciones del servidor.

## 🔧 Instalación y Uso

1.  **Descargar**: Obtén la última versión desde la sección de Releases (o clona este repositorio).
2.  **Ejecutar**: Abre `VOID_MANAGER.exe` (o ejecuta `main.py` si usas el código fuente).
3.  **Instalar Servidor**: Si es la primera vez, el gestor detectará que falta el servidor y te ofrecerá instalarlo. Haz clic en el botón de instalación/actualización.
4.  **Configurar**: Ve a la pestaña de ajustes para definir el nombre de tu servidor, contraseña y reglas de juego.
5.  **Jugar**: Inicia el servidor desde el Dashboard y espera a que aparezca "Server is running".

## 💻 Detalles Técnicos

El proyecto está construido utilizando las siguientes tecnologías:

*   **Lenguaje**: Python 3.x
*   **GUI**: `customtkinter` (basado en Tkinter).
*   **Gestión de Procesos**: `psutil`, `subprocess`, `ctypes` (para manejo de señales de Windows).
*   **Interacción Web**: `requests` (para consultar APIs de Steam).
*   **Gestión de Datos**: `json` (para persistencia de configuraciones).
*   **Empaquetado**: PyInstaller e Inno Setup (para crear el instalador .exe).

---

**Nota**: Este proyecto es una herramienta de terceros y no está afiliada oficialmente con Gamepires ni Jagex.

## 📂 Estructura del Proyecto

El proyecto está organizado de la siguiente manera para facilitar su mantenimiento y escalabilidad:

*   `src/`: Contiene todo el código fuente del núcleo de la aplicación.
    *   `logic/`: Módulos de "backend" que manejan la lógica del servidor, SteamCMD, gestión de archivos, backups, etc.
    *   `ui/`: Módulos de interfaz gráfica (`customtkinter`), ventanas y componentes visuales.
*   `data/`: Archivos estáticos y recursos.
    *   `lang/`: Archivos JSON para el soporte multi-idioma.
    *   `assets/`: Imágenes, iconos y otros recursos visuales.
*   `dev_tools/`: Scripts de utilidad para desarrollo y mantenimiento (verificación de sintaxis, restauración, etc.). No son necesarios para el uso normal de la aplicación.
*   `installer_langs/`: Archivos de traducción para el instalador de Inno Setup.
*   `main.py`: **Punto de entrada**. Ejecute este archivo para iniciar la aplicación desde el código fuente.
*   `COMPILAR.bat`: Script por lotes para compilar la aplicación a un ejecutable (.exe).
