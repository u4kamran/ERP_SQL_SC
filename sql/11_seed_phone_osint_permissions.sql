-- Seed support phone OSINT lookup permissions
USE [NSDS2626_AUTH];
GO

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
BEGIN
    SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';
END

IF @ReportsModuleId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'support.phone_osint.view')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (
        @ReportsModuleId,
        'support.phone_osint.view',
        'View Phone OSINT Lookup',
        'Search customer phones against ERP and generate public OSINT links'
    );
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode = 'support.phone_osint.view'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
