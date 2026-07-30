-- =============================================================================
-- AH Steel Lab - Authentication Tables
-- Database: NSDS2626_AUTH | Schema: auth
-- SQL Server 2008 Compatible
-- =============================================================================

USE [NSDS2626_AUTH];
GO

-- -----------------------------------------------------------------------------
-- Modules (ERP module registry for future expansion)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Modules]') AND type = 'U')
CREATE TABLE [auth].[Modules] (
    [ModuleId]          INT IDENTITY(1,1) NOT NULL,
    [ModuleCode]        NVARCHAR(50)  NOT NULL,
    [ModuleName]        NVARCHAR(100) NOT NULL,
    [Description]       NVARCHAR(500) NULL,
    [DisplayOrder]      INT           NOT NULL CONSTRAINT [DF_Modules_DisplayOrder] DEFAULT (0),
    [IconClass]         NVARCHAR(100) NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_Modules_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_Modules_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_Modules_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_Modules] PRIMARY KEY CLUSTERED ([ModuleId]),
    CONSTRAINT [UQ_Modules_ModuleCode] UNIQUE ([ModuleCode])
);
GO

-- -----------------------------------------------------------------------------
-- Features (sub-features within modules)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Features]') AND type = 'U')
CREATE TABLE [auth].[Features] (
    [FeatureId]         INT IDENTITY(1,1) NOT NULL,
    [ModuleId]          INT           NOT NULL,
    [FeatureCode]       NVARCHAR(50)  NOT NULL,
    [FeatureName]       NVARCHAR(100) NOT NULL,
    [Description]       NVARCHAR(500) NULL,
    [DisplayOrder]      INT           NOT NULL CONSTRAINT [DF_Features_DisplayOrder] DEFAULT (0),
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_Features_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_Features_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_Features_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_Features] PRIMARY KEY CLUSTERED ([FeatureId]),
    CONSTRAINT [FK_Features_Modules] FOREIGN KEY ([ModuleId]) REFERENCES [auth].[Modules]([ModuleId]),
    CONSTRAINT [UQ_Features_ModuleCode] UNIQUE ([ModuleId], [FeatureCode])
);
GO

-- -----------------------------------------------------------------------------
-- Permissions
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Permissions]') AND type = 'U')
CREATE TABLE [auth].[Permissions] (
    [PermissionId]      INT IDENTITY(1,1) NOT NULL,
    [ModuleId]          INT           NULL,
    [FeatureId]         INT           NULL,
    [PermissionCode]    NVARCHAR(100) NOT NULL,
    [PermissionName]    NVARCHAR(150) NOT NULL,
    [Description]       NVARCHAR(500) NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_Permissions_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_Permissions_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_Permissions_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_Permissions] PRIMARY KEY CLUSTERED ([PermissionId]),
    CONSTRAINT [FK_Permissions_Modules] FOREIGN KEY ([ModuleId]) REFERENCES [auth].[Modules]([ModuleId]),
    CONSTRAINT [FK_Permissions_Features] FOREIGN KEY ([FeatureId]) REFERENCES [auth].[Features]([FeatureId]),
    CONSTRAINT [UQ_Permissions_Code] UNIQUE ([PermissionCode])
);
GO

-- -----------------------------------------------------------------------------
-- Roles
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Roles]') AND type = 'U')
CREATE TABLE [auth].[Roles] (
    [RoleId]            INT IDENTITY(1,1) NOT NULL,
    [RoleCode]          NVARCHAR(50)  NOT NULL,
    [RoleName]          NVARCHAR(100) NOT NULL,
    [Description]       NVARCHAR(500) NULL,
    [IsSystemRole]      BIT           NOT NULL CONSTRAINT [DF_Roles_IsSystemRole] DEFAULT (0),
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_Roles_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_Roles_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_Roles_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_Roles] PRIMARY KEY CLUSTERED ([RoleId]),
    CONSTRAINT [UQ_Roles_RoleCode] UNIQUE ([RoleCode])
);
GO

