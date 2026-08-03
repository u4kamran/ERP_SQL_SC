@echo off
title Start All - Shafique Center + Al Haram Steel Lab
cd /d "%~dp0"

set "ERP_ROOT=%~dp0"
set "ARP_ROOT=D:\CursorProject\ahsteellab-arp"

echo.
echo  ============================================
echo   AH Steel Lab - START ALL PROJECTS
echo  ============================================
echo    ERP  https://erp.ahsteellab.com  port 8000
echo    ARP  https://arp.ahsteellab.com  port 8001
echo  ============================================
echo.

if not exist "%ARP_ROOT%\deploy\start-site.ps1" (
    echo ERROR: ARP folder not found: %ARP_ROOT%
    echo Run CLONE-ARP-SITE.bat first.
    pause
    exit /b 1
)

echo [1/5] Sync application code to ARP ^(same reports as ERP^)...
"%ERP_ROOT%venv\Scripts\python.exe" "%ERP_ROOT%scripts\sync_code_to_arp.py"
if errorlevel 1 (
    echo.
    echo  ERROR: Code sync to ARP failed.
    pause
    exit /b 1
)

echo [2/5] Sync shared SMTP ^(same Gmail for both sites^)...
"%ERP_ROOT%venv\Scripts\python.exe" "%ERP_ROOT%scripts\sync_smtp_from_erp.py"
if errorlevel 1 (
    echo.
    echo  WARNING: SMTP sync skipped - set SMTP_PASSWORD in ERP .env
    echo.
)

echo [3/5] Stopping old app/tunnel processes...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ERP_ROOT%deploy\stop-listeners.ps1"

echo [4/5] Starting Shafique Center ^(ERP^)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ERP_ROOT%deploy\start-site.ps1" -Site erp

echo [5/5] Starting Al Haram Steel Lab ^(ARP^)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ARP_ROOT%\deploy\start-site.ps1" -Site arp

echo.
echo  Waiting for apps to start...
ping 127.0.0.1 -n 13 >nul

echo.
echo  Health check:
powershell -NoProfile -ExecutionPolicy Bypass -File "%ERP_ROOT%deploy\health-check-both.ps1"

echo.
echo  Both sites started. Keep this PC on.
echo  To stop: STOP-ALL.bat
echo.
pause
