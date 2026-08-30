-- Seed Item Image Manager permissions (auth DB only).
USE [NSDS2626_AUTH];
GO

SET NOCOUNT ON;

DECLARE @InvModuleId INT;
SELECT @InvModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'INVENTORY';

IF @InvModuleId IS NULL
    SELECT @InvModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @InvModuleId IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.item_images.view')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @InvModuleId,
            'inventory.item_images.view',
            'View Item Images',
            'View Item Image Manager, coverage, and candidates'
        );

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.item_images.manage')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @InvModuleId,
            'inventory.item_images.manage',
            'Manage Item Images',
            'Search, approve, reject, upload, and configure item images'
        );

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.item_images.bulk')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @InvModuleId,
            'inventory.item_images.bulk',
            'Bulk Item Image Fetch',
            'Start, pause, resume, or cancel bulk image fetch jobs'
        );
END;
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode IN (
      'inventory.item_images.view',
      'inventory.item_images.manage',
      'inventory.item_images.bulk'
  )
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
