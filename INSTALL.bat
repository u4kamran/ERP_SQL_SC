@echo off
title AH Steel Lab - Install
color 0A
echo.
echo  ============================================
echo   AH STEEL LAB - AUTO INSTALL
echo  ============================================
echo.

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed.
    echo  Download Python 3.13+ from https://www.python.org/downloads/
    echo  Check "Add Python to PATH" during install, then run this again.
    pause
    exit /b 1
)

echo  [1/5] Creating Python environment...
if not exist "venv" (
    python -m venv venv
)

echo  [2/5] Installing packages (may take 2-3 minutes)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause
    exit /b 1
)

echo  [3/5] Creating .env file...
if not exist ".env" (
    copy /Y .env.production.example .env >nul
    echo  Created .env - you must edit it next.
) else (
    echo  .env already exists - keeping your settings.
)

echo  [4/5] Generating security keys...
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\generate-secrets.ps1" > secrets.txt
echo.
echo  Open secrets.txt and copy SECRET_KEY + CSRF_SECRET_KEY into .env
echo  Also set DB_PASSWORD in .env to your SQL Server password.
echo.
notepad secrets.txt
notepad .env

echo  [5/5] Cloudflare setup (one time - browser will open)...
echo.
set /p RUN_CF="Run Cloudflare setup now? (Y/N): "
if /i "%RUN_CF%"=="Y" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\setup-cloudflare.ps1"
)

echo.
echo  ============================================
echo   INSTALL DONE
echo  ============================================
echo.
echo  Next: Double-click START-WEBSITE.bat
echo  Then open: https://app.ahsteellab.com/login
echo.
pause
