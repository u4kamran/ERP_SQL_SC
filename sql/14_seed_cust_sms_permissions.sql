-- Seed CUST_SMS CRUD permissions
USE [NSDS2626_AUTH];
GO

DECLARE @ReportsModuleId INT;
SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'REPORTS';

IF @ReportsModuleId IS NULL
    SELECT @ReportsModuleId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH';

IF @ReportsModuleId IS NOT NULL
BEGIN
    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.cust_sms.view')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (@ReportsModuleId, 'marketing.cust_sms.view', 'View CUST_SMS', 'View Customer SMS (CUST_SMS) master records');

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.cust_sms.create')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (@ReportsModuleId, 'marketing.cust_sms.create', 'Create CUST_SMS', 'Create Customer SMS (CUST_SMS) records');

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.cust_sms.update')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (@ReportsModuleId, 'marketing.cust_sms.update', 'Update CUST_SMS', 'Update Customer SMS (CUST_SMS) records');

    IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE PermissionCode = 'marketing.cust_sms.delete')
        INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
        VALUES (@ReportsModuleId, 'marketing.cust_sms.delete', 'Delete CUST_SMS', 'Delete Customer SMS (CUST_SMS) records');
END
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN', 'USER')
  AND p.PermissionCode IN (
      'marketing.cust_sms.view',
      'marketing.cust_sms.create',
      'marketing.cust_sms.update',
      'marketing.cust_sms.delete'
  )
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO
