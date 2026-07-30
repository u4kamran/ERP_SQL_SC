@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0.."

title AH Steel Lab - Test SQL connection to shahenhp

echo.
echo ============================================================
echo  Test connection from THIS PC to database machine
echo ============================================================
echo.

set "USER=sa"
set "PASS=redgreen"
set "BIZ=nsds2626"
set "AUTH=NSDS2626_AUTH"
set "SERVER=shaheenhp"

echo [1] Ping shaheenhp ...
ping -n 2 shaheenhp
if errorlevel 1 (
    echo.
    echo WARN: Cannot ping shaheenhp by name.
    echo You can still connect using IP address.
    echo.
    set /p DBIP="Enter database machine IP if you know it: "
    if not "!DBIP!"=="" set "SERVER=!DBIP!"
)

echo.
echo [2] Will try these server names:
echo     !SERVER!
echo     !SERVER!\SQLEXPRESS
echo     shahenhp
echo     shahenhp\SQLEXPRESS
echo.

if not exist "venv\Scripts\python.exe" (
    echo Creating venv for test...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install pyodbc -q
) else (
    call venv\Scripts\activate.bat
)

python "%~dp0test_db_connection.py" "!SERVER!" "%USER%" "%PASS%" "%BIZ%" "%AUTH%"

echo.
echo ============================================================
echo  If all tests FAIL, fix ON THE DATABASE PC (shahenhp):
echo   1. SQL Server Configuration Manager - enable TCP/IP
echo   2. Restart SQL Server service
echo   3. Windows Firewall - allow SQL Server port 1433
echo   4. Allow remote connections + sa login enabled
echo.
echo  Then put working value in .env:
echo   DB_SERVER=shahenhp
echo   or DB_SERVER=192.168.x.x
echo   or DB_SERVER=shaheenhp\SQLEXPRESS
echo ============================================================
echo.
pause
