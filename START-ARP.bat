@echo off
title Start - Al Haram Steel Lab (ARP)
cd /d "%~dp0"
echo.
echo  Starting Al Haram Steel Lab...
echo  Public URL: https://arp.ahsteellab.com
echo.
echo  Keep this window OPEN. To stop: STOP-APP.bat
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\start-site.ps1" -Site arp
pause
