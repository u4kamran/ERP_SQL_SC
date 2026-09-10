-- Customer App Cart tables (mobile shopping basket saved for store review).
-- NOT a sales invoice. Does NOT post stock or GL.
-- SQL Server 2008 compatible and safe to rerun.
-- Distinct from WhatsApp Bot WO-… orders (JSON guest chat).
USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.customer_app_cart_seq', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_app_cart_seq (
        day_key CHAR(8) NOT NULL,
        last_n INT NOT NULL
            CONSTRAINT DF_customer_app_cart_seq_last_n DEFAULT (0),
        CONSTRAINT PK_customer_app_cart_seq PRIMARY KEY CLUSTERED (day_key)
    );
END;
GO

IF OBJECT_ID(N'dbo.customer_app_carts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_app_carts (
        id INT IDENTITY(1,1) NOT NULL,
        cart_ref NVARCHAR(32) NOT NULL,
        cust_sms_id INT NOT NULL,
        customer_name NVARCHAR(150) NOT NULL,
        customer_mobile_no VARCHAR(30) NOT NULL,
        mobile_key VARCHAR(10) NOT NULL,
        customer_address NVARCHAR(250) NULL,
        status NVARCHAR(30) NOT NULL
            CONSTRAINT DF_customer_app_carts_status DEFAULT (N'SAVED'),
        source NVARCHAR(30) NOT NULL
            CONSTRAINT DF_customer_app_carts_source DEFAULT (N'MOBILE_APP'),
        total_items INT NOT NULL
            CONSTRAINT DF_customer_app_carts_total_items DEFAULT (0),
        estimated_subtotal MONEY NOT NULL
            CONSTRAINT DF_customer_app_carts_subtotal DEFAULT (0),
        estimated_discount MONEY NOT NULL
            CONSTRAINT DF_customer_app_carts_discount DEFAULT (0),
        estimated_tax MONEY NOT NULL
            CONSTRAINT DF_customer_app_carts_tax DEFAULT (0),
        estimated_total MONEY NOT NULL
            CONSTRAINT DF_customer_app_carts_total DEFAULT (0),
        idempotency_key NVARCHAR(64) NOT NULL,
        converted_doc_ref NVARCHAR(50) NULL,
        created_at DATETIME NOT NULL
            CONSTRAINT DF_customer_app_carts_created_at DEFAULT (GETDATE()),
        updated_at DATETIME NOT NULL
            CONSTRAINT DF_customer_app_carts_updated_at DEFAULT (GETDATE()),
        CONSTRAINT PK_customer_app_carts PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_customer_app_carts_cart_ref UNIQUE (cart_ref),
        CONSTRAINT UQ_customer_app_carts_idempotency UNIQUE (idempotency_key),
        CONSTRAINT CK_customer_app_carts_status CHECK (
            status IN (
                N'SAVED', N'UNDER_REVIEW', N'CONTACTED', N'CONFIRMED',
                N'CONVERTED', N'CANCELLED', N'EXPIRED'
            )
        ),
        CONSTRAINT CK_customer_app_carts_source CHECK (
            source IN (N'MOBILE_APP')
        ),
        CONSTRAINT CK_customer_app_carts_mobile CHECK (
            LEN(LTRIM(RTRIM(customer_mobile_no))) >= 10
            AND LEN(mobile_key) = 10
        )
    );
END;
GO

IF OBJECT_ID(N'dbo.customer_app_cart_lines', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_app_cart_lines (
        id INT IDENTITY(1,1) NOT NULL,
        cart_id INT NOT NULL,
        line_no INT NOT NULL,
        manual_id INT NOT NULL,
        item_title NVARCHAR(200) NOT NULL,
        barcode NVARCHAR(50) NULL,
        uom_title NVARCHAR(50) NULL,
        qty DECIMAL(18,3) NOT NULL,
        unit_price MONEY NOT NULL,
        discount_amount MONEY NOT NULL
            CONSTRAINT DF_customer_app_cart_lines_disc DEFAULT (0),
        tax_amount MONEY NOT NULL
            CONSTRAINT DF_customer_app_cart_lines_tax DEFAULT (0),
        line_total MONEY NOT NULL,
        CONSTRAINT PK_customer_app_cart_lines PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_customer_app_cart_lines_cart
            FOREIGN KEY (cart_id) REFERENCES dbo.customer_app_carts(id),
        CONSTRAINT UQ_customer_app_cart_lines_cart_line UNIQUE (cart_id, line_no),
        CONSTRAINT CK_customer_app_cart_lines_qty CHECK (qty > 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.customer_app_cart_status_history', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_app_cart_status_history (
        id INT IDENTITY(1,1) NOT NULL,
        cart_id INT NOT NULL,
        old_status NVARCHAR(30) NULL,
        new_status NVARCHAR(30) NOT NULL,
        action_code NVARCHAR(40) NOT NULL,
        actor_username NVARCHAR(100) NOT NULL,
        remarks NVARCHAR(1000) NULL,
        created_at DATETIME NOT NULL
            CONSTRAINT DF_customer_app_cart_hist_created DEFAULT (GETDATE()),
        CONSTRAINT PK_customer_app_cart_status_history PRIMARY KEY CLUSTERED (id),
        CONSTRAINT FK_customer_app_cart_hist_cart
            FOREIGN KEY (cart_id) REFERENCES dbo.customer_app_carts(id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customer_app_carts_mobile_created'
      AND object_id = OBJECT_ID(N'dbo.customer_app_carts')
)
    CREATE NONCLUSTERED INDEX IX_customer_app_carts_mobile_created
        ON dbo.customer_app_carts (mobile_key, created_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customer_app_carts_status_created'
      AND object_id = OBJECT_ID(N'dbo.customer_app_carts')
)
    CREATE NONCLUSTERED INDEX IX_customer_app_carts_status_created
        ON dbo.customer_app_carts (status, created_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customer_app_carts_cust_sms'
      AND object_id = OBJECT_ID(N'dbo.customer_app_carts')
)
    CREATE NONCLUSTERED INDEX IX_customer_app_carts_cust_sms
        ON dbo.customer_app_carts (cust_sms_id, created_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customer_app_cart_lines_cart'
      AND object_id = OBJECT_ID(N'dbo.customer_app_cart_lines')
)
    CREATE NONCLUSTERED INDEX IX_customer_app_cart_lines_cart
        ON dbo.customer_app_cart_lines (cart_id);
GO
