@echo off
title Stop always-on Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Stopping ERP scheduled tasks. ARP stays running.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\erp-always-on.ps1" -Action stop
echo.
echo  ERP stopped. Website and phone will be down until START-ERP-SERVICES.bat
echo.
pause
