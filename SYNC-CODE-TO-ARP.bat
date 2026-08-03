@echo off
title Sync application code to Al Haram (ARP)
cd /d "%~dp0"
echo.
echo  Copy reports and app code from Shafique Center (ERP) to Al Haram (ARP).
echo  Same reports on both sites. ARP .env and tunnel config are NOT changed.
echo.
venv\Scripts\python.exe scripts\sync_code_to_arp.py
echo.
pause
