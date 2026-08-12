-- Seed Purchase Receipt (Fin_PurM) permissions
USE [NSDS2626_AUTH];
GO

DECLARE @InvModuleId INT;
SELECT @InvModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'INVENTORY';

IF @InvModuleId IS NULL
BEGIN
    INSERT INTO [auth].[Modules] (ModuleCode, ModuleName, Description, DisplayOrder, IsActive)
    VALUES ('INVENTORY', 'Inventory', 'Inventory and purchase', 20, 1);
    SET @InvModuleId = SCOPE_IDENTITY();
END

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_pur.view')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_pur.view', 'View Purchase Receipt', 'Open Purchase Receipt (Fin_PurM)');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_pur.create')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_pur.create', 'Create Purchase Receipt', 'Save new GRN / purchase documents');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_pur.edit')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_pur.edit', 'Edit Purchase Receipt', 'Edit unposted purchase documents');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_pur.delete')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_pur.delete', 'Delete Purchase Receipt', 'Delete unposted purchase documents');
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode LIKE 'inventory.fin_pur.%'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
