@echo off
title Setup - Al Haram Steel Lab (ARP)
cd /d "%~dp0"
echo.
echo  One-time setup for arp.ahsteellab.com
echo  Database: nahsl2627 on shahenhp (same SQL Server as ERP)
echo  Port: 8001
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\setup-site.ps1" -Site arp
pause
