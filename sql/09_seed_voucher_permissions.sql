-- Seed voucher entry permissions (same GL tables as VB6)
USE [NSDS2626_AUTH];
GO

DECLARE @GlModuleId INT;
SELECT @GlModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'GL';

IF @GlModuleId IS NULL
BEGIN
    INSERT INTO [auth].[Modules] (ModuleCode, ModuleName, Description, DisplayOrder, IsActive)
    VALUES ('GL', 'General Ledger', 'Voucher and GL entry', 15, 1);
    SET @GlModuleId = SCOPE_IDENTITY();
END

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'gl.voucher.view')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@GlModuleId, 'gl.voucher.view', 'View Voucher Entry', 'Open voucher entry and lookups');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'gl.voucher.create')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@GlModuleId, 'gl.voucher.create', 'Create Vouchers', 'Save new vouchers to GL0002/GL0003');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'gl.voucher.edit')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@GlModuleId, 'gl.voucher.edit', 'Edit Vouchers', 'Edit unposted vouchers');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'gl.voucher.delete')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@GlModuleId, 'gl.voucher.delete', 'Delete Vouchers', 'Delete unposted vouchers');
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode LIKE 'gl.voucher.%'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
