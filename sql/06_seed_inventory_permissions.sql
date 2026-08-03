-- =============================================================================
-- Seed inventory FIN_ITEM permissions
-- Run against NSDS2626_AUTH database
-- =============================================================================

USE [NSDS2626_AUTH];
GO

DECLARE @InvModuleId INT = (SELECT ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'INVENTORY');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_item.view')
INSERT INTO [auth].[Permissions] ([ModuleId], [PermissionCode], [PermissionName], [Description])
VALUES
    (@InvModuleId, 'inventory.fin_item.view',   'View Items',   'View FIN_ITEM inventory items'),
    (@InvModuleId, 'inventory.fin_item.create', 'Create Items', 'Create FIN_ITEM records'),
    (@InvModuleId, 'inventory.fin_item.update', 'Update Items', 'Update FIN_ITEM records'),
    (@InvModuleId, 'inventory.fin_item.delete', 'Delete Items', 'Delete FIN_ITEM records');
GO

-- Grant to SUPER_ADMIN and ADMIN roles
DECLARE @SuperAdminId INT = (SELECT RoleId FROM [auth].[Roles] WHERE RoleCode = 'SUPER_ADMIN');
DECLARE @AdminId INT = (SELECT RoleId FROM [auth].[Roles] WHERE RoleCode = 'ADMIN');
DECLARE @UserRoleId INT = (SELECT RoleId FROM [auth].[Roles] WHERE RoleCode = 'USER');

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT @SuperAdminId, p.PermissionId
FROM [auth].[Permissions] p
WHERE p.PermissionCode LIKE 'inventory.fin_item.%'
AND NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @SuperAdminId AND rp.PermissionId = p.PermissionId
);

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT @AdminId, p.PermissionId
FROM [auth].[Permissions] p
WHERE p.PermissionCode LIKE 'inventory.fin_item.%'
AND NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @AdminId AND rp.PermissionId = p.PermissionId
);

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT @UserRoleId, p.PermissionId
FROM [auth].[Permissions] p
WHERE p.PermissionCode LIKE 'inventory.fin_item.%'
AND NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @UserRoleId AND rp.PermissionId = p.PermissionId
);
GO
