-- Seed SMS_DB_ email scheduler permissions
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

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'reports.sms_email.manage')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ReportsModuleId, 'reports.sms_email.manage', 'Manage SMS Sales Email', 'Configure and run SMS_DB_ sales email scheduler');
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode = 'reports.sms_email.manage'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
