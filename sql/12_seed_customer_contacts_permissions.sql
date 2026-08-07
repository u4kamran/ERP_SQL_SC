-- Seed customer marketing contacts permissions
USE [NSDS2626_AUTH];
GO

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
    SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @ReportsModuleId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.customer_contacts.view')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (
        @ReportsModuleId,
        'marketing.customer_contacts.view',
        'View Customer Contacts',
        'View customer phones, emails, and social links for marketing'
    );
END

IF @ReportsModuleId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.customer_contacts.manage')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (
        @ReportsModuleId,
        'marketing.customer_contacts.manage',
        'Manage Customer Contacts',
        'Edit customer marketing emails and social media links'
    );
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode IN ('marketing.customer_contacts.view', 'marketing.customer_contacts.manage')
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
