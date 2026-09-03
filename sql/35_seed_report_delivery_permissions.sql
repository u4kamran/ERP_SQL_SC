-- Additive seed: report Email / WhatsApp delivery permissions (Option A).
-- PDF remains tied to *.view. No schema changes.
-- Idempotent. Grants delivery rights to roles that already have the matching view
-- so existing users keep current behaviour until an admin tightens Menu Rights.
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
GO

DECLARE @ReportsModuleId INT = (SELECT ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'reports.gl_ledger.email')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ReportsModuleId, 'reports.gl_ledger.email', 'Email GL / Ledger Reports',
            'Email PDF for GL Ledger, Credit Summary, Trial Balance, Stock Balance');
END

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'reports.gl_ledger.whatsapp')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ReportsModuleId, 'reports.gl_ledger.whatsapp', 'WhatsApp GL / Ledger Reports',
            'Send PDF via WhatsApp for GL Ledger and Trial Balance');
END

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'reports.sales_dashboard.email')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ReportsModuleId, 'reports.sales_dashboard.email', 'Email Sales Dashboard',
            'Configure and send Sales Dashboard scheduled / test emails');
END
GO

-- Grant delivery perms to SUPER_ADMIN / ADMIN / REPORTS_ONLY when they already have the view
INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
INNER JOIN [auth].[Permissions] pv
    ON pv.PermissionCode = 'reports.gl_ledger.view'
INNER JOIN [auth].[RolePermissions] rpv
    ON rpv.RoleId = r.RoleId
   AND rpv.PermissionId = pv.PermissionId
   AND ISNULL(rpv.IsDeleted, 0) = 0
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'REPORTS_ONLY')
  AND p.PermissionCode IN ('reports.gl_ledger.email', 'reports.gl_ledger.whatsapp')
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
INNER JOIN [auth].[Permissions] pv
    ON pv.PermissionCode = 'reports.sales_dashboard.view'
INNER JOIN [auth].[RolePermissions] rpv
    ON rpv.RoleId = r.RoleId
   AND rpv.PermissionId = pv.PermissionId
   AND ISNULL(rpv.IsDeleted, 0) = 0
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'REPORTS_ONLY')
  AND p.PermissionCode = 'reports.sales_dashboard.email'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO

PRINT 'Report delivery permissions (email/whatsapp) seeded.';
GO
