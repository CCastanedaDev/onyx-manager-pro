@echo off
title ONYX MANAGER - PANEL WEB Y TUNEL
cd /d "%~dp0"
echo ========================================================
echo   ONYX Stats Web Panel Launcher
echo ========================================================
echo.
python run_web_panel_with_tunnel.py
pause
