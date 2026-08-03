@echo off
title Start - Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Starting Shafique Center ERP...
echo  Public URL: https://erp.ahsteellab.com
echo.
echo  Keep this window OPEN. To stop: STOP-APP.bat
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\start-site.ps1" -Site erp
pause
