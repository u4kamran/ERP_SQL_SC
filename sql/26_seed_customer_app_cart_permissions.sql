-- Seed Customer App Cart permissions (staff ERP screen).
USE [NSDS2626_AUTH];
GO

SET NOCOUNT ON;

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
    SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @ReportsModuleId IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.customer_app_carts.view')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @ReportsModuleId,
            'marketing.customer_app_carts.view',
            'View Customer App Carts',
            'View mobile-app saved customer carts (not WhatsApp WO orders)'
        );

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.customer_app_carts.update')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @ReportsModuleId,
            'marketing.customer_app_carts.update',
            'Update Customer App Carts',
            'Change status of mobile-app saved carts (review / contact / confirm)'
        );

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.customer_app_carts.cancel')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @ReportsModuleId,
            'marketing.customer_app_carts.cancel',
            'Cancel Customer App Carts',
            'Cancel mobile-app saved carts'
        );

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.customer_app_carts.convert')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @ReportsModuleId,
            'marketing.customer_app_carts.convert',
            'Convert Customer App Carts',
            'Convert saved cart to ERP sales order (Phase 2 — stub until sales API exists)'
        );
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode IN (
      'marketing.customer_app_carts.view',
      'marketing.customer_app_carts.update',
      'marketing.customer_app_carts.cancel',
      'marketing.customer_app_carts.convert'
  )
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