-- -----------------------------------------------------------------------------
-- Users
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Users]') AND type = 'U')
CREATE TABLE [auth].[Users] (
    [UserId]                INT IDENTITY(1,1) NOT NULL,
    [Username]              NVARCHAR(100) NOT NULL,
    [Email]                 NVARCHAR(255) NOT NULL,
    [PasswordHash]          NVARCHAR(255) NOT NULL,
    [FirstName]             NVARCHAR(100) NULL,
    [LastName]              NVARCHAR(100) NULL,
    [PhoneNumber]           NVARCHAR(30)  NULL,
    [ProfileImageUrl]       NVARCHAR(500) NULL,
    [MustChangePassword]    BIT           NOT NULL CONSTRAINT [DF_Users_MustChangePassword] DEFAULT (0),
    [PasswordChangedDate]   DATETIME      NULL,
    [PasswordExpiryDate]    DATETIME      NULL,
    [FailedLoginAttempts]   INT           NOT NULL CONSTRAINT [DF_Users_FailedLoginAttempts] DEFAULT (0),
    [LockoutEndDate]        DATETIME      NULL,
    [LastLoginDate]         DATETIME      NULL,
    [LastLoginIp]           NVARCHAR(45)  NULL,
    [IsEmailVerified]       BIT           NOT NULL CONSTRAINT [DF_Users_IsEmailVerified] DEFAULT (0),
    [CreatedDate]           DATETIME      NOT NULL CONSTRAINT [DF_Users_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]             INT           NULL,
    [ModifiedDate]          DATETIME      NULL,
    [ModifiedBy]            INT           NULL,
    [IsActive]              BIT           NOT NULL CONSTRAINT [DF_Users_IsActive] DEFAULT (1),
    [IsDeleted]             BIT           NOT NULL CONSTRAINT [DF_Users_IsDeleted] DEFAULT (0),
    [RowVersion]            ROWVERSION    NOT NULL,
    CONSTRAINT [PK_Users] PRIMARY KEY CLUSTERED ([UserId]),
    CONSTRAINT [UQ_Users_Username] UNIQUE ([Username]),
    CONSTRAINT [UQ_Users_Email] UNIQUE ([Email])
);
GO

