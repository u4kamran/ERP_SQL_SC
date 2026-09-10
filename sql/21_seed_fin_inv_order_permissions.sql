-- Seed Purchase Order (Fin_InvM_Order) permissions
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

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_inv_order.view')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_inv_order.view', 'View Purchase Order', 'Open Purchase Order (Fin_InvM_Order)');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_inv_order.create')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_inv_order.create', 'Create Purchase Order', 'Save new purchase orders');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_inv_order.edit')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_inv_order.edit', 'Edit Purchase Order', 'Edit unposted purchase orders');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'inventory.fin_inv_order.delete')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@InvModuleId, 'inventory.fin_inv_order.delete', 'Delete Purchase Order', 'Delete unposted purchase orders');
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode LIKE 'inventory.fin_inv_order.%'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
