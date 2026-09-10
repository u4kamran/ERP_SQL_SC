-- =============================================================================
-- User Menu Rights (auth.Menus + auth.UserMenuRights)
-- SQL Server 2008 Compatible
-- Run against the AUTH database (NSDS2626_AUTH / NAHSL2627_AUTH).
-- =============================================================================

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[Menus]') AND type = 'U')
CREATE TABLE [auth].[Menus] (
    [MenuId]            INT IDENTITY(1,1) NOT NULL,
    [MenuCode]          NVARCHAR(120) NOT NULL,
    [MenuName]          NVARCHAR(150) NOT NULL,
    [MenuGroup]         NVARCHAR(100) NOT NULL,
    [ParentMenuCode]    NVARCHAR(120) NULL,
    [Path]              NVARCHAR(255) NULL,
    [IconClass]         NVARCHAR(100) NULL,
    [PermissionCode]    NVARCHAR(100) NULL,
    [Description]       NVARCHAR(500) NULL,
    [DisplayOrder]      INT           NOT NULL CONSTRAINT [DF_Menus_DisplayOrder] DEFAULT (0),
    [IsGroup]           BIT           NOT NULL CONSTRAINT [DF_Menus_IsGroup] DEFAULT (0),
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_Menus_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_Menus_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_Menus_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_Menus] PRIMARY KEY CLUSTERED ([MenuId]),
    CONSTRAINT [UQ_Menus_MenuCode] UNIQUE ([MenuCode])
);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_Menus_ParentMenuCode' AND object_id = OBJECT_ID(N'[auth].[Menus]'))
CREATE NONCLUSTERED INDEX [IX_Menus_ParentMenuCode] ON [auth].[Menus]([ParentMenuCode]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_Menus_Path' AND object_id = OBJECT_ID(N'[auth].[Menus]'))
CREATE NONCLUSTERED INDEX [IX_Menus_Path] ON [auth].[Menus]([Path]);
GO

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[auth].[UserMenuRights]') AND type = 'U')
CREATE TABLE [auth].[UserMenuRights] (
    [UserMenuRightId]   INT IDENTITY(1,1) NOT NULL,
    [UserId]            INT           NOT NULL,
    [MenuId]            INT           NOT NULL,
    [CanAccess]         BIT           NOT NULL CONSTRAINT [DF_UserMenuRights_CanAccess] DEFAULT (0),
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_UserMenuRights_CreatedDate] DEFAULT (GETUTCDATE()),
    [CreatedBy]         INT           NULL,
    [ModifiedDate]      DATETIME      NULL,
    [ModifiedBy]        INT           NULL,
    [IsActive]          BIT           NOT NULL CONSTRAINT [DF_UserMenuRights_IsActive] DEFAULT (1),
    [IsDeleted]         BIT           NOT NULL CONSTRAINT [DF_UserMenuRights_IsDeleted] DEFAULT (0),
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_UserMenuRights] PRIMARY KEY CLUSTERED ([UserMenuRightId]),
    CONSTRAINT [FK_UserMenuRights_Users] FOREIGN KEY ([UserId]) REFERENCES [auth].[Users]([UserId]),
    CONSTRAINT [FK_UserMenuRights_Menus] FOREIGN KEY ([MenuId]) REFERENCES [auth].[Menus]([MenuId]),
    CONSTRAINT [UQ_UserMenuRights_UserMenu] UNIQUE ([UserId], [MenuId])
);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_UserMenuRights_UserId' AND object_id = OBJECT_ID(N'[auth].[UserMenuRights]'))
CREATE NONCLUSTERED INDEX [IX_UserMenuRights_UserId] ON [auth].[UserMenuRights]([UserId]) INCLUDE ([MenuId], [CanAccess], [IsDeleted]);
GO
