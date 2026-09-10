-- Seed cheque printing permissions (auth DB + ERP CHEQUE_PERMISSION for VB6)
USE [NSDS2626_AUTH];
GO

DECLARE @ModId INT;
SELECT @ModId = ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'CHEQUE';

IF @ModId IS NULL
BEGIN
    INSERT INTO [auth].[Modules] (ModuleCode, ModuleName, Description, DisplayOrder, IsActive)
    VALUES ('CHEQUE', 'Cheque Printing', 'Enterprise cheque layout and print management', 25, 1);
    SET @ModId = SCOPE_IDENTITY();
END

DECLARE @Perms TABLE (Code NVARCHAR(100), Name NVARCHAR(150), Descr NVARCHAR(500));
INSERT INTO @Perms (Code, Name, Descr) VALUES
('cheque.print',          'Print Cheque',            'Print cheque from voucher'),
('cheque.reprint',        'Reprint Cheque',          'Confirm and reprint already printed cheques'),
('cheque.preview',        'Preview Cheque',          'Open print preview'),
('cheque.layout.create',  'Create Layout',           'Create new bank cheque layouts'),
('cheque.layout.edit',    'Edit Layout',             'Edit cheque layout designer'),
('cheque.layout.delete',  'Delete Layout',           'Delete cheque layouts'),
('cheque.cancel',         'Cancel Cheque',           'Cancel or void printed cheques'),
('cheque.export_pdf',     'Export PDF',              'Export cheque preview to PDF/image'),
('cheque.calibrate',      'Calibrate Printer',       'Alignment wizard offsets'),
('cheque.batch',          'Batch Print',             'Print multiple cheques'),
('cheque.history',        'Cheque History',          'Search and view cheque audit trail');

INSERT INTO [auth].[Permissions] (ModuleId, PermissionCode, PermissionName, Description)
SELECT @ModId, p.Code, p.Name, p.Descr
FROM @Perms p
WHERE NOT EXISTS (
    SELECT 1 FROM [auth].[Permissions] x WHERE x.PermissionCode = p.Code
);
GO

INSERT INTO [auth].[RolePermissions] (RoleId, PermissionId)
SELECT r.RoleId, p.PermissionId
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.RoleCode IN ('SUPER_ADMIN', 'ADMIN')
  AND p.PermissionCode LIKE 'cheque.%'
  AND NOT EXISTS (
      SELECT 1 FROM [auth].[RolePermissions] rp
      WHERE rp.RoleId = r.RoleId AND rp.PermissionId = p.PermissionId
  );
GO

PRINT 'Cheque printing auth permissions seeded.';
GO
