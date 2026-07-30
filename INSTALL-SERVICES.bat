@echo off
title AH Steel Lab - Install Services (Admin)
echo.
echo  This installs the website to start automatically on PC boot.
echo  You must Run as Administrator.
echo.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\install-services.ps1"
pause
