-- =============================================================================
-- AH Steel Lab - Seed Data
-- Database: NSDS2626_AUTH | Schema: auth
-- Default admin password: ChangeMe@2026! (must change on first login)
-- BCrypt hash generated with 12 rounds
-- =============================================================================

USE [NSDS2626_AUTH];
GO

SET NOCOUNT ON;

-- -----------------------------------------------------------------------------
-- ERP Modules (future-ready)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM [auth].[Modules] WHERE [ModuleCode] = 'AUTH')
INSERT INTO [auth].[Modules] ([ModuleCode], [ModuleName], [Description], [DisplayOrder], [IconClass])
VALUES
    ('AUTH',      'Authentication',  'User authentication and authorization', 1,  'bi-shield-lock'),
    ('DASHBOARD', 'Dashboard',       'Main dashboard and analytics',          2,  'bi-speedometer2'),
    ('INVENTORY', 'Inventory',       'Inventory management',                  3,  'bi-box-seam'),
    ('PURCHASE',  'Purchase',        'Purchase orders and procurement',       4,  'bi-cart-plus'),
    ('SALES',     'Sales',           'Sales orders and invoicing',            5,  'bi-receipt'),
    ('ACCOUNTS',  'Accounts',        'Accounting and finance',                6,  'bi-calculator'),
    ('POS',       'Point of Sale',   'POS terminal operations',               7,  'bi-shop'),
    ('PAYROLL',   'Payroll',         'Payroll processing',                    8,  'bi-cash-stack'),
    ('HR',        'Human Resources', 'HR management',                         9,  'bi-people'),
    ('PRODUCTION','Production',      'Production planning',                   10, 'bi-gear'),
    ('CRM',       'CRM',             'Customer relationship management',      11, 'bi-person-lines-fill'),
    ('REPORTS',   'Reports',         'Reporting and analytics',               12, 'bi-file-earmark-bar-graph');
GO

-- -----------------------------------------------------------------------------
-- Features per module
-- -----------------------------------------------------------------------------
DECLARE @AuthModuleId INT = (SELECT ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH');

IF NOT EXISTS (SELECT 1 FROM [auth].[Features] WHERE [FeatureCode] = 'USERS' AND [ModuleId] = @AuthModuleId)
INSERT INTO [auth].[Features] ([ModuleId], [FeatureCode], [FeatureName], [Description], [DisplayOrder])
VALUES
    (@AuthModuleId, 'USERS',       'User Management',       'Manage system users',           1),
    (@AuthModuleId, 'ROLES',       'Role Management',       'Manage roles and assignments',  2),
    (@AuthModuleId, 'PERMISSIONS', 'Permission Management', 'Manage permissions',            3),
    (@AuthModuleId, 'SESSIONS',    'Session Management',    'Manage active sessions',        4),
    (@AuthModuleId, 'AUDIT',       'Audit Logs',            'View audit trail',              5),
    (@AuthModuleId, 'PROFILE',     'User Profile',          'User profile management',       6);
GO

-- -----------------------------------------------------------------------------
-- Permissions
-- -----------------------------------------------------------------------------
DECLARE @AuthModuleId2 INT = (SELECT ModuleId FROM [auth].[Modules] WHERE ModuleCode = 'AUTH');

IF NOT EXISTS (SELECT 1 FROM [auth].[Permissions] WHERE [PermissionCode] = 'auth.users.view')
INSERT INTO [auth].[Permissions] ([ModuleId], [PermissionCode], [PermissionName], [Description])
VALUES
    (@AuthModuleId2, 'auth.users.view',           'View Users',           'View user list and details'),
    (@AuthModuleId2, 'auth.users.create',         'Create Users',         'Create new users'),
    (@AuthModuleId2, 'auth.users.update',         'Update Users',         'Update user information'),
    (@AuthModuleId2, 'auth.users.delete',         'Delete Users',         'Deactivate/delete users'),
    (@AuthModuleId2, 'auth.roles.view',           'View Roles',           'View roles'),
    (@AuthModuleId2, 'auth.roles.manage',         'Manage Roles',         'Create/update/delete roles'),
    (@AuthModuleId2, 'auth.permissions.view',     'View Permissions',     'View permissions'),
    (@AuthModuleId2, 'auth.permissions.manage',   'Manage Permissions',   'Assign permissions to roles'),
    (@AuthModuleId2, 'auth.sessions.view',        'View Sessions',        'View active sessions'),
    (@AuthModuleId2, 'auth.sessions.revoke',      'Revoke Sessions',      'Force logout sessions'),
    (@AuthModuleId2, 'auth.audit.view',           'View Audit Logs',      'View audit trail'),
    (@AuthModuleId2, 'auth.profile.view',         'View Profile',         'View own profile'),
    (@AuthModuleId2, 'auth.profile.update',       'Update Profile',       'Update own profile'),
    (@AuthModuleId2, 'auth.profile.change_password','Change Password',    'Change own password'),
    (@AuthModuleId2, 'auth.admin.full',           'Full Admin Access',    'Full administrative access');
GO

-- -----------------------------------------------------------------------------
-- Roles
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM [auth].[Roles] WHERE [RoleCode] = 'SUPER_ADMIN')
INSERT INTO [auth].[Roles] ([RoleCode], [RoleName], [Description], [IsSystemRole])
VALUES
    ('SUPER_ADMIN', 'Super Administrator', 'Full system access with all permissions', 1),
    ('ADMIN',       'Administrator',       'Administrative access',                   1),
    ('USER',        'Standard User',       'Standard user with basic access',         1);
