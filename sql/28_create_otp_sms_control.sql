-- OTP / SMS master control (single-row configuration).
-- Business DB: nsds2626.dbo.otp_sms_control
-- SQL Server 2008 compatible and safe to rerun.
USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.otp_sms_control', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.otp_sms_control (
        id INT NOT NULL,
        master_otp_enabled BIT NOT NULL
            CONSTRAINT DF_otp_sms_control_master DEFAULT (1),
        web_otp_enabled BIT NOT NULL
            CONSTRAINT DF_otp_sms_control_web DEFAULT (1),
        mobile_otp_enabled BIT NOT NULL
            CONSTRAINT DF_otp_sms_control_mobile DEFAULT (1),
        row_version INT NOT NULL
            CONSTRAINT DF_otp_sms_control_version DEFAULT (1),
        updated_by_user_id INT NULL,
        updated_by_username NVARCHAR(100) NULL,
        updated_at DATETIME2 NOT NULL
            CONSTRAINT DF_otp_sms_control_updated DEFAULT (SYSDATETIME()),
        comment NVARCHAR(300) NULL,
        CONSTRAINT PK_otp_sms_control PRIMARY KEY CLUSTERED (id),
        CONSTRAINT CK_otp_sms_control_id CHECK (id = 1)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.otp_sms_control WHERE id = 1)
BEGIN
    INSERT INTO dbo.otp_sms_control (
        id, master_otp_enabled, web_otp_enabled, mobile_otp_enabled, row_version
    )
    VALUES (1, 1, 1, 1, 1);
END;
GO
