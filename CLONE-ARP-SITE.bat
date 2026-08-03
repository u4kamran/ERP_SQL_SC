@echo off
title Clone project for Al Haram Steel Lab (ARP)
color 0B
echo.
echo  This creates a second copy of the ERP for Al Haram Steel Lab.
echo  Target folder: D:\CursorProject\ahsteellab-arp
echo  URL: https://arp.ahsteellab.com
echo  Database: nahsl2627
echo.

set "TARGET=D:\CursorProject\ahsteellab-arp"

if exist "%TARGET%" (
    echo  Folder already exists: %TARGET%
    echo  Delete it first or choose a different path.
    pause
    exit /b 1
)

echo  Cloning from GitHub...
cd /d D:\CursorProject
git clone https://github.com/u4kamran/ERP_SQL_SC.git ahsteellab-arp
if errorlevel 1 (
    echo.
    echo  Git clone failed. Copy this folder manually instead:
    echo    xcopy /E /I "%~dp0" "%TARGET%"
    pause
    exit /b 1
)

echo.
echo  Clone complete.
echo.
echo  Next steps:
echo    1. cd %TARGET%
echo    2. Double-click INSTALL-ARP.bat
echo    3. Double-click SETUP-ARP.bat
echo    4. Double-click START-ARP.bat
echo.
pause