-- -----------------------------------------------------------------------------
-- RolePermissions (many-to-many)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[RolePermissions]') AND type = 'U')
CREATE TABLE [auth].[RolePermissions] (
    [RolePermissionId]  INT IDENTITY(1,1) NOT NULL,
    [RoleId]            INT NOT NULL,
    [PermissionId]      INT NOT NULL,
    [CreatedDate]       DATETIME NOT NULL CONSTRAINT [DF_RolePermissions_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT      NULL,
    [ModifiedDate]      DATETIME NULL,
    [ModifiedBy]        INT      NULL,
    [IsActive]          BIT      NOT NULL CONSTRAINT [DF_RolePermissions_IsActive] DEFAULT (1),
    [IsDeleted]         BIT      NOT NULL CONSTRAINT [DF_RolePermissions_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION NOT NULL,
    CONSTRAINT [PK_RolePermissions] PRIMARY KEY CLUSTERED ([RolePermissionId]),
    CONSTRAINT [FK_RolePermissions_Roles] FOREIGN KEY ([RoleId]) REFERENCES [auth].[Roles]([RoleId]),
    CONSTRAINT [FK_RolePermissions_Permissions] FOREIGN KEY ([PermissionId]) REFERENCES [auth].[Permissions]([PermissionId]),
    CONSTRAINT [UQ_RolePermissions] UNIQUE ([RoleId], [PermissionId])
);
GO

-- -----------------------------------------------------------------------------
-- UserRoles (many-to-many)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[UserRoles]') AND type = 'U')
CREATE TABLE [auth].[UserRoles] (
    [UserRoleId]        INT IDENTITY(1,1) NOT NULL,
    [UserId]            INT NOT NULL,
    [RoleId]            INT NOT NULL,
    [CreatedDate]       DATETIME NOT NULL CONSTRAINT [DF_UserRoles_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT      NULL,
    [ModifiedDate]      DATETIME NULL,
    [ModifiedBy]        INT      NULL,
    [IsActive]          BIT      NOT NULL CONSTRAINT [DF_UserRoles_IsActive] DEFAULT (1),
    [IsDeleted]         BIT      NOT NULL CONSTRAINT [DF_UserRoles_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION NOT NULL,
    CONSTRAINT [PK_UserRoles] PRIMARY KEY CLUSTERED ([UserRoleId]),
    CONSTRAINT [FK_UserRoles_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId]),
    CONSTRAINT [FK_UserRoles_Roles] FOREIGN KEY ([RoleId]) REFERENCES [auth].[Roles]([RoleId]),
    CONSTRAINT [UQ_UserRoles] UNIQUE ([UserId], [RoleId])
);
GO

-- -----------------------------------------------------------------------------
-- UserSessions (active session tracking)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[UserSessions]') AND type = 'U')
CREATE TABLE [auth].[UserSessions] (
    [SessionId]         UNIQUEIDENTIFIER NOT NULL,
    [UserId]            INT              NOT NULL,
    [RefreshTokenHash]  NVARCHAR(255)    NOT NULL,
    [IpAddress]         NVARCHAR(45)     NULL,
    [UserAgent]         NVARCHAR(500)    NULL,
    [Browser]           NVARCHAR(100)    NULL,
    [Device]            NVARCHAR(100)    NULL,
    [OperatingSystem]   NVARCHAR(100)    NULL,
    [IsRememberMe]      BIT              NOT NULL CONSTRAINT [DF_UserSessions_IsRememberMe] DEFAULT (0),
    [ExpiresAt]         DATETIME         NOT NULL,
    [LastActivityDate]  DATETIME         NOT NULL CONSTRAINT [DF_UserSessions_LastActivity] DEFAULT (GETUTCDATE()),
    [IsRevoked]         BIT              NOT NULL CONSTRAINT [DF_UserSessions_IsRevoked] DEFAULT (0),
    [RevokedDate]       DATETIME         NULL,
    [RevokedReason]     NVARCHAR(200)    NULL,
    [CreatedDate]       DATETIME         NOT NULL CONSTRAINT [DF_UserSessions_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT              NULL,
    [ModifiedDate]      DATETIME         NULL,
    [ModifiedBy]        INT              NULL,
    [IsActive]          BIT              NOT NULL CONSTRAINT [DF_UserSessions_IsActive] DEFAULT (1),
    [IsDeleted]         BIT              NOT NULL CONSTRAINT [DF_UserSessions_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION       NOT NULL,
    CONSTRAINT [PK_UserSessions] PRIMARY KEY CLUSTERED ([SessionId]),
    CONSTRAINT [FK_UserSessions_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId])
);
GO

-- -----------------------------------------------------------------------------
-- RefreshTokens
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[RefreshTokens]') AND type = 'U')
CREATE TABLE [auth].[RefreshTokens] (
    [RefreshTokenId]    INT IDENTITY(1,1) NOT NULL,
    [UserId]            INT              NOT NULL,
    [SessionId]         UNIQUEIDENTIFIER NOT NULL,
    [TokenHash]         NVARCHAR(255)    NOT NULL,
    [ExpiresAt]         DATETIME         NOT NULL,
    [IsRevoked]         BIT              NOT NULL CONSTRAINT [DF_RefreshTokens_IsRevoked] DEFAULT (0),
    [RevokedDate]       DATETIME         NULL,
    [ReplacedByTokenId] INT              NULL,
    [CreatedDate]       DATETIME         NOT NULL CONSTRAINT [DF_RefreshTokens_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT              NULL,
    [ModifiedDate]      DATETIME         NULL,
    [ModifiedBy]        INT              NULL,
    [IsActive]          BIT              NOT NULL CONSTRAINT [DF_RefreshTokens_IsActive] DEFAULT (1),
    [IsDeleted]         BIT              NOT NULL CONSTRAINT [DF_RefreshTokens_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION       NOT NULL,
    CONSTRAINT [PK_RefreshTokens] PRIMARY KEY CLUSTERED ([RefreshTokenId]),
    CONSTRAINT [FK_RefreshTokens_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId]),
    CONSTRAINT [FK_RefreshTokens_Sessions] FOREIGN KEY ([SessionId]) REFERENCES [auth].[UserSessions]([SessionId])
);
GO

-- -----------------------------------------------------------------------------
-- RevokedTokens (JWT jti blacklist)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[RevokedTokens]') AND type = 'U')
CREATE TABLE [auth].[RevokedTokens] (
    [RevokedTokenId]    INT IDENTITY(1,1) NOT NULL,
    [Jti]               NVARCHAR(100) NOT NULL,
    [TokenType]         NVARCHAR(20)  NOT NULL,
    [UserId]            INT           NULL,
    [ExpiresAt]         DATETIME      NOT NULL,
    [RevokedDate]       DATETIME      NOT NULL CONSTRAINT [DF_RevokedTokens_RevokedDate] DEFAULT (GETUTCDATE()),
    [RevokedReason]     NVARCHAR(200) NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_RevokedTokens_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_RevokedTokens_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_RevokedTokens_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_RevokedTokens] PRIMARY KEY CLUSTERED ([RevokedTokenId]),
    CONSTRAINT [UQ_RevokedTokens_Jti] UNIQUE ([Jti])
);
GO

-- -----------------------------------------------------------------------------
-- PasswordHistory
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[PasswordHistory]') AND type = 'U')
CREATE TABLE [auth].[PasswordHistory] (
    [PasswordHistoryId] INT IDENTITY(1,1) NOT NULL,
    [UserId]            INT           NOT NULL,
    [PasswordHash]      NVARCHAR(255) NOT NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_PasswordHistory_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_PasswordHistory_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_PasswordHistory_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_PasswordHistory] PRIMARY KEY CLUSTERED ([PasswordHistoryId]),
    CONSTRAINT [FK_PasswordHistory_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId])
);
GO

-- -----------------------------------------------------------------------------
-- PasswordResetTokens
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[PasswordResetTokens]') AND type = 'U')
CREATE TABLE [auth].[PasswordResetTokens] (
    [PasswordResetTokenId] INT IDENTITY(1,1) NOT NULL,
    [UserId]               INT           NOT NULL,
    [TokenHash]            NVARCHAR(255) NOT NULL,
    [ExpiresAt]            DATETIME      NOT NULL,
    [IsUsed]               BIT           NOT NULL CONSTRAINT [DF_PasswordResetTokens_IsUsed] DEFAULT (0),
    [UsedDate]             DATETIME      NULL,
    [CreatedDate]          DATETIME      NOT NULL CONSTRAINT [DF_PasswordResetTokens_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]            INT           NULL,
    [ModifiedDate]         DATETIME      NULL,
    [ModifiedBy]           INT           NULL,
    [IsActive]             BIT           NOT NULL CONSTRAINT [DF_PasswordResetTokens_IsActive] DEFAULT (1),
    [IsDeleted]            BIT           NOT NULL CONSTRAINT [DF_PasswordResetTokens_IsDeleted] DEFAULT (0),
    [RowVersion]           ROWVERSION    NOT NULL,
    CONSTRAINT [PK_PasswordResetTokens] PRIMARY KEY CLUSTERED ([PasswordResetTokenId]),
    CONSTRAINT [FK_PasswordResetTokens_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId])
);
GO

-- -----------------------------------------------------------------------------
-- LoginHistory
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[LoginHistory]') AND type = 'U')
CREATE TABLE [auth].[LoginHistory] (
    [LoginHistoryId]    INT IDENTITY(1,1) NOT NULL,
    [UserId]            INT           NULL,
    [Username]          NVARCHAR(100) NOT NULL,
    [LoginStatus]       NVARCHAR(20)  NOT NULL,
    [FailureReason]     NVARCHAR(200) NULL,
    [IpAddress]         NVARCHAR(45)  NULL,
    [UserAgent]         NVARCHAR(500) NULL,
    [Browser]           NVARCHAR(100) NULL,
    [Device]            NVARCHAR(100) NULL,
    [OperatingSystem]   NVARCHAR(100) NULL,
    [SessionId]         UNIQUEIDENTIFIER NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_LoginHistory_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_LoginHistory_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_LoginHistory_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_LoginHistory] PRIMARY KEY CLUSTERED ([LoginHistoryId]),
    CONSTRAINT [FK_LoginHistory_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId])
);
GO

