@echo off
title Start always-on Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  Starting ERP scheduled tasks (app + tunnel + health).
echo  ARP is not started or stopped.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\erp-always-on.ps1" -Action start
echo.
powershell -NoProfile -Command "Start-Sleep -Seconds 8; try { $r=Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 8; Write-Host 'Local health:' $r.Content } catch { Write-Host 'Local health FAIL' }"
echo.
pause