GO

-- -----------------------------------------------------------------------------
-- RolePermissions - Super Admin gets all permissions
-- -----------------------------------------------------------------------------
DECLARE @SuperAdminRoleId INT = (SELECT RoleId FROM [auth].[Roles] WHERE [RoleCode] = 'SUPER_ADMIN');

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT @SuperAdminRoleId, p.PermissionId
FROM [auth].[Permissions] p
WHERE NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @SuperAdminRoleId AND rp.PermissionId = p.PermissionId
);
GO

-- Admin gets most permissions except full admin
DECLARE @AdminRoleId INT = (SELECT RoleId FROM [auth].[Roles] WHERE [RoleCode] = 'ADMIN');

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT @AdminRoleId, p.PermissionId
FROM [auth].[Permissions] p
WHERE p.PermissionCode <> 'auth.admin.full'
AND NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @AdminRoleId AND rp.PermissionId = p.PermissionId
);
GO

-- Standard user gets profile permissions only
DECLARE @UserRoleId INT = (SELECT RoleId FROM [auth].[Roles] WHERE [RoleCode] = 'USER');

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT @UserRoleId, p.PermissionId
FROM [auth].[Permissions] p
WHERE p.PermissionCode IN ('auth.profile.view', 'auth.profile.update', 'auth.profile.change_password')
AND NOT EXISTS (
    SELECT 1 FROM [auth].[RolePermissions] rp
    WHERE rp.RoleId = @UserRoleId AND rp.PermissionId = p.PermissionId
);
GO

-- -----------------------------------------------------------------------------
-- Default Administrator User
-- Password: ChangeMe@2026!
-- BCrypt hash (12 rounds): $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYPKMKjKqKqK
-- NOTE: The application seed script will generate the correct hash at runtime.
-- This placeholder will be updated by the Python seed command.
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM [auth].[Users] WHERE [Username] = 'admin')
BEGIN
    INSERT INTO [auth].[Users] (
        [Username], [Email], [PasswordHash],
        [FirstName], [LastName],
        [MustChangePassword], [PasswordChangedDate], [PasswordExpiryDate],
        [IsEmailVerified], [IsActive]
    )
    VALUES (
        'admin',
        'admin@ahsteellab.com',
        '$2b$12$PLACEHOLDER_HASH_WILL_BE_SET_BY_APP_SEED',
        'System',
        'Administrator',
        1,
        NULL,
        DATEADD(DAY, 90, GETUTCDATE()),
        1,
        1
    );

    DECLARE @AdminUserId INT = SCOPE_IDENTITY();
    DECLARE @SuperAdminId INT = (SELECT RoleId FROM [auth].[Roles] WHERE [RoleCode] = 'SUPER_ADMIN');

    INSERT INTO [auth].[UserRoles] ([UserId], [RoleId], [CreatedBy])
    VALUES (@AdminUserId, @SuperAdminId, @AdminUserId);
END
GO

PRINT 'Seed data inserted successfully.';
PRINT 'IMPORTANT: Run the Python seed command to set the correct admin password hash.';
GO
