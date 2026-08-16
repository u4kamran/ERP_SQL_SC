@echo off
title Install always-on Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Installs Windows tasks so erp.ahsteellab.com starts at logon.
echo  ARP / Al Haram is NOT changed.
echo  Do not use INSTALL-SERVICES.bat (that replaces the machine cloudflared service).
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\erp-always-on.ps1" -Action install
echo.
pause
