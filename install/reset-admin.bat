@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

title Reset admin login

echo.
echo Reset admin user password in NSDS2626_AUTH
echo Default login after this:
echo   Username: admin
echo   Password: ChangeMe@2026!
echo.

if not exist "venv\Scripts\python.exe" (
    echo venv not found. Run install\install.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python -m scripts.seed_database
if errorlevel 1 (
    echo seed_database failed - check DB connection in .env
    pause
    exit /b 1
)

python -m scripts.seed_inventory_permissions

echo.
echo Done. Try login again at http://localhost:8000/login
pause
