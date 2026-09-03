-- Per-report View / Email / WhatsApp permissions (each report has its own rights).
-- Idempotent. Prefer: python scripts/seed_report_delivery_permissions.py --site erp
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

DECLARE @Codes TABLE (PermissionCode NVARCHAR(100), PermissionName NVARCHAR(150), Description NVARCHAR(500));
INSERT INTO @Codes (PermissionCode, PermissionName, Description) VALUES
('reports.gl_ledger.view', 'View GL Ledger Report', 'Open desktop GL Ledger report'),
('reports.gl_ledger.email', 'Email GL Ledger Report', 'Email PDF from desktop GL Ledger'),
('reports.gl_ledger.whatsapp', 'WhatsApp GL Ledger Report', 'WhatsApp PDF from desktop GL Ledger'),
('reports.gl_ledger_detailed.view', 'View Customer Ledger (Detailed)', 'Open detailed customer ledger with invoice lines'),
('reports.gl_ledger_detailed.email', 'Email Customer Ledger (Detailed)', 'Email detailed customer ledger PDF'),
('reports.gl_ledger_detailed.whatsapp', 'WhatsApp Customer Ledger (Detailed)', 'WhatsApp detailed customer ledger PDF'),
('reports.gl_ledger_mobile.view', 'View GL Ledger (Mobile)', 'Open mobile GL Ledger report'),
('reports.gl_ledger_mobile.email', 'Email GL Ledger (Mobile)', 'Email PDF from mobile GL Ledger'),
('reports.gl_ledger_mobile.whatsapp', 'WhatsApp GL Ledger (Mobile)', 'WhatsApp PDF from mobile GL Ledger'),
('reports.gl_credit_summary.view', 'View Credit Summary Ledger', 'Open Credit Summary Ledger'),
('reports.gl_credit_summary.email', 'Email Credit Summary Ledger', 'Email PDF from Credit Summary'),
('reports.trial_balance_d2d.view', 'View Trial Balance D2D', 'Open Trial Balance D2D'),
('reports.trial_balance_d2d.email', 'Email Trial Balance D2D', 'Email PDF from Trial Balance D2D'),
('reports.trial_balance_d2d.whatsapp', 'WhatsApp Trial Balance D2D', 'WhatsApp PDF from Trial Balance D2D'),
('reports.trial_balance_d2d_mobile.view', 'View Trial Balance D2D (Mobile)', 'Open mobile Trial Balance'),
('reports.trial_balance_d2d_mobile.email', 'Email Trial Balance D2D (Mobile)', 'Email PDF from mobile Trial Balance'),
('reports.trial_balance_d2d_mobile.whatsapp', 'WhatsApp Trial Balance D2D (Mobile)', 'WhatsApp PDF from mobile Trial Balance'),
('reports.stock_balance_d2d.view', 'View Stock Balance D2D', 'Open Stock Balance D2D'),
('reports.stock_balance_d2d.email', 'Email Stock Balance D2D', 'Email PDF from Stock Balance D2D'),
('reports.sales_dashboard.view', 'View Sales Dashboard', 'Open sales dashboard'),
('reports.sales_dashboard.email', 'Email Sales Dashboard', 'Sales Dashboard email'),
('reports.sms_email.manage', 'Manage SMS Sales Email', 'SMS_DB_ sales email scheduler');

INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
SELECT @ReportsModuleId, c.PermissionCode, c.PermissionName, c.Description
FROM @Codes c
WHERE NOT EXISTS (
    SELECT 1 FROM [auth].[Permissions] p WHERE p.PermissionCode = c.PermissionCode
);
GO

-- Grant all report perms to SUPER_ADMIN / ADMIN
INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode LIKE 'reports.%'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO

PRINT 'Per-report permissions seeded.';
GO
