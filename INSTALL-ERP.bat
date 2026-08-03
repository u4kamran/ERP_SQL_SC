@echo off
title Install - Shafique Center (ERP)
color 0A
echo.
echo  ============================================
echo   SHAFIQUE CENTER - ERP INSTALL
echo   Database: nsds2626
echo   URL:      https://erp.ahsteellab.com
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

echo  [1/4] Creating Python environment...
if not exist "venv" python -m venv venv

echo  [2/4] Installing packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause
    exit /b 1
)

echo  [3/4] Creating .env for ERP site...
venv\Scripts\python.exe install\generate_env.py --site erp --force
echo.
echo  IMPORTANT: Edit .env and set DB_PASSWORD for SQL Server (shahenhp).
notepad .env

echo  [4/4] Cloudflare setup (one time - browser will open)...
echo.
set /p RUN_CF="Run Cloudflare setup for erp.ahsteellab.com now? (Y/N): "
if /i "%RUN_CF%"=="Y" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\setup-site.ps1" -Site erp -SkipEnv
)

echo.
echo  ============================================
echo   ERP INSTALL DONE
echo  ============================================
echo.
echo  Next: Double-click START-ERP.bat
echo  Then open: https://erp.ahsteellab.com/login
echo.
pause
