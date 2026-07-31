@echo off
title LAN Database Sync - Main PC to Backup PC (no internet)
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Run INSTALL.bat first.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   LAN Database Sync
echo   Machine 1 MAIN  --^>  Machine 2 BACKUP
echo  ========================================
echo.
echo  Machine 1 MAIN:   shaheenhp  (192.168.92.103)  SQL Server 2008
echo  Machine 2 BACKUP: shaheenac  (192.168.92.215)  SQL Server 2008
echo  Folder: D:\DB_2626  (data\ subfolder for .mdf/.ldf)
echo.

venv\Scripts\python.exe -m scripts.run_lan_db_sync %*

pause
