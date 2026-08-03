@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo.
echo ============================================================
echo  ARP DATABASE SETUP
echo  Server:   shaheenhp
echo  Auth DB:  NAHSL2627_AUTH
echo  Business: NAHSL2627
echo ============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo venv not found. Run INSTALL-ARP.bat first.
    pause
    exit /b 1
)

venv\Scripts\python.exe scripts\setup_auth_database.py --site arp
pause
