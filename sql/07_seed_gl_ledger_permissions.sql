-- Seed General Ledger report permissions
USE [NSDS2626_AUTH];
GO

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
BEGIN
    INSERT INTO [auth].[Modules] (ModuleCode, ModuleName, Description, DisplayOrder, IsActive)
    VALUES ('REPORTS', 'Reports', 'ERP reports', 20, 1);
    SET @ReportsModuleId = SCOPE_IDENTITY();
END

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'reports.gl_ledger.view')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ReportsModuleId, 'reports.gl_ledger.view', 'View GL Ledger Report', 'Generate General Ledger PDF report');
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode = 'reports.gl_ledger.view'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
