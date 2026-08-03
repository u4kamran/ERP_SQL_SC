-- Seed sales dashboard report permission and REPORTS_ONLY role
USE [NSDS2626_AUTH];
GO

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
BEGIN
    INSERT INTO [auth].[Modules] (ModuleCode, ModuleName, Description, DisplayOrder, IsActive)
    VALUES ('REPORTS', 'Reports', 'Reporting and analytics', 12, 1);
    SET @ReportsModuleId = SCOPE_IDENTITY();
END

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'reports.sales_dashboard.view')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ReportsModuleId, 'reports.sales_dashboard.view', 'View Sales Dashboard', 'Open sales dashboard and KPI reports');
END
GO

-- Grant sales dashboard permission to admin roles
INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode = 'reports.sales_dashboard.view'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO

-- Reports-only role: view reports + own profile (no inventory, vouchers, or admin)
IF NOT EXISTS (SELECT 1 FROM [auth].[Roles] WHERE RoleCode = 'REPORTS_ONLY')
BEGIN
    INSERT INTO [auth].[Roles] (RoleCode, RoleName, Description, IsSystemRole)
    VALUES ('REPORTS_ONLY', 'Reports Only', 'View sales and GL reports only', 1);
END
GO

DECLARE @ReportsRoleId INT = (SELECT RoleId FROM [auth].[Roles] WHERE RoleCode = 'REPORTS_ONLY');

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT @ReportsRoleId, p.PermissionId
FROM [auth].[Permissions] p
WHERE p.PermissionCode IN (
    'reports.sales_dashboard.view',
    'reports.gl_ledger.view',
    'auth.profile.view',
    'auth.profile.update',
    'auth.profile.change_password'
)
AND NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @ReportsRoleId AND rp.PermissionId = p.PermissionId
);
GO

PRINT 'REPORTS_ONLY role seeded.';
GO
