@echo off
title Check - Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Checking erp.ahsteellab.com ...
echo.

set OK=1

echo [1] App on port 8000...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 5; Write-Host '     OK -' $r.Content } catch { Write-Host '     FAIL - app not running. Run START-ERP.bat'; exit 1 }"
if errorlevel 1 set OK=0

echo.
echo [2] Cloudflare tunnel...
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find /I "cloudflared.exe" >nul
if errorlevel 1 (
    echo      FAIL - tunnel NOT running. Run START-ERP.bat
    set OK=0
) else (
    echo      OK - cloudflared.exe is running
)

echo.
echo [3] Public URL https://erp.ahsteellab.com ...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri https://erp.ahsteellab.com/health -UseBasicParsing -TimeoutSec 15; Write-Host '     OK -' $r.Content } catch { Write-Host '     FAIL - public site not reachable'; exit 1 }"
if errorlevel 1 set OK=0

echo.
if %OK% equ 1 (
    echo  All OK. Open: https://erp.ahsteellab.com/login
) else (
        echo  FIX: Double-click START-ERP-SERVICES.bat  (or START-ERP.bat)
)
echo.
pause
