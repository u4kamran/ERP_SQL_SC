@echo off
title Configure SMTP (Same for ERP + ARP)
cd /d "%~dp0"
echo.
echo  One Gmail account for BOTH sites:
echo    ERP  erp.ahsteellab.com
echo    ARP  arp.ahsteellab.com
echo.
echo  Gmail App Password: https://myaccount.google.com/apppasswords
echo.
venv\Scripts\python.exe scripts\configure_smtp.py --interactive
