@echo off
title Stop Shafique Center (ERP only)
cd /d "%~dp0"
echo.
echo  Stopping Shafique Center ERP (erp.ahsteellab.com)
echo  ARP site is NOT stopped.
echo.

schtasks /Query /TN "AHSteelLab-ERP-App" >nul 2>&1
if %errorlevel%==0 (
    echo  Always-on tasks found. Stopping those first...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\erp-always-on.ps1" -Action stop
    echo.
    echo  Shafique Center (ERP) stopped.
    echo  Al Haram (ARP) still runs from: D:\CursorProject\ahsteellab-arp
    echo.
    pause
    exit /b 0
)

echo [1] Stopping app on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo [2] Stopping ERP watchdog...
for /f "skip=1 tokens=2" %%a in ('wmic process where "CommandLine like '%%app_watchdog.py%%' and CommandLine like '%%ahsteellab-nsds2626%%'" get ProcessId 2^>nul') do (
    if not "%%a"=="" taskkill /PID %%a /F >nul 2>&1
)

echo [3] Stopping ERP Cloudflare tunnel...
set "ERP_CFG=%~dp0deploy\cloudflared\config.yml"
for /f "skip=1 tokens=2" %%a in ('wmic process where "Name='cloudflared.exe'" get ProcessId,CommandLine 2^>nul') do (
    echo %%a | findstr /I "ahsteellab-nsds2626" >nul && taskkill /PID %%a /F >nul 2>&1
)

echo.
echo  Shafique Center (ERP) stopped.
echo  Al Haram (ARP) still runs from: D:\CursorProject\ahsteellab-arp
echo.
pause
