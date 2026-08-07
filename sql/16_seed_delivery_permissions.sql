-- Seed delivery module and permissions in the authentication database.
USE [NSDS2626_AUTH];
GO

SET NOCOUNT ON;

IF NOT EXISTS (
    SELECT 1 FROM [auth].[Modules] WHERE [ModuleCode] = N'DELIVERY'
)
BEGIN
    INSERT INTO [auth].[Modules] (
        [ModuleCode], [ModuleName], [Description], [DisplayOrder], [IconClass]
    )
    VALUES (
        N'DELIVERY', N'Delivery Management',
        N'Delivery order, rider, and status management',
        13, N'bi-truck'
    );
END;

DECLARE @DeliveryModuleId INT;
SELECT @DeliveryModuleId = [ModuleId]
FROM [auth].[Modules]
WHERE [ModuleCode] = N'DELIVERY';

IF @DeliveryModuleId IS NOT NULL
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM [auth].[Permissions]
        WHERE [PermissionCode] = N'delivery.orders.view'
    )
        INSERT INTO [auth].[Permissions] (
            [ModuleId], [PermissionCode], [PermissionName], [Description]
        )
        VALUES (
            @DeliveryModuleId, N'delivery.orders.view',
            N'View Delivery Orders', N'View delivery orders, summary, and riders'
        );

    IF NOT EXISTS (
        SELECT 1 FROM [auth].[Permissions]
        WHERE [PermissionCode] = N'delivery.orders.sync'
    )
        INSERT INTO [auth].[Permissions] (
            [ModuleId], [PermissionCode], [PermissionName], [Description]
        )
        VALUES (
            @DeliveryModuleId, N'delivery.orders.sync',
            N'Sync Delivery Orders', N'Import recent delivery orders from invoices'
        );

    IF NOT EXISTS (
        SELECT 1 FROM [auth].[Permissions]
        WHERE [PermissionCode] = N'delivery.orders.assign'
    )
        INSERT INTO [auth].[Permissions] (
            [ModuleId], [PermissionCode], [PermissionName], [Description]
        )
        VALUES (
            @DeliveryModuleId, N'delivery.orders.assign',
            N'Assign Delivery Orders', N'Assign delivery orders to active riders'
        );

    IF NOT EXISTS (
        SELECT 1 FROM [auth].[Permissions]
        WHERE [PermissionCode] = N'delivery.orders.update'
    )
        INSERT INTO [auth].[Permissions] (
            [ModuleId], [PermissionCode], [PermissionName], [Description]
        )
        VALUES (
            @DeliveryModuleId, N'delivery.orders.update',
            N'Update Delivery Status', N'Update delivery order status and proof of delivery'
        );

    IF NOT EXISTS (
        SELECT 1 FROM [auth].[Permissions]
        WHERE [PermissionCode] = N'delivery.riders.manage'
    )
        INSERT INTO [auth].[Permissions] (
            [ModuleId], [PermissionCode], [PermissionName], [Description]
        )
        VALUES (
            @DeliveryModuleId, N'delivery.riders.manage',
            N'Manage Delivery Riders', N'Create and manage delivery riders'
        );
END;
GO

INSERT INTO [auth].[RolePermissions] ([RoleId], [PermissionId])
SELECT r.[RoleId], p.[PermissionId]
FROM [auth].[Roles] r
CROSS JOIN [auth].[Permissions] p
WHERE r.[RoleCode] IN (N'SUPER_ADMIN', N'ADMIN')
  AND p.[PermissionCode] IN (
      N'delivery.orders.view',
      N'delivery.orders.sync',
      N'delivery.orders.assign',
      N'delivery.orders.update',
      N'delivery.riders.manage'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM [auth].[RolePermissions] rp
      WHERE rp.[RoleId] = r.[RoleId]
        AND rp.[PermissionId] = p.[PermissionId]
  );
GO
