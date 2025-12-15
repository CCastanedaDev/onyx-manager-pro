# VOID SCUM MANAGER (ONYX MANAGER) 🛡️

**VOID SCUM MANAGER** is an advanced and comprehensive administrative tool designed to streamline the installation, configuration, and management of **SCUM** dedicated servers on Windows environments. 

Developed in Python with a modern graphical interface (CustomTkinter), this application allows server administrators to control every aspect of their server without interacting with complex console scripts or manually editing error-prone configuration files.

## 🚀 Key Features

### 1. Automated Server Management
* **Simplified Installation & Updates**: Automatically downloads and installs the SCUM dedicated server using integrated SteamCMD. Detects new versions and allows one-click updates.
* **Total Control**: Intuitive buttons to **Start**, **Stop**, and **Restart** the server.
* **Safe Shutdown (Anti-Corruption)**: Implements an advanced shutdown system that injects termination signals (`CTRL+C`) directly into the server process via Windows API. This ensures the server saves the player database before closing, preventing data corruption and progress rollbacks.
* **Watchdog**: Constant monitoring system that automatically restarts the server if a crash is detected.

### 2. Visual Configuration Editor
* No more manual editing of `ServerSettings.ini`. The manager offers a visual interface organized by categories (World, PvP, Vehicles, etc.) to modify server variables.
* **Supported Settings**:
    * Experience and damage multipliers.
    * Day/night cycle configuration.
    * Building restrictions and zones.
    * Vehicle settings (fuel consumption, battery).
    * And much more.

### 3. Raid Scheduler
* Dedicated graphical editor for `RaidTimes.json`.
* Configure allowed raid schedules for each day of the week individually.
* Simple interface to toggle days on/off and define time windows (e.g., "18:00-22:00").

### 4. Modern UI & Multi-language
* **Dark Mode UI**: Designed with `customtkinter` for a pleasant and modern visual experience.
* **Multi-language**: Support for multiple languages (Spanish, English, Russian, etc.), allowing instant interface language switching.
* **Live Console**: Real-time visualization of server and system logs within the application, facilitating debugging and monitoring.

### 5. Advanced Tools
* **Backup Management**: System to manage server data backups.
* **IP Detection**: Utility to auto-detect the server's public IP.
* **Multi-threading**: The interface remains responsive while the server loads or updates thanks to threading implementation.

## 🛠 System Requirements

* **Operating System**: Windows 10/11 (64-bit).
* **Game**: SCUM Dedicated Server License (AppID 3792580).
* **Internet Connection**: Required for downloading SteamCMD files and server updates.

## 🔧 Installation & Usage

1.  **Download**: Get the latest version from the **Releases** section (or clone this repository).
2.  **Run**: Open `VOID_MANAGER.exe` (or run `main.py` if using source code).
3.  **Install Server**: If it's the first run, the manager will detect the missing server and offer to install it. Click the Install/Update button.
4.  **Configure**: Go to the settings tab to define your server name, password, and game rules.
5.  **Play**: Start the server from the Dashboard and wait for "Server is running".

## 💻 Technical Details

The project is built using the following technologies:

* **Language**: Python 3.x
* **GUI**: `customtkinter` (based on Tkinter).
* **Process Management**: `psutil`, `subprocess`, `ctypes` (for Windows signal handling).
* **Web Interaction**: `requests` (to query Steam APIs).
* **Data Management**: `json` (for configuration persistence).
* **Packaging**: PyInstaller & Inno Setup (to create the .exe installer).

---

**Disclaimer**: This project is a third-party tool and is not officially affiliated with Gamepires or Jagex.

## 📂 Project Structure

The project is organized to facilitate maintenance and scalability:

* `src/`: Contains all core application source code.
    * `logic/`: "Backend" modules handling server logic, SteamCMD, file management, backups, etc.
    * `ui/`: GUI modules (`customtkinter`), windows, and visual components.
* `data/`: Static files and resources.
    * `lang/`: JSON files for multi-language support.
    * `assets/`: Images, icons, and other visual resources.
* `dev_tools/`: Utility scripts for development and maintenance (syntax checking, restoration, etc.). Not required for normal application usage.
* `installer_langs/`: Translation files for the Inno Setup installer.
* `main.py`: **Entry Point**. Run this file to start the application from source.
* `COMPILAR.bat`: Batch script to compile the application into an executable (.exe).
