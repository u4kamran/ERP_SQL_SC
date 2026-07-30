@echo off
title AH Steel Lab - Website
color 0B
echo.
echo  Starting AH Steel Lab website...
echo  Public URL: https://app.ahsteellab.com
echo.
echo  Keep this window OPEN. Closing it stops the website.
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo  ERROR: Not installed yet. Double-click INSTALL.bat first.
    pause
    exit /b 1
)

if not exist ".env" (
    echo  ERROR: .env not found. Run INSTALL.bat first.
    pause
    exit /b 1
)

if not exist "deploy\cloudflared\config.yml" (
    echo  Cloudflare not configured yet.
    echo  Run INSTALL.bat and choose Y for Cloudflare setup.
    pause
    exit /b 1
)

set "CF_EXE="
if exist "deploy\cloudflared\bin\cloudflared.exe" (
    set "CF_EXE=deploy\cloudflared\bin\cloudflared.exe"
) else if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
    set "CF_EXE=C:\Program Files (x86)\cloudflared\cloudflared.exe"
) else (
    echo  ERROR: cloudflared not found. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    pause
    exit /b 1
)

start "AH Steel Lab App" cmd /k "cd /d %~dp0 && venv\Scripts\python.exe run.py"
timeout /t 4 /nobreak >nul
start "Cloudflare Tunnel" cmd /k "cd /d %~dp0 && "%CF_EXE%" tunnel --config deploy\cloudflared\config.yml run"

echo.
echo  Website is starting...
echo  Open: https://app.ahsteellab.com/login
echo.
pause
