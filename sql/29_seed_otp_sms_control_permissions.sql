-- Seed OTP / SMS master control permissions
USE [NSDS2626_AUTH];
GO

SET NOCOUNT ON;

DECLARE @AuthModuleId INT;
SELECT @AuthModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @AuthModuleId IS NULL
    SELECT @AuthModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @AuthModuleId IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'auth.otp_sms_control.view')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @AuthModuleId,
            'auth.otp_sms_control.view',
            'View OTP SMS Control',
            'View master / web / mobile OTP SMS enablement'
        );

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'auth.otp_sms_control.manage')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (
            @AuthModuleId,
            'auth.otp_sms_control.manage',
            'Manage OTP SMS Control',
            'Enable or disable OTP SMS for web and mobile applications'
        );
END;
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode IN ('auth.otp_sms_control.view', 'auth.otp_sms_control.manage')
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
