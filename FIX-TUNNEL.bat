@echo off
title Fix Cloudflare Tunnel (Error 1033)
color 0E
echo.
echo  Fixing Cloudflare Tunnel for app.ahsteellab.com ...
echo.

cd /d "%~dp0"

taskkill /F /IM cloudflared.exe >nul 2>&1

set "CF_EXE=C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not exist "%CF_EXE%" set "CF_EXE=deploy\cloudflared\bin\cloudflared.exe"

if not exist "%CF_EXE%" (
    echo  cloudflared not found.
    pause
    exit /b 1
)

echo  Starting app on port 8000...
start "AH Steel Lab App" cmd /k "cd /d %~dp0 && venv\Scripts\python.exe run.py"
timeout /t 4 /nobreak >nul

echo  Starting Cloudflare tunnel...
start "Cloudflare Tunnel" cmd /k ""%CF_EXE%" tunnel --config deploy\cloudflared\config.yml run"

echo.
echo  Wait 10 seconds, then open: https://app.ahsteellab.com/login
echo  Keep BOTH windows open.
echo.
pause
