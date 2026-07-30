@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not "%1"=="quiet" (
    title Stop ERP App
    echo.
    echo  Stopping Shafique Departmental Store ERP...
    echo.
)

echo [1] Stopping watchdog...
for /f "skip=1 tokens=2" %%a in ('wmic process where "CommandLine like '%%app_watchdog.py%%'" get ProcessId 2^>nul') do (
    if not "%%a"=="" (
        if not "%1"=="quiet" echo       Stopping watchdog PID %%a
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo [2] Stopping app on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do (
    if not "%1"=="quiet" echo       Stopping PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo [3] Stopping run.py processes...
for /f "skip=1 tokens=2" %%a in ('wmic process where "CommandLine like '%%run.py%%' and CommandLine like '%%ahsteellab-nsds2626%%'" get ProcessId 2^>nul') do (
    if not "%%a"=="" taskkill /PID %%a /F >nul 2>&1
)

echo [4] Stopping Cloudflare tunnel...
taskkill /F /IM cloudflared.exe >nul 2>&1

timeout /t 2 /nobreak >nul

if not "%1"=="quiet" (
    netstat -ano | findstr ":8000" | findstr LISTENING >nul
    if !errorlevel!==0 (
        echo.
        echo  WARNING: Port 8000 may still be in use.
    ) else (
        echo.
        echo  ERP stopped.
    )
    echo.
    pause
)
