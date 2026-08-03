@echo off
title Test SMTP Email
cd /d "%~dp0"
echo.
echo  Testing SMTP for ERP and ARP...
echo.
venv\Scripts\python.exe scripts\test_smtp.py --site erp
echo.
venv\Scripts\python.exe scripts\test_smtp.py --site arp
echo.
pause
