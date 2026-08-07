-- Allow authorized admin bulk-delivery actions without GPS.
-- Individual Delivered updates continue to require GPS in the FastAPI service.

USE [nsds2626];
GO

SET NOCOUNT ON;
GO

IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.delivery_orders')
      AND name = N'CK_delivery_orders_delivered_location'
)
BEGIN
    ALTER TABLE dbo.delivery_orders
        DROP CONSTRAINT CK_delivery_orders_delivered_location;
END;
GO

PRINT N'Admin bulk delivery without GPS is enabled.';
GO
