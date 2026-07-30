@echo off
title Restart ERP Website
cd /d "%~dp0"

echo.
echo  Restarting ERP website (app + tunnel)...
call STOP-APP.bat quiet
timeout /t 2 /nobreak >nul
start "ERP Site" cmd /k "%~dp0START-SITE.bat"
