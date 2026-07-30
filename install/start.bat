@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Run install\install.bat first.
    pause
    exit /b 1
)

if not exist ".env" (
    echo .env not found. Run install\install.bat first.
    pause
    exit /b 1
)

title AH Steel Lab
call venv\Scripts\activate.bat
python run.py
