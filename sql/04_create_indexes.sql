-- =============================================================================
-- AH Steel Lab - Authentication Indexes
-- Database: NSDS2626_AUTH | Schema: auth
-- =============================================================================

USE [NSDS2626_AUTH];
GO

SET QUOTED_IDENTIFIER ON;
GO

-- Users
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_IsActive' AND object_id = OBJECT_ID('auth.Users'))
    CREATE NONCLUSTERED INDEX [IX_Users_IsActive] ON [auth].[Users]([IsActive], [IsDeleted]) INCLUDE ([Username], [Email]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_LockoutEndDate' AND object_id = OBJECT_ID('auth.Users'))
    CREATE NONCLUSTERED INDEX [IX_Users_LockoutEndDate] ON [auth].[Users]([LockoutEndDate]) WHERE [LockoutEndDate] IS NOT NULL;
GO

-- UserSessions
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_UserSessions_UserId' AND object_id = OBJECT_ID('auth.UserSessions'))
    CREATE NONCLUSTERED INDEX [IX_UserSessions_UserId] ON [auth].[UserSessions]([UserId], [IsRevoked], [ExpiresAt]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_UserSessions_RefreshTokenHash' AND object_id = OBJECT_ID('auth.UserSessions'))
    CREATE NONCLUSTERED INDEX [IX_UserSessions_RefreshTokenHash] ON [auth].[UserSessions]([RefreshTokenHash]);
GO

-- RefreshTokens
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RefreshTokens_TokenHash' AND object_id = OBJECT_ID('auth.RefreshTokens'))
    CREATE NONCLUSTERED INDEX [IX_RefreshTokens_TokenHash] ON [auth].[RefreshTokens]([TokenHash], [IsRevoked]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RefreshTokens_UserId' AND object_id = OBJECT_ID('auth.RefreshTokens'))
    CREATE NONCLUSTERED INDEX [IX_RefreshTokens_UserId] ON [auth].[RefreshTokens]([UserId], [ExpiresAt]);
GO

-- RevokedTokens
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RevokedTokens_Jti' AND object_id = OBJECT_ID('auth.RevokedTokens'))
    CREATE NONCLUSTERED INDEX [IX_RevokedTokens_Jti] ON [auth].[RevokedTokens]([Jti], [ExpiresAt]);
GO

-- LoginHistory
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LoginHistory_UserId' AND object_id = OBJECT_ID('auth.LoginHistory'))
    CREATE NONCLUSTERED INDEX [IX_LoginHistory_UserId] ON [auth].[LoginHistory]([UserId], [CreatedDate] DESC);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LoginHistory_Username' AND object_id = OBJECT_ID('auth.LoginHistory'))
    CREATE NONCLUSTERED INDEX [IX_LoginHistory_Username] ON [auth].[LoginHistory]([Username], [CreatedDate] DESC);
GO

-- AuditLogs
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AuditLogs_UserId' AND object_id = OBJECT_ID('auth.AuditLogs'))
    CREATE NONCLUSTERED INDEX [IX_AuditLogs_UserId] ON [auth].[AuditLogs]([UserId], [CreatedDate] DESC);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AuditLogs_Action' AND object_id = OBJECT_ID('auth.AuditLogs'))
    CREATE NONCLUSTERED INDEX [IX_AuditLogs_Action] ON [auth].[AuditLogs]([Action], [CreatedDate] DESC);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AuditLogs_Entity' AND object_id = OBJECT_ID('auth.AuditLogs'))
    CREATE NONCLUSTERED INDEX [IX_AuditLogs_Entity] ON [auth].[AuditLogs]([EntityType], [EntityId]);
GO

-- PasswordHistory
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PasswordHistory_UserId' AND object_id = OBJECT_ID('auth.PasswordHistory'))
    CREATE NONCLUSTERED INDEX [IX_PasswordHistory_UserId] ON [auth].[PasswordHistory]([UserId], [CreatedDate] DESC);
GO

-- PasswordResetTokens
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PasswordResetTokens_TokenHash' AND object_id = OBJECT_ID('auth.PasswordResetTokens'))
    CREATE NONCLUSTERED INDEX [IX_PasswordResetTokens_TokenHash] ON [auth].[PasswordResetTokens]([TokenHash], [IsUsed]);
GO

-- RolePermissions / UserRoles
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_RolePermissions_RoleId' AND object_id = OBJECT_ID('auth.RolePermissions'))
    CREATE NONCLUSTERED INDEX [IX_RolePermissions_RoleId] ON [auth].[RolePermissions]([RoleId]) INCLUDE ([PermissionId]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_UserRoles_UserId' AND object_id = OBJECT_ID('auth.UserRoles'))
    CREATE NONCLUSTERED INDEX [IX_UserRoles_UserId] ON [auth].[UserRoles]([UserId]) INCLUDE ([RoleId]);
GO

-- Permissions
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Permissions_ModuleId' AND object_id = OBJECT_ID('auth.Permissions'))
    CREATE NONCLUSTERED INDEX [IX_Permissions_ModuleId] ON [auth].[Permissions]([ModuleId]);
GO

PRINT 'All indexes created successfully.';
GO
