@echo off
echo -------------------------------------------------------
echo   INICIANDO COMPILACION DE ONYX MANAGER PRO (v1.0)
echo -------------------------------------------------------

:: 1. Limpiar rastro de compilaciones previas para evitar errores
echo [1/3] Limpiando archivos antiguos...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ONYX MANAGER.spec" del "ONYX MANAGER.spec"

:: 2. Ejecutar PyInstaller con Admin Mode forzado
echo [2/3] Generando ejecutable con Permisos de Administrador...
:: Flags explicados:
:: --noconfirm: Sobreescribe sin preguntar
:: --onedir: Crea una carpeta (mejor para steamcmd) en vez de un solo archivo lento
:: --windowed: No muestra la consola negra detras
:: --uac-admin: ESTO FORZA EL MODO ADMINISTRADOR SIEMPRE
:: --icon: Pone tu icono
pyinstaller --noconfirm --onedir --windowed --uac-admin --name "ONYX MANAGER" --icon "favicon_io/favicon.ico" --clean main.py

:: 3. Copiar carpetas de recursos (Data, SteamCMD, Iconos)
echo [3/3] Copiando carpetas de recursos (Data, SteamCMD, Favicon)...

:: Copiar DATA (Idiomas, perfiles, etc)
xcopy "data" "dist\ONYX MANAGER\data" /E /I /Y

:: Copiar STEAMCMD (Binarios)
xcopy "steamcmd" "dist\ONYX MANAGER\steamcmd" /E /I /Y

:: Copiar FAVICON_IO (Imagenes del easter egg)
xcopy "favicon_io" "dist\ONYX MANAGER\favicon_io" /E /I /Y

echo -------------------------------------------------------
echo   COMPILACION FINALIZADA
echo   Tu ejecutable esta en la carpeta: dist/ONYX MANAGER/
echo -------------------------------------------------------
echo Build script finished.