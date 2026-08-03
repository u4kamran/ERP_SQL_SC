@echo off
title Install - Al Haram Steel Lab (ARP)
color 0B
echo.
echo  ============================================
echo   AL HARAM STEEL LAB - ARP INSTALL
echo   Database: nahsl2627 on shahenhp (same SQL Server)
echo   Port:     8001
echo   URL:      https://arp.ahsteellab.com
echo  ============================================
echo.

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed.
    echo  Download Python 3.13+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  [1/5] Creating Python environment...
if not exist "venv" python -m venv venv

echo  [2/5] Installing packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause
    exit /b 1
)

echo  [3/5] Creating .env for ARP site...
venv\Scripts\python.exe install\generate_env.py --site arp --force
echo.
echo  IMPORTANT: Edit .env and set DB_PASSWORD for SQL Server (shahenhp).
notepad .env

echo  [4/5] Create auth database NAHSL2627_AUTH...
echo.
set /p RUN_DB="Create NAHSL2627_AUTH database now? (Y/N): "
if /i "%RUN_DB%"=="Y" (
    venv\Scripts\python.exe scripts\setup_auth_database.py --site arp
)

echo  [5/5] Cloudflare setup (one time - browser will open)...
echo.
set /p RUN_CF="Run Cloudflare setup for arp.ahsteellab.com now? (Y/N): "
if /i "%RUN_CF%"=="Y" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\setup-site.ps1" -Site arp -SkipEnv
)

echo.
echo  ============================================
echo   ARP INSTALL DONE
echo  ============================================
echo.
echo  Next: SETUP-ARP-DATABASE.bat (if not done), then START-ARP.bat
echo  Then open: https://arp.ahsteellab.com/login
echo.
pause
