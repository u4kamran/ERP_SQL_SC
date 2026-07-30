@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0.."

echo.
echo Set SQL Server name in .env (use value that showed OK in test-db-connection.bat)
echo Examples:
echo   shaheenhp\SQLEXPRESS
echo   192.168.1.50
echo   192.168.1.50\SQLEXPRESS
echo.
set /p NEWSERVER="Enter DB_SERVER value: "
if "!NEWSERVER!"=="" (
    echo Cancelled.
    pause
    exit /b 1
)

if not exist ".env" (
    echo .env not found. Run: python install\generate_env.py --force
    pause
    exit /b 1
)

powershell -NoProfile -Command ^
  "$p='.env'; $c=Get-Content $p -Raw; $c=$c -replace '(?m)^DB_SERVER=.*','DB_SERVER=!NEWSERVER!'; $c=$c -replace '(?m)^BUSINESS_DB_SERVER=.*','BUSINESS_DB_SERVER=!NEWSERVER!'; Set-Content $p $c -NoNewline"

echo.
echo Updated .env:
findstr /B "DB_SERVER BUSINESS_DB_SERVER" .env
echo.
echo Restart app: python run.py
pause
