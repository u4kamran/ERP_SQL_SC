@echo off
title Setup backup folder share on MACHINE 2 (shaheenac)
REM Run this ON shaheenac (192.168.92.215) as Administrator

set FOLDER=D:\DB_2626
set DATA=%FOLDER%\data
set SHARE=DB_2626

echo.
echo  Creating folder and share on BACKUP PC (shaheenac)
echo  SQL Server 2008 — backup + restore folder
echo  Folder: %FOLDER%
echo  Data:   %DATA%  (.mdf / .ldf after restore)
echo  Share:  \\shaheenac\%SHARE%
echo.

if not exist "%FOLDER%" mkdir "%FOLDER%"
if not exist "%DATA%" mkdir "%DATA%"

net share %SHARE%=%FOLDER% /GRANT:Everyone,FULL

echo.
echo  Share created. From MAIN PC (shaheenhp) test:
echo    dir \\shaheenac\%SHARE%
echo.