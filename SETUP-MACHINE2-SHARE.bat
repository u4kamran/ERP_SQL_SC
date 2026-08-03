@echo off
title Setup backup folder share on MACHINE 2 (shaheenac)
REM Run this ON shaheenac (192.168.92.215)

:: ---------------------------------------------------------------------------
:: Must run as Administrator (net share needs admin - error 5 if not)
:: ---------------------------------------------------------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Access denied - this script must run as Administrator.
    echo.
    echo  Right-click SETUP-MACHINE2-SHARE.bat -^> Run as administrator
    echo.
    echo  Or open Command Prompt as Admin, then run this file again.
    echo.
    pause
    exit /b 5
)

set FOLDER=D:\DB_2626
set DATA=%FOLDER%\data
set SHARE=DB_2626
set SHARE_OK=0

echo.
echo  Creating folder and share on BACKUP PC (shaheenac)
echo  SQL Server 2008 - backup + restore folder
echo  Folder: %FOLDER%
echo  Data:   %DATA%  (.mdf / .ldf after restore)
echo  Share:  \\shaheenac\%SHARE%
echo.

if not exist "%FOLDER%" (
    mkdir "%FOLDER%"
    if errorlevel 1 (
        echo  ERROR: Could not create %FOLDER%
        goto :failed
    )
    echo  Created %FOLDER%
) else (
    echo  OK: %FOLDER% already exists
)

if not exist "%DATA%" (
    mkdir "%DATA%"
    if errorlevel 1 (
        echo  ERROR: Could not create %DATA%
        goto :failed
    )
    echo  Created %DATA%
) else (
    echo  OK: %DATA% already exists
)

echo.
echo  Creating network share...

:: Remove old share with same name (ignore errors if none exists)
net share %SHARE% /delete /y >nul 2>&1

net share %SHARE%=%FOLDER% /GRANT:Everyone,FULL
if %errorlevel% equ 0 (
    set SHARE_OK=1
    echo  OK: Share \\shaheenac\%SHARE% created
) else (
    echo.
    echo  net share failed (error %errorlevel%). Try manual share - see below.
)

:: Folder permissions for SQL Server and network copy
echo.
echo  Setting folder permissions (Everyone + Users modify)...
icacls "%FOLDER%" /grant Everyone:(OI)(CI)F /T >nul 2>&1
icacls "%FOLDER%" /grant Users:(OI)(CI)M /T >nul 2>&1
icacls "%FOLDER%" /grant "NETWORK SERVICE":(OI)(CI)M /T >nul 2>&1

echo.
if "%SHARE_OK%"=="1" (
    echo  SUCCESS. From MAIN PC (shaheenhp) test:
    echo    dir \\shaheenac\%SHARE%
    echo    echo test ^> \\shaheenac\%SHARE%\ping.txt
) else (
    :manual
    echo  MANUAL SHARE (if net share failed):
    echo    1. Open Windows Explorer -^> D:\DB_2626
    echo    2. Right-click DB_2626 -^> Properties -^> Sharing tab
    echo    3. Advanced Sharing -^> Share this folder
    echo    4. Share name: %SHARE%
    echo    5. Permissions -^> Everyone -^> Full Control (or Change + Read)
    echo    6. Security tab -^> add NETWORK SERVICE -^> Modify
    echo.
    echo  Then on shaheenhp run:  dir \\shaheenac\%SHARE%
)

echo.
echo  SQL Server 2008 service account also needs Modify on:
echo    %FOLDER%
echo    %DATA%
echo  Common accounts: NETWORK SERVICE  or  NT SERVICE\MSSQL$SQLEXPRESS
echo.
pause
exit /b 0

:failed
echo.
pause
exit /b 1
