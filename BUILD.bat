@echo off
echo.
echo -------------------------------------------------------
echo   ONYX MANAGER PRO - AUTO BUILD
echo -------------------------------------------------------
echo.

echo [1/5] Instalando dependencias Python...
pip install customtkinter requests psutil python-a2s schedule watchdog pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias.
    pause
    exit /b 1
)
echo OK - Dependencias instaladas.
echo.

echo [2/5] Limpiando compilaciones anteriores...
if exist "build"             rmdir /s /q "build"
if exist "dist"              rmdir /s /q "dist"
if exist "ONYX MANAGER.spec" del /q "ONYX MANAGER.spec"
echo OK.
echo.

echo [3/5] Compilando ejecutable (puede tardar 3-5 minutos)...
pyinstaller --noconfirm --onedir --windowed --uac-admin --name "ONYX MANAGER" --icon "favicon_io/favicon.ico" --clean --add-data "data;data" --add-data "favicon_io;favicon_io" --hidden-import "customtkinter" --hidden-import "PIL._tkinter_finder" --hidden-import "a2s" --hidden-import "psutil" --hidden-import "schedule" --hidden-import "watchdog.observers" --hidden-import "watchdog.events" --hidden-import "watchdog.observers.winapi" --hidden-import "requests" main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: La compilacion fallo. Revisa los errores arriba.
    pause
    exit /b 1
)
echo OK - Compilacion exitosa.
echo.

echo [4/5] Copiando recursos...
if exist "data"       xcopy "data"       "dist\ONYX MANAGER\data\"       /E /I /Y /Q
if exist "steamcmd"   xcopy "steamcmd"   "dist\ONYX MANAGER\steamcmd\"   /E /I /Y /Q
if exist "favicon_io" xcopy "favicon_io" "dist\ONYX MANAGER\favicon_io\" /E /I /Y /Q
echo OK.
echo.

echo [5/5] Creando nota LEEME.txt...
echo ONYX MANAGER PRO - Como usar > "dist\ONYX MANAGER\LEEME.txt"
echo. >> "dist\ONYX MANAGER\LEEME.txt"
echo Coloca la carpeta "ONYX MANAGER" junto a tu carpeta SCUM_Server: >> "dist\ONYX MANAGER\LEEME.txt"
echo. >> "dist\ONYX MANAGER\LEEME.txt"
echo   MiServidor/ >> "dist\ONYX MANAGER\LEEME.txt"
echo   +-- ONYX MANAGER/         (esta carpeta) >> "dist\ONYX MANAGER\LEEME.txt"
echo   +-- SCUM_Server/          (tu servidor SCUM) >> "dist\ONYX MANAGER\LEEME.txt"
echo. >> "dist\ONYX MANAGER\LEEME.txt"
echo Ejecuta "ONYX MANAGER.exe" como Administrador. >> "dist\ONYX MANAGER\LEEME.txt"
echo.

echo -------------------------------------------------------
echo   BUILD COMPLETADO
echo   Ejecutable en: dist\ONYX MANAGER\ONYX MANAGER.exe
echo -------------------------------------------------------
echo.
explorer "dist\ONYX MANAGER"
pause