-- -----------------------------------------------------------------------------
-- AuditLogs
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[AuditLogs]') AND type = 'U')
CREATE TABLE [auth].[AuditLogs] (
    [AuditLogId]        BIGINT IDENTITY(1,1) NOT NULL,
    [UserId]            INT           NULL,
    [Username]          NVARCHAR(100) NULL,
    [Action]            NVARCHAR(100) NOT NULL,
    [EntityType]        NVARCHAR(100) NULL,
    [EntityId]          NVARCHAR(100) NULL,
    [OldValues]         NVARCHAR(MAX) NULL,
    [NewValues]         NVARCHAR(MAX) NULL,
    [IpAddress]         NVARCHAR(45)  NULL,
    [UserAgent]         NVARCHAR(500) NULL,
    [Status]            NVARCHAR(20)  NOT NULL CONSTRAINT [DF_AuditLogs_Status] DEFAULT ('SUCCESS'),
    [ErrorMessage]      NVARCHAR(500) NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_AuditLogs_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_AuditLogs_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_AuditLogs_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_AuditLogs] PRIMARY KEY CLUSTERED ([AuditLogId])
);
GO

-- -----------------------------------------------------------------------------
-- UserPreferences
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[UserPreferences]') AND type = 'U')
CREATE TABLE [auth].[UserPreferences] (
    [UserPreferenceId]  INT IDENTITY(1,1) NOT NULL,
    [UserId]            INT           NOT NULL,
    [PreferenceKey]     NVARCHAR(100) NOT NULL,
    [PreferenceValue]   NVARCHAR(500) NOT NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_UserPreferences_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_UserPreferences_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_UserPreferences_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_UserPreferences] PRIMARY KEY CLUSTERED ([UserPreferenceId]),
    CONSTRAINT [FK_UserPreferences_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId]),
    CONSTRAINT [UQ_UserPreferences] UNIQUE ([UserId], [PreferenceKey])
);
GO

PRINT 'All authentication tables created successfully.';
GO
