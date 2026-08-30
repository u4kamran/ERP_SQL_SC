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

for /f "delims=" %%B in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%B"

echo  Current branch: %BRANCH%
echo.
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
echo  Tip: if you expected changes here, you may be on branch %BRANCH%
echo       while other work was committed on another branch.
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

echo  [2/3] Saving snapshot (commit) on branch %BRANCH%...
git commit -m "%MSG%"
if errorlevel 1 (
    echo  ERROR: Commit failed. Nothing was uploaded.
    pause
    exit /b 1
)

echo  [3/3] Uploading branch %BRANCH% to GitHub...
git push -u erpsqlsc HEAD
if errorlevel 1 (
    echo.
    echo  ERROR: Push failed.
    echo.
    if /I "%BRANCH%"=="main" (
        echo  GitHub often blocks direct pushes to main ^(branch protection^).
        echo  Work on a feature branch instead, then open a Pull Request:
        echo    git checkout -b feature/my-change
        echo    BACKUP-TO-GITHUB.bat
        echo.
    )
    echo  Other common fixes:
    echo    - Check internet connection
    echo    - Log in to GitHub when Git asks
    echo    - Use a Personal Access Token as password
    echo      GitHub - Settings - Developer settings - Tokens
    echo    - Remove secrets from files before commit
    echo      ^(.env, API keys in .env.example, etc.^)
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   BACKUP COMPLETE
echo  ============================================
echo.
echo  Branch %BRANCH% is saved on GitHub:
echo  https://github.com/u4kamran/ERP_SQL_SC
echo.
git log -1 --oneline
echo.
if /I not "%BRANCH%"=="main" (
    echo  Note: backup went to branch %BRANCH%, not main.
    echo  Open a Pull Request on GitHub when ready to merge.
    echo.
)
pause
exit /b 0
