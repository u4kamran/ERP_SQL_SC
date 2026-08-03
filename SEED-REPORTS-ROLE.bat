@echo off
title Seed REPORTS_ONLY role
cd /d "%~dp0"
echo.
echo  Creating REPORTS_ONLY role on ERP and ARP auth databases...
echo.
venv\Scripts\python.exe scripts\seed_reports_role.py --all
echo.
pause
