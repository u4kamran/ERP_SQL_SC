@echo off
REM Instant rollback for Customer Ledger (Detailed) — existing GL Ledger is untouched.
REM Sets GL_LEDGER_DETAILED_ENABLED=false in this project's .env if present.
setlocal
cd /d "%~dp0"
if not exist ".env" (
  echo .env not found. Add: GL_LEDGER_DETAILED_ENABLED=false
  exit /b 1
)
findstr /B /C:"GL_LEDGER_DETAILED_ENABLED=" ".env" >nul 2>&1
if errorlevel 1 (
  echo GL_LEDGER_DETAILED_ENABLED=false>> ".env"
  echo Added GL_LEDGER_DETAILED_ENABLED=false to .env
) else (
  powershell -NoProfile -Command "(Get-Content .env) -replace '^GL_LEDGER_DETAILED_ENABLED=.*','GL_LEDGER_DETAILED_ENABLED=false' | Set-Content .env"
  echo Updated GL_LEDGER_DETAILED_ENABLED=false in .env
)
echo Restart the app for rollback to take effect. Existing GL Ledger Report still works.
endlocal
