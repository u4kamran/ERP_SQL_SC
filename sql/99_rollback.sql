-- =============================================================================
-- AH Steel Lab - Rollback Script
-- WARNING: This will DROP the entire authentication database.
-- Does NOT affect nsds2626 (legacy business database).
-- =============================================================================

USE [master];
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'NSDS2626_AUTH')
BEGIN
    ALTER DATABASE [NSDS2626_AUTH] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [NSDS2626_AUTH];
    PRINT 'Database NSDS2626_AUTH dropped successfully.';
END
ELSE
BEGIN
    PRINT 'Database NSDS2626_AUTH does not exist.';
END
GO
