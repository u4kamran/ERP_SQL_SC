@echo off
title Install nightly LAN sync task on MAIN PC
cd /d "%~dp0"

set TASK_NAME=ERP_LAN_Database_Sync
set SCRIPT=%~dp0SYNC-LAN-DATABASE.bat
set TIME=02:00

echo.
echo  Creating Windows scheduled task: %TASK_NAME%
echo  Runs daily at %TIME% — LAN sync to backup PC
echo.

schtasks /Create /F /TN "%TASK_NAME%" /TR "\"%SCRIPT%\"" /SC DAILY /ST %TIME% /RL HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo  SUCCESS — task installed.
    echo  Test now: SYNC-LAN-DATABASE.bat --status
    echo  Test sync: SYNC-LAN-DATABASE.bat --dry-run
) else (
    echo.
    echo  FAILED — run this batch file as Administrator.
)

pause
