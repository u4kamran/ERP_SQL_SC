@echo off
title Start - Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Starting Shafique Center ERP...
echo  Public URL: https://erp.ahsteellab.com
echo.

schtasks /Query /TN "AHSteelLab-ERP-App" >nul 2>&1
if %errorlevel%==0 (
    echo  Always-on tasks are installed. Starting those (no extra window).
    echo  Stop with STOP-ERP-SERVICES.bat
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\erp-always-on.ps1" -Action start
    pause
    exit /b 0
)

echo  Keep this window OPEN. To stop: STOP-ERP.bat
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\start-site.ps1" -Site erp
pause
