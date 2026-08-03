@echo off
title Stop All - Shafique Center + Al Haram Steel Lab
cd /d "%~dp0"

set "ERP_ROOT=%~dp0"
set "ARP_ROOT=D:\CursorProject\ahsteellab-arp"

echo.
echo  Stopping both sites...
echo.

echo [1] Stopping apps on ports 8000 and 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001" ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo [2] Stopping ERP watchdog...
for /f "skip=1 tokens=2" %%a in ('wmic process where "CommandLine like '%%app_watchdog.py%%' and CommandLine like '%%ahsteellab-nsds2626%%'" get ProcessId 2^>nul') do (
    if not "%%a"=="" taskkill /PID %%a /F >nul 2>&1
)

echo [3] Stopping ARP watchdog...
for /f "skip=1 tokens=2" %%a in ('wmic process where "CommandLine like '%%app_watchdog.py%%' and CommandLine like '%%ahsteellab-arp%%'" get ProcessId 2^>nul') do (
    if not "%%a"=="" taskkill /PID %%a /F >nul 2>&1
)

echo [4] Stopping Cloudflare tunnels...
for /f "skip=1 tokens=2" %%a in ('wmic process where "Name='cloudflared.exe'" get ProcessId,CommandLine 2^>nul') do (
    echo %%a | findstr /I "ahsteellab-nsds2626 ahsteellab-arp" >nul && taskkill /PID %%a /F >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo.
echo  Both sites stopped.
echo  To start again: START-ALL.bat
echo.
pause
