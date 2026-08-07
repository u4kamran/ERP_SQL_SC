-- Delivery-management tables for the nsds2626 business database.
-- SQL Server 2008 compatible and safe to rerun.
-- This script does not alter the legacy FIN_INV_M or CUST_SMS table structures.
USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.delivery_riders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.delivery_riders (
        id INT IDENTITY(1,1) NOT NULL,
        name NVARCHAR(100) NOT NULL,
        phone VARCHAR(30) NULL,
        is_active BIT NOT NULL
            CONSTRAINT DF_delivery_riders_is_active DEFAULT (1),
        created_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_riders_created_at DEFAULT (GETDATE()),
        updated_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_riders_updated_at DEFAULT (GETDATE()),
        CONSTRAINT PK_delivery_riders PRIMARY KEY CLUSTERED (id),
        CONSTRAINT CK_delivery_riders_name
            CHECK (LEN(LTRIM(RTRIM(name))) > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.delivery_orders', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.delivery_orders (
        id INT IDENTITY(1,1) NOT NULL,
        source_serial_no INT NOT NULL,
        invoice_id INT NULL,
        invoice_date DATETIME NULL,
        customer_id INT NULL,
        cust_sms_id INT NULL,
        customer_title NVARCHAR(100) NOT NULL,
        customer_mobile_no VARCHAR(30) NOT NULL,
        customer_alternate_mobile VARCHAR(30) NULL,
        address NVARCHAR(250) NOT NULL,
        city_id SMALLINT NULL,
        sale_amount MONEY NULL,
        balance_amount MONEY NULL,
        total_amount MONEY NULL,
        payment_type SMALLINT NULL,
        rider_id INT NULL,
        status NVARCHAR(30) NOT NULL
            CONSTRAINT DF_delivery_orders_status DEFAULT (N'Pending'),
        created_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_orders_created_at DEFAULT (GETDATE()),
        updated_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_orders_updated_at DEFAULT (GETDATE()),
        delivered_at DATETIME NULL,
        delivered_latitude DECIMAL(10,7) NULL,
        delivered_longitude DECIMAL(10,7) NULL,
        delivered_accuracy DECIMAL(10,2) NULL,
        remarks NVARCHAR(1000) NULL,
        CONSTRAINT PK_delivery_orders PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_delivery_orders_source_serial_no UNIQUE (source_serial_no),
        CONSTRAINT FK_delivery_orders_rider
            FOREIGN KEY (rider_id) REFERENCES dbo.delivery_riders(id),
        CONSTRAINT CK_delivery_orders_customer_mobile CHECK (
            LEN(LTRIM(RTRIM(customer_mobile_no))) > 0
            AND LTRIM(RTRIM(customer_mobile_no)) <> N'.'
        ),
        CONSTRAINT CK_delivery_orders_status CHECK (
            status IN (
                N'Pending', N'Assigned', N'On The Way', N'Arrived',
                N'Delivered', N'Cancelled', N'Failed Delivery', N'Returned'
            )
        ),
        CONSTRAINT CK_delivery_orders_delivery_coordinates CHECK (
            (delivered_latitude IS NULL OR
                delivered_latitude BETWEEN -90 AND 90)
            AND
            (delivered_longitude IS NULL OR
                delivered_longitude BETWEEN -180 AND 180)
            AND
            (delivered_accuracy IS NULL OR delivered_accuracy >= 0)
        )
    );
END;
GO

IF COL_LENGTH(N'dbo.delivery_orders', N'cust_sms_id') IS NULL
    ALTER TABLE dbo.delivery_orders ADD cust_sms_id INT NULL;
GO

IF COL_LENGTH(N'dbo.delivery_orders', N'customer_alternate_mobile') IS NULL
    ALTER TABLE dbo.delivery_orders ADD customer_alternate_mobile VARCHAR(30) NULL;
GO

-- Individual rider delivery still requires GPS in the API. This database
-- constraint is removed so authorized admins can perform explicit bulk delivery.
IF EXISTS (
    SELECT 1
    FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.delivery_orders')
      AND name = N'CK_delivery_orders_delivered_location'
)
    ALTER TABLE dbo.delivery_orders
        DROP CONSTRAINT CK_delivery_orders_delivered_location;
GO

IF OBJECT_ID(N'dbo.delivery_status_history', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.delivery_status_history (
        id INT IDENTITY(1,1) NOT NULL,
        order_id INT NOT NULL,
        old_status NVARCHAR(30) NULL,
        new_status NVARCHAR(30) NOT NULL,
        actor_username NVARCHAR(100) NOT NULL,
        remarks NVARCHAR(1000) NULL,
        created_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_history_created_at DEFAULT (GETDATE()),
        CONSTRAINT PK_delivery_status_history PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_delivery_history_order
            FOREIGN KEY (order_id) REFERENCES dbo.delivery_orders(id),
        CONSTRAINT CK_delivery_history_old_status CHECK (
            old_status IS NULL OR old_status IN (
                N'Pending', N'Assigned', N'On The Way', N'Arrived',
                N'Delivered', N'Cancelled', N'Failed Delivery', N'Returned'
            )
        ),
        CONSTRAINT CK_delivery_history_new_status CHECK (
            new_status IN (
                N'Pending', N'Assigned', N'On The Way', N'Arrived',
                N'Delivered', N'Cancelled', N'Failed Delivery', N'Returned'
            )
        )
    );
END;
GO

IF OBJECT_ID(N'dbo.delivery_customer_locations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.delivery_customer_locations (
        id INT IDENTITY(1,1) NOT NULL,
        mobile_key VARCHAR(20) NOT NULL,
        customer_mobile_no VARCHAR(30) NOT NULL,
        cust_sms_id INT NULL,
        latitude DECIMAL(10,7) NOT NULL,
        longitude DECIMAL(10,7) NOT NULL,
        accuracy DECIMAL(10,2) NULL,
        updated_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_customer_location_updated DEFAULT (GETDATE()),
        updated_by NVARCHAR(100) NOT NULL,
        CONSTRAINT PK_delivery_customer_locations PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_delivery_customer_locations_mobile UNIQUE (mobile_key),
        CONSTRAINT CK_delivery_customer_location_coordinates CHECK (
            latitude BETWEEN -90 AND 90
            AND longitude BETWEEN -180 AND 180
            AND (accuracy IS NULL OR accuracy >= 0)
        )
    );
END;
GO

IF OBJECT_ID(N'dbo.delivery_rider_locations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.delivery_rider_locations (
        rider_id INT NOT NULL,
        latitude DECIMAL(10,7) NOT NULL,
        longitude DECIMAL(10,7) NOT NULL,
        accuracy DECIMAL(10,2) NULL,
        source_order_id INT NULL,
        recorded_at DATETIME NOT NULL
            CONSTRAINT DF_delivery_rider_location_recorded DEFAULT (GETDATE()),
        updated_by NVARCHAR(100) NOT NULL,
        CONSTRAINT PK_delivery_rider_locations PRIMARY KEY CLUSTERED (rider_id),
        CONSTRAINT FK_delivery_rider_location_rider
            FOREIGN KEY (rider_id) REFERENCES dbo.delivery_riders(id),
        CONSTRAINT FK_delivery_rider_location_order
            FOREIGN KEY (source_order_id) REFERENCES dbo.delivery_orders(id),
        CONSTRAINT CK_delivery_rider_location_coordinates CHECK (
            latitude BETWEEN -90 AND 90
            AND longitude BETWEEN -180 AND 180
            AND (accuracy IS NULL OR accuracy >= 0)
        )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID(N'dbo.delivery_orders')
      AND name = N'CK_delivery_orders_customer_mobile'
)
BEGIN
    -- Existing proof-of-concept rows may contain legacy "." placeholders.
    -- Keep them for auditability, but enforce the rule for every future write.
    ALTER TABLE dbo.delivery_orders WITH NOCHECK
        ADD CONSTRAINT CK_delivery_orders_customer_mobile CHECK (
            LEN(LTRIM(RTRIM(customer_mobile_no))) > 0
            AND LTRIM(RTRIM(customer_mobile_no)) <> N'.'
        );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.delivery_orders')
      AND name = N'IX_delivery_orders_status_created'
)
    CREATE NONCLUSTERED INDEX IX_delivery_orders_status_created
        ON dbo.delivery_orders (status, created_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.delivery_orders')
      AND name = N'IX_delivery_orders_rider_status'
)
    CREATE NONCLUSTERED INDEX IX_delivery_orders_rider_status
        ON dbo.delivery_orders (rider_id, status);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.delivery_orders')
      AND name = N'IX_delivery_orders_invoice_date'
)
    CREATE NONCLUSTERED INDEX IX_delivery_orders_invoice_date
        ON dbo.delivery_orders (invoice_date DESC, id DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'dbo.delivery_status_history')
      AND name = N'IX_delivery_history_order_created'
)
    CREATE NONCLUSTERED INDEX IX_delivery_history_order_created
        ON dbo.delivery_status_history (order_id, created_at DESC, id DESC);
GO

PRINT N'Delivery tables initialized successfully in database nsds2626.';
GO
