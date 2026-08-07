-- Seed promotion hub permissions
USE [NSDS2626_AUTH];
GO

DECLARE @ModuleId INT;
SELECT @ModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';
IF @ModuleId IS NULL SELECT @ModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @ModuleId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.promotion.view')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ModuleId, 'marketing.promotion.view', 'View Promotion Hub', 'Access promotion hub and social discovery');

IF @ModuleId IS NOT NULL AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.promotion.send')
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (@ModuleId, 'marketing.promotion.send', 'Send Promotions', 'Send WhatsApp and email promotions to customers');
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode IN ('marketing.promotion.view', 'marketing.promotion.send')
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
