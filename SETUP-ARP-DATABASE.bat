@echo off
title Create NAHSL2627_AUTH database
cd /d "%~dp0"

echo.
echo  ============================================================
echo   CREATE AUTH DATABASE FOR AL HARAM STEEL LAB
echo   Server:   shaheenhp (SQL Server 2008)
echo   Auth DB:  NAHSL2627_AUTH
echo   Business: NAHSL2627
echo  ============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo  ERROR: Run INSTALL-ARP.bat or INSTALL-ERP.bat first.
    pause
    exit /b 1
)

if not exist ".env" (
    echo  ERROR: .env not found.
    echo  Run: venv\Scripts\python.exe install\generate_env.py --site arp --force
    pause
    exit /b 1
)

echo  Creating NAHSL2627_AUTH ...
echo.

venv\Scripts\python.exe scripts\setup_auth_database.py --site arp
if errorlevel 1 (
    echo.
    echo  FAILED. Check DB_PASSWORD in .env and that SQL Server is running.
    pause
    exit /b 1
)

echo.
echo  Done. You can now run START-ARP.bat
echo.
pause
