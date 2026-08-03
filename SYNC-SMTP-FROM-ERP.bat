@echo off
title Sync SMTP from Shafique Center (ERP) to ARP
cd /d "%~dp0"
echo.
echo  Copy working SMTP from Shafique Center .env to shared-smtp.env
echo  (same Gmail for ERP + ARP)
echo.
venv\Scripts\python.exe scripts\sync_smtp_from_erp.py
echo.
pause
