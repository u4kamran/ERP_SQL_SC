@echo off
title Database Sync - Local to Online SQL Server
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL.bat first.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   SQL Server Sync (local -^> online)
echo  ========================================
echo.
echo  This copies a full backup to your online server.
echo  For ~10 GB, run once per night — not every minute.
echo.

venv\Scripts\python.exe -m scripts.run_db_sync %*

pause
