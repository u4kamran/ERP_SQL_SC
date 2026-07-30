@echo off
title Start ERP Website (App + Cloudflare)
cd /d "%~dp0"

echo.
echo  ========================================
echo   Shafique Departmental Store ERP
echo   Starting website for public access
echo  ========================================
echo.
echo  Public URL: https://erp.ahsteellab.com
echo.
echo  Keep this window OPEN.
echo  To stop: run STOP-APP.bat
echo.

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL.bat first.
    pause
    exit /b 1
)

set "CF_EXE=deploy\cloudflared\bin\cloudflared.exe"
if not exist "%CF_EXE%" set "CF_EXE=C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not exist "%CF_EXE%" (
    echo ERROR: cloudflared not found. Website will NOT work from internet.
    echo Install cloudflared or copy to deploy\cloudflared\bin\
    pause
    exit /b 1
)

echo [1] Starting ERP app watchdog...
start "ERP Watchdog" /MIN cmd /c "cd /d %~dp0 && venv\Scripts\python.exe scripts\app_watchdog.py"
timeout /t 5 /nobreak >nul

echo [2] Starting Cloudflare tunnel (erp.ahsteellab.com)...
taskkill /F /IM cloudflared.exe >nul 2>&1
start "Cloudflare Tunnel" /MIN cmd /c "cd /d %~dp0 && "%CF_EXE%" tunnel --config deploy\cloudflared\config.yml run"

echo.
echo  Wait 15 seconds, then open:
echo    https://erp.ahsteellab.com/login
echo.
echo  Local test: http://127.0.0.1:8000/health
echo.
pause
