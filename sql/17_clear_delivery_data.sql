-- Delete all operational data from the delivery module.
-- This script does NOT delete or modify FIN_INV_M or CUST_SMS records.
-- Set @ConfirmDelete to 1 only when you intentionally want to clear the data.

USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

DECLARE @ConfirmDelete BIT;
SET @ConfirmDelete = 0;

IF @ConfirmDelete <> 1
BEGIN
    RAISERROR(
        'Delivery data was NOT deleted. Set @ConfirmDelete = 1 and run again.',
        16,
        1
    );
    RETURN;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Delete children before their parent records.
    DELETE FROM dbo.delivery_rider_locations;
    DELETE FROM dbo.delivery_customer_locations;
    DELETE FROM dbo.delivery_status_history;
    DELETE FROM dbo.delivery_orders;
    DELETE FROM dbo.delivery_riders;

    -- Reset identity values so the next inserted record starts at 1.
    DBCC CHECKIDENT (N'dbo.delivery_status_history', RESEED, 0)
        WITH NO_INFOMSGS;
    DBCC CHECKIDENT (N'dbo.delivery_customer_locations', RESEED, 0)
        WITH NO_INFOMSGS;
    DBCC CHECKIDENT (N'dbo.delivery_orders', RESEED, 0)
        WITH NO_INFOMSGS;
    DBCC CHECKIDENT (N'dbo.delivery_riders', RESEED, 0)
        WITH NO_INFOMSGS;

    COMMIT TRANSACTION;
    PRINT N'All delivery-module data was deleted successfully.';
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrorMessage NVARCHAR(4000);
    SET @ErrorMessage = ERROR_MESSAGE();
    RAISERROR(@ErrorMessage, 16, 1);
END CATCH;
GO
