-- =============================================================================
-- AH Steel Lab - Authentication Schema Creation
-- Database: NSDS2626_AUTH
-- Schema: auth
-- SQL Server 2008 Compatible
-- =============================================================================

USE [NSDS2626_AUTH];
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'auth')
BEGIN
    EXEC('CREATE SCHEMA [auth] AUTHORIZATION [dbo]');
END
GO

PRINT 'Schema [auth] created successfully.';
GO
