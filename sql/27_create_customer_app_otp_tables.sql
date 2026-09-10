-- Customer App OTP verification table (hash only — never stores plain OTP).
-- SMS delivery uses existing dbo.SMS_DB_ queue (STATUS=1 = pending).
-- SQL Server 2008 compatible and safe to rerun.
USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.customer_app_otp', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.customer_app_otp (
        id INT IDENTITY(1,1) NOT NULL,
        request_id NVARCHAR(64) NOT NULL,
        mobile_key VARCHAR(10) NOT NULL,
        mobile_display VARCHAR(20) NOT NULL,
        otp_hash CHAR(64) NOT NULL,
        salt VARCHAR(32) NOT NULL,
        created_at DATETIME2 NOT NULL
            CONSTRAINT DF_customer_app_otp_created DEFAULT (SYSDATETIME()),
        expires_at DATETIME2 NOT NULL,
        attempt_count INT NOT NULL
            CONSTRAINT DF_customer_app_otp_attempts DEFAULT (0),
        max_attempts INT NOT NULL
            CONSTRAINT DF_customer_app_otp_max_attempts DEFAULT (5),
        status NVARCHAR(20) NOT NULL
            CONSTRAINT DF_customer_app_otp_status DEFAULT (N'PENDING'),
        sms_db_id INT NULL,
        verified_at DATETIME2 NULL,
        verified_until DATETIME2 NULL,
        client_ip NVARCHAR(64) NULL,
        CONSTRAINT PK_customer_app_otp PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_customer_app_otp_request_id UNIQUE (request_id),
        CONSTRAINT CK_customer_app_otp_status CHECK (
            status IN (N'PENDING', N'VERIFIED', N'EXPIRED', N'BLOCKED', N'SUPERSEDED')
        ),
        CONSTRAINT CK_customer_app_otp_mobile_key CHECK (LEN(mobile_key) = 10)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customer_app_otp_mobile_created'
      AND object_id = OBJECT_ID(N'dbo.customer_app_otp')
)
    CREATE NONCLUSTERED INDEX IX_customer_app_otp_mobile_created
        ON dbo.customer_app_otp (mobile_key, created_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_customer_app_otp_mobile_status'
      AND object_id = OBJECT_ID(N'dbo.customer_app_otp')
)
    CREATE NONCLUSTERED INDEX IX_customer_app_otp_mobile_status
        ON dbo.customer_app_otp (mobile_key, status, verified_until);
GO
