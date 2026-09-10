@echo off
title Uninstall always-on Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Removes ERP scheduled tasks only. ARP is not touched.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\erp-always-on.ps1" -Action uninstall
echo.
pause
