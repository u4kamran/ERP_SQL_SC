-- Seed WhatsApp chatbot permissions
USE [NSDS2626_AUTH];
GO

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
    SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @ReportsModuleId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.whatsapp_bot.view')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (
        @ReportsModuleId,
        'marketing.whatsapp_bot.view',
        'View WhatsApp Chatbot',
        'View WhatsApp and offline chatbot inbox'
    );
END

IF @ReportsModuleId IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.whatsapp_bot.manage')
BEGIN
    INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
    VALUES (
        @ReportsModuleId,
        'marketing.whatsapp_bot.manage',
        'Manage WhatsApp Chatbot',
        'Configure chatbot, reply as staff, and toggle online mode'
    );
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode IN ('marketing.whatsapp_bot.view', 'marketing.whatsapp_bot.manage')
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
