@echo off
title Setup - Shafique Center (ERP)
cd /d "%~dp0"
echo.
echo  One-time setup for erp.ahsteellab.com
echo  Database: nsds2626 on shahenhp
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\setup-site.ps1" -Site erp
pause
