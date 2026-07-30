-- =============================================================================
-- AH Steel Lab - Authentication Database Creation Script
-- SQL Server 2008+ Compatible (auto-detects data file path)
-- =============================================================================
-- RECOMMENDATION: Separate authentication database (NSDS2626_AUTH)
--
-- This script creates a NEW database on the same SQL Server instance.
-- It does NOT modify nsds2626 (legacy VB6 business database).
-- =============================================================================

USE [master];
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'NSDS2626_AUTH')
BEGIN
    DECLARE @DataPath NVARCHAR(512);
    DECLARE @LogPath  NVARCHAR(512);
    DECLARE @Sql      NVARCHAR(MAX);

    -- Auto-detect default data/log paths from the server instance
    -- Works on SQL Server 2012+ via SERVERPROPERTY
    SET @DataPath = CONVERT(NVARCHAR(512), SERVERPROPERTY('InstanceDefaultDataPath'));
    SET @LogPath  = CONVERT(NVARCHAR(512), SERVERPROPERTY('InstanceDefaultLogPath'));

    -- Fallback for SQL Server 2008 (SERVERPROPERTY not available for paths)
    IF @DataPath IS NULL OR @DataPath = ''
    BEGIN
        SELECT @DataPath = SUBSTRING(
            physical_name, 1,
            CHARINDEX(N'master.mdf', LOWER(physical_name)) - 1
        )
        FROM sys.master_files
        WHERE database_id = 1 AND file_id = 1;
    END

    IF @LogPath IS NULL OR @LogPath = ''
        SET @LogPath = @DataPath;

    SET @Sql = N'
    CREATE DATABASE [NSDS2626_AUTH]
    ON PRIMARY
    (
        NAME = N''NSDS2626_AUTH'',
        FILENAME = N''' + @DataPath + N'NSDS2626_AUTH.mdf'',
        SIZE = 100MB,
        MAXSIZE = UNLIMITED,
        FILEGROWTH = 10MB
    )
    LOG ON
    (
        NAME = N''NSDS2626_AUTH_log'',
        FILENAME = N''' + @LogPath + N'NSDS2626_AUTH_log.ldf'',
        SIZE = 50MB,
        MAXSIZE = UNLIMITED,
        FILEGROWTH = 10MB
    );';

    PRINT 'Creating database using data path: ' + @DataPath;
    EXEC sp_executesql @Sql;
END
ELSE
BEGIN
    PRINT 'Database NSDS2626_AUTH already exists — skipping creation.';
END
GO

-- Set compatibility level and recovery model
IF EXISTS (SELECT name FROM sys.databases WHERE name = N'NSDS2626_AUTH')
BEGIN
    ALTER DATABASE [NSDS2626_AUTH] SET COMPATIBILITY_LEVEL = 100;
    ALTER DATABASE [NSDS2626_AUTH] SET RECOVERY SIMPLE;
END
GO

PRINT 'Database NSDS2626_AUTH is ready.';
GO
