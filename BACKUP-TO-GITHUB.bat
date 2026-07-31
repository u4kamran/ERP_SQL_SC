@echo off
setlocal EnableExtensions
title AH Steel Lab - Backup to GitHub
color 0B
cd /d "%~dp0"

echo.
echo  ============================================
echo   BACKUP TO GITHUB
echo   https://github.com/u4kamran/ERP_SQL_SC
echo  ============================================
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Git is not installed.
    echo  Download from: https://git-scm.com/download/win
    echo  Install it, restart this window, then run again.
    pause
    exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo  ERROR: This folder is not a Git repository.
    pause
    exit /b 1
)

echo  Changed files:
echo  --------------
git status --short
echo.

git diff --quiet
if errorlevel 1 goto :has_changes
git diff --cached --quiet
if errorlevel 1 goto :has_changes

echo  Nothing to backup - no changes since last commit.
echo.
git log -1 --oneline
echo.
pause
exit /b 0

:has_changes
echo  Enter a short message describing what you changed.
echo  Example: Fixed login page / Added new report
echo.
set "MSG="
set /p MSG="Commit message: "

if "%MSG%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set D=%%c-%%a-%%b
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set T=%%a:%%b
    set "MSG=Backup %D% %T%"
    echo.
    echo  Using default message: %MSG%
)

echo.
echo  [1/3] Staging files...
git add -A
if errorlevel 1 (
    echo  ERROR: git add failed.
    pause
    exit /b 1
)

echo  [2/3] Saving snapshot (commit)...
git commit -m "%MSG%"
if errorlevel 1 (
    echo  ERROR: Commit failed. Nothing was uploaded.
    pause
    exit /b 1
)

echo  [3/3] Uploading to GitHub...
git push erpsqlsc main
if errorlevel 1 (
    echo.
    echo  ERROR: Push failed.
    echo.
    echo  Common fixes:
    echo    - Check internet connection
    echo    - Log in to GitHub when Git asks
    echo    - Use a Personal Access Token as password
    echo      GitHub - Settings - Developer settings - Tokens
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   BACKUP COMPLETE
echo  ============================================
echo.
echo  Your code is saved on GitHub:
echo  https://github.com/u4kamran/ERP_SQL_SC
echo.
git log -1 --oneline
echo.
pause
exit /b 0
