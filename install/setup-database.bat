@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo.
echo ============================================================
echo  DATABASE SETUP (run on shahenhp or remotely via network)
echo  Target server: shahenhp
echo  Auth DB: NSDS2626_AUTH
echo.
echo  If SQL Server is on another PC, this batch connects over
echo  the network. You can also run sql\*.sql in SSMS on shahenhp.
echo ============================================================
echo.

where sqlcmd >nul 2>&1
if errorlevel 1 (
    echo sqlcmd not found.
    echo.
    echo Install SQL Server Command Line Tools, OR run these files in SSMS on shahenhp:
    echo   sql\01_create_database.sql
    echo   sql\02_create_schema.sql
    echo   sql\03_create_tables.sql
    echo   sql\04_create_indexes.sql
    echo   sql\05_seed_data.sql
    echo.
    pause
    exit /b 1
)

set "SQLSERVER=shahenhp"
set "SQLUSER=sa"
set "SQLPASS=redgreen"

echo Running SQL scripts on %SQLSERVER% ...
echo.

for %%F in (
    "sql\01_create_database.sql"
    "sql\02_create_schema.sql"
    "sql\03_create_tables.sql"
    "sql\04_create_indexes.sql"
    "sql\05_seed_data.sql"
) do (
    echo --- %%~F ---
    sqlcmd -S %SQLSERVER% -U %SQLUSER% -P %SQLPASS% -b -i %%F
    if errorlevel 1 (
        echo.
        echo FAILED: %%~F
        pause
        exit /b 1
    )
    echo.
)

echo Auth database setup completed.
pause
