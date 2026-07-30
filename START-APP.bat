@echo off
title ERP Auto-Start Watchdog
cd /d "%~dp0"

echo.
echo  ========================================
echo   Shafique Departmental Store ERP
echo   Auto-start / auto-restart watchdog
echo  ========================================
echo.
echo  - Starts the app if it is down
echo  - Restarts every 60 seconds if it crashes
echo  - Prevents duplicate copies on port 8000
echo.
echo  To stop the site: run STOP-APP.bat
echo  For PUBLIC website use: START-SITE.bat  (app + Cloudflare tunnel)
echo  URL: https://erp.ahsteellab.com
echo.

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL.bat first.
    pause
    exit /b 1
)

venv\Scripts\python.exe scripts\app_watchdog.py
