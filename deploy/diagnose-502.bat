@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0.."

echo.
echo ============================================================
echo  ERP site 502 diagnostic
echo  Target: https://erp.ahsteellab.com
echo ============================================================
echo.

set OK=1

echo [1] App health on this PC (must be OK)...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 5; Write-Host 'OK  ' $r.Content } catch { Write-Host 'FAIL - app not running on 127.0.0.1:8000'; exit 1 }"
if errorlevel 1 set OK=0

echo.
echo [2] cloudflared process on this PC...
tasklist /FI "IMAGENAME eq cloudflared.exe" 2>nul | find /I "cloudflared.exe" >nul
if errorlevel 1 (
    echo FAIL - cloudflared is NOT running. Start it:
    echo   deploy\cloudflared\bin\cloudflared.exe tunnel --config deploy\cloudflared\config.yml run
    set OK=0
) else (
    echo OK   cloudflared.exe is running
)

echo.
echo [3] config.yml on this PC...
if not exist "deploy\cloudflared\config.yml" (
    echo FAIL - deploy\cloudflared\config.yml missing
    set OK=0
) else (
    findstr /I "erp.ahsteellab.com" deploy\cloudflared\config.yml >nul || (
        echo FAIL - erp.ahsteellab.com not in config.yml
        set OK=0
    )
    findstr /I "127.0.0.1:8000" deploy\cloudflared\config.yml >nul || (
        echo FAIL - config must use 127.0.0.1:8000 not port 5000
        set OK=0
    )
    findstr /B "tunnel:" deploy\cloudflared\config.yml >nul || (
        echo FAIL - missing tunnel: line in config.yml
        set OK=0
    )
    if !OK! equ 1 echo OK   config.yml looks correct
    echo.
    type deploy\cloudflared\config.yml
)

echo.
echo [4] This PC IP (if tunnel runs elsewhere, erp must point here)...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do echo     %%a

echo.
if %OK% equ 1 (
    echo ============================================================
    echo  Local checks OK. If browser still shows 502:
    echo  - Only ONE PC should run this tunnel connector
    echo  - erp DNS must point to THIS tunnel in Cloudflare
    echo  - Stop tunnel on other PC if same tunnel ID
    echo ============================================================
) else (
    echo ============================================================
    echo  Fix FAIL items above, then restart:
    echo    python run.py
    echo    cloudflared tunnel --config deploy\cloudflared\config.yml run
    echo ============================================================
)
echo.
pause
