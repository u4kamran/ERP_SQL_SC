@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

title AH Steel Lab - Install

echo.
echo ============================================================
echo  AH Steel Lab - App machine install
echo  Database server (remote): shaheenhp
echo  Business DB: nsds2626
echo  Auth DB: NSDS2626_AUTH
echo.
echo  NOTE: Database is on a DIFFERENT PC (shahenhp).
echo  Create auth DB on shahenhp first - see install\SETUP-SHAHENHP.txt
echo ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not on PATH.
    echo Install Python 3.13+ from https://www.python.org/downloads/
    echo Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "delims=" %%V in ('python -c "import sys; print('%s.%s' %% (sys.version_info.major, sys.version_info.minor))"') do set PYVER=%%V
echo Python version: %PYVER%

python "%~dp0generate_env.py"
if errorlevel 1 (
    echo Python env setup failed, trying PowerShell...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0generate-env.ps1"
    if errorlevel 1 (
        echo Failed to create .env
        pause
        exit /b 1
    )
)

if not exist "venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create venv.
        pause
        exit /b 1
    )
)

echo.
echo Installing Python packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo pip install failed.
    pause
    exit /b 1
)

echo.
echo Testing ODBC connection to business database nsds2626 ...
venv\Scripts\python.exe -c "import pyodbc; c=pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=\\shaheenhp;DATABASE=nsds2626;UID=sa;PWD=redgreen;TrustServerCertificate=yes;Encrypt=no'); print('Business DB connection: OK'); c.close()"
if errorlevel 1 (
    echo.
    echo WARNING: Could not connect to nsds2626 on shahenhp.
    echo - Install "ODBC Driver 18 for SQL Server"
    echo - Check server name, sa password, firewall, SQL remote access
    echo.
)

echo.
echo Testing ODBC connection to auth database NSDS2626_AUTH ...
venv\Scripts\python.exe -c "import pyodbc; c=pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=\\shaheenhp;DATABASE=NSDS2626_AUTH;UID=sa;PWD=redgreen;TrustServerCertificate=yes;Encrypt=no'); print('Auth DB connection: OK'); c.close()"
if errorlevel 1 (
    echo.
    echo Auth database not ready on shahenhp (remote database machine).
    echo.
    echo On the DATABASE machine (shahenhp), run sql\01..05 in SSMS first.
    echo See install\SETUP-SHAHENHP.txt Part A.
    echo.
    echo Or from this app PC (if network + sqlcmd works):
    echo   install\setup-database.bat
    echo.
    pause
    exit /b 1
)

echo.
echo Seeding admin user and inventory permissions...
venv\Scripts\python.exe -m scripts.seed_database
if errorlevel 1 (
    echo seed_database failed.
    pause
    exit /b 1
)

venv\Scripts\python.exe -m scripts.seed_inventory_permissions
if errorlevel 1 (
    echo seed_inventory_permissions failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  INSTALL COMPLETE
echo.
echo  Start app:  install\start.bat
echo  Or:         python run.py
echo.
echo  Login:      http://localhost:8000/login
echo  Username:   admin
echo  Password:   ChangeMe@2026!
echo ============================================================
echo.
pause
