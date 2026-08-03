@echo off
title Check - Al Haram Steel Lab (ARP)
cd /d "%~dp0"
echo.
echo  Checking arp.ahsteellab.com ...
echo.

set OK=1

echo [1] App on port 8001...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri http://127.0.0.1:8001/health -UseBasicParsing -TimeoutSec 5; Write-Host '     OK -' $r.Content } catch { Write-Host '     FAIL - app not running. Run START-ARP.bat'; exit 1 }"
if errorlevel 1 set OK=0

echo.
echo [2] Cloudflare tunnel...
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find /I "cloudflared.exe" >nul
if errorlevel 1 (
    echo      FAIL - tunnel NOT running. Run START-ARP.bat
    set OK=0
) else (
    echo      OK - cloudflared.exe is running
)

echo.
echo [3] Public URL https://arp.ahsteellab.com ...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri https://arp.ahsteellab.com/health -UseBasicParsing -TimeoutSec 15; Write-Host '     OK -' $r.Content } catch { Write-Host '     FAIL - public site not reachable'; exit 1 }"
if errorlevel 1 set OK=0

echo.
if %OK% equ 1 (
    echo  All OK. Open: https://arp.ahsteellab.com/login
) else (
    echo  FIX: Double-click START-ARP.bat and keep window open.
)
echo.
pause
