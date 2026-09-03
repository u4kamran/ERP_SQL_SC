@echo off
REM Seed report Email/WhatsApp delivery permissions (Option A).
REM Usage:
REM   SEED-REPORT-DELIVERY-PERMISSIONS.bat
REM   SEED-REPORT-DELIVERY-PERMISSIONS.bat --site erp
REM   SEED-REPORT-DELIVERY-PERMISSIONS.bat --all

cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Missing venv\Scripts\python.exe
  pause
  exit /b 1
)
venv\Scripts\python.exe scripts\seed_report_delivery_permissions.py %*
if errorlevel 1 (
  echo Seed failed.
  pause
  exit /b 1
)
echo Done. Users must re-login to refresh JWT permissions.
pause
