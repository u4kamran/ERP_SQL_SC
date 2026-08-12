-- =============================================================================
-- Enterprise Cheque Printing Module — Tables, Indexes, Relationships
-- Target: SQL Server 2008+ (ERP business database)
-- Design unit: millimetres. No hard-coded print coordinates in application code.
-- =============================================================================

SET NOCOUNT ON;
GO

-- -----------------------------------------------------------------------------
-- BANK_MASTER
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[BANK_MASTER]') AND type = 'U')
CREATE TABLE [dbo].[BANK_MASTER] (
    [BankID]            INT IDENTITY(1,1) NOT NULL,
    [CompanyID]         INT           NOT NULL CONSTRAINT [DF_BANK_MASTER_CompanyID] DEFAULT (1),
    [BankCode]          NVARCHAR(30)  NOT NULL,
    [BankName]          NVARCHAR(150) NOT NULL,
    [Branch]            NVARCHAR(150) NULL,
    [BranchAddress]     NVARCHAR(500) NULL,
    [DefaultPrinter]    NVARCHAR(255) NULL,
    [PaperSize]         NVARCHAR(30)  NOT NULL CONSTRAINT [DF_BANK_MASTER_PaperSize] DEFAULT (N'Custom'),
    [Active]            BIT           NOT NULL CONSTRAINT [DF_BANK_MASTER_Active] DEFAULT (1),
    [Remarks]           NVARCHAR(500) NULL,
    [CreatedBy]         NVARCHAR(50)  NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_BANK_MASTER_CreatedDate] DEFAULT (GETDATE()),
    [ModifiedBy]        NVARCHAR(50)  NULL,
    [ModifiedDate]      DATETIME      NULL,
    CONSTRAINT [PK_BANK_MASTER] PRIMARY KEY CLUSTERED ([BankID]),
    CONSTRAINT [UQ_BANK_MASTER_Code] UNIQUE ([CompanyID], [BankCode])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_LAYOUT_MASTER — one record per cheque design
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_LAYOUT_MASTER]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_LAYOUT_MASTER] (
    [LayoutID]          INT IDENTITY(1,1) NOT NULL,
    [BankID]            INT           NOT NULL,
    [CompanyID]         INT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_CompanyID] DEFAULT (1),
    [LayoutName]        NVARCHAR(150) NOT NULL,
    [ChequeWidth]       DECIMAL(10,3) NOT NULL,   -- mm
    [ChequeHeight]      DECIMAL(10,3) NOT NULL,   -- mm
    [TopMargin]         DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_LAY_M_TopMargin] DEFAULT (0),
    [LeftMargin]        DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_LAY_M_LeftMargin] DEFAULT (0),
    [PrinterDPI]        INT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_DPI] DEFAULT (300),
    [PaperOrientation]  TINYINT       NOT NULL CONSTRAINT [DF_CHQ_LAY_M_Orient] DEFAULT (1), -- 1=Portrait 2=Landscape
    [PaperSizeName]     NVARCHAR(30)  NULL,       -- A4 / Letter / Legal / Custom
    [DateFormatCode]    NVARCHAR(30)  NOT NULL CONSTRAINT [DF_CHQ_LAY_M_DateFmt] DEFAULT (N'DD-MMM-YYYY'),
    [AmountFormatCode]  NVARCHAR(30)  NOT NULL CONSTRAINT [DF_CHQ_LAY_M_AmtFmt] DEFAULT (N'#,##0.00'),
    [CurrencyPrefix]    NVARCHAR(10)  NULL,
    [ShowCurrencyPrefix] BIT          NOT NULL CONSTRAINT [DF_CHQ_LAY_M_CurPref] DEFAULT (0),
    [PayeeCaseMode]     TINYINT       NOT NULL CONSTRAINT [DF_CHQ_LAY_M_PayeeCase] DEFAULT (1), -- 1=Original 2=Upper 3=Proper
    [PayeeMaxLength]    INT           NULL,
    [PayeeWrap]         BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_PayeeWrap] DEFAULT (0),
    [PayeeAutoShrink]   BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_PayeeShrink] DEFAULT (1),
    [AutoCenter]        BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_AutoCenter] DEFAULT (0),
    [BackgroundImage]   NVARCHAR(260) NULL,
    [Active]            BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_Active] DEFAULT (1),
    [IsDefault]         BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_M_IsDefault] DEFAULT (0),
    [Remarks]           NVARCHAR(500) NULL,
    [CreatedBy]         NVARCHAR(50)  NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_CHQ_LAY_M_Created] DEFAULT (GETDATE()),
    [ModifiedBy]        NVARCHAR(50)  NULL,
    [ModifiedDate]      DATETIME      NULL,
    CONSTRAINT [PK_CHEQUE_LAYOUT_MASTER] PRIMARY KEY CLUSTERED ([LayoutID]),
    CONSTRAINT [FK_CHQ_LAY_M_BANK] FOREIGN KEY ([BankID]) REFERENCES [dbo].[BANK_MASTER]([BankID]),
    CONSTRAINT [UQ_CHQ_LAY_M_Name] UNIQUE ([CompanyID], [BankID], [LayoutName])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_LAYOUT_DETAIL — every printable object (no hard-coded coords)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_LAYOUT_DETAIL]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_LAYOUT_DETAIL] (
    [DetailID]          INT IDENTITY(1,1) NOT NULL,
    [LayoutID]          INT           NOT NULL,
    [ObjectName]        NVARCHAR(80)  NOT NULL,
    [ObjectCode]        NVARCHAR(40)  NOT NULL,   -- PAYEE_NAME, AMOUNT, ...
    [XPos]              DECIMAL(10,3) NOT NULL,   -- mm
    [YPos]              DECIMAL(10,3) NOT NULL,   -- mm
    [Width]             DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_LAY_D_W] DEFAULT (40),
    [Height]            DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_LAY_D_H] DEFAULT (6),
    [FontName]          NVARCHAR(80)  NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Font] DEFAULT (N'Arial'),
    [FontSize]          DECIMAL(6,2)  NOT NULL CONSTRAINT [DF_CHQ_LAY_D_FSize] DEFAULT (10),
    [Bold]              BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Bold] DEFAULT (0),
    [Italic]            BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Italic] DEFAULT (0),
    [Alignment]         TINYINT       NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Align] DEFAULT (0), -- 0=Left 1=Center 2=Right
    [Visible]           BIT           NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Vis] DEFAULT (1),
    [Rotation]          SMALLINT      NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Rot] DEFAULT (0), -- degrees
    [PrintOrder]        INT           NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Ord] DEFAULT (100),
    [DefaultText]       NVARCHAR(255) NULL,       -- for CUSTOM_TEXT / AC_PAYEE / BEARER
    [ForeColor]         INT           NULL,       -- OLE color (optional)
    [LineStyle]         TINYINT       NULL,       -- for CROSS_MARK etc.
    [DataField]         NVARCHAR(80)  NULL,       -- optional override field map
    [MinFontSize]       DECIMAL(6,2)  NULL,       -- auto-shrink floor
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_CHQ_LAY_D_Created] DEFAULT (GETDATE()),
    [ModifiedDate]      DATETIME      NULL,
    CONSTRAINT [PK_CHEQUE_LAYOUT_DETAIL] PRIMARY KEY CLUSTERED ([DetailID]),
    CONSTRAINT [FK_CHQ_LAY_D_M] FOREIGN KEY ([LayoutID]) REFERENCES [dbo].[CHEQUE_LAYOUT_MASTER]([LayoutID]) ON DELETE CASCADE,
    CONSTRAINT [UQ_CHQ_LAY_D_Obj] UNIQUE ([LayoutID], [ObjectName])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_BOOK — cheque stock / sequencing per bank account
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_BOOK]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_BOOK] (
    [ChequeBookID]      INT IDENTITY(1,1) NOT NULL,
    [CompanyID]         INT           NOT NULL CONSTRAINT [DF_CHQ_BOOK_Co] DEFAULT (1),
    [BankID]            INT           NOT NULL,
    [BankAccountID]     INT           NULL,       -- GL account / fin bank account id
    [BankAccountNo]     NVARCHAR(50)  NULL,
    [BookName]          NVARCHAR(100) NOT NULL,
    [LayoutID]          INT           NULL,
    [StartChequeNo]     NVARCHAR(30)  NOT NULL,
    [EndChequeNo]       NVARCHAR(30)  NOT NULL,
    [NextChequeNo]      NVARCHAR(30)  NOT NULL,
    [Prefix]            NVARCHAR(20)  NULL,
    [Suffix]            NVARCHAR(20)  NULL,
    [Active]            BIT           NOT NULL CONSTRAINT [DF_CHQ_BOOK_Active] DEFAULT (1),
    [Remarks]           NVARCHAR(500) NULL,
    CONSTRAINT [PK_CHEQUE_BOOK] PRIMARY KEY CLUSTERED ([ChequeBookID]),
    CONSTRAINT [FK_CHQ_BOOK_BANK] FOREIGN KEY ([BankID]) REFERENCES [dbo].[BANK_MASTER]([BankID]),
    CONSTRAINT [FK_CHQ_BOOK_LAYOUT] FOREIGN KEY ([LayoutID]) REFERENCES [dbo].[CHEQUE_LAYOUT_MASTER]([LayoutID])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_PRINT_REGISTER — one logical cheque per voucher/cheque#
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_REGISTER]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_PRINT_REGISTER] (
    [RegisterID]        BIGINT IDENTITY(1,1) NOT NULL,
    [CompanyID]         INT           NOT NULL CONSTRAINT [DF_CHQ_REG_Co] DEFAULT (1),
    [BranchID]          INT           NULL,
    [VoucherNo]         NVARCHAR(40)  NOT NULL,
    [VoucherDate]       DATETIME      NULL,
    [VoucherSerial]     INT           NULL,
    [DocTypeID]         INT           NULL,
    [Fiscal]            SMALLINT      NULL,
    [PartyID]           INT           NULL,
    [PayeeName]         NVARCHAR(255) NOT NULL,
    [Amount]            DECIMAL(18,4) NOT NULL,
    [CurrencyCode]      NVARCHAR(10)  NOT NULL CONSTRAINT [DF_CHQ_REG_Cur] DEFAULT (N'PKR'),
    [AmountInWords]     NVARCHAR(500) NULL,
    [Narration]         NVARCHAR(500) NULL,
    [BankID]            INT           NULL,
    [BankAccount]       NVARCHAR(80)  NULL,
    [ChequeNo]          NVARCHAR(40)  NOT NULL,
    [ChequeDate]        DATETIME      NOT NULL,
    [LayoutID]          INT           NULL,
    [ChequeBookID]      INT           NULL,
    [StatusCode]        NVARCHAR(20)  NOT NULL CONSTRAINT [DF_CHQ_REG_Status] DEFAULT (N'Draft'),
    -- Draft | Printed | Reprinted | Cancelled | Voided | Cleared | Bounced
    [PrintCount]        INT           NOT NULL CONSTRAINT [DF_CHQ_REG_PrintCnt] DEFAULT (0),
    [LastPrintedBy]     NVARCHAR(50)  NULL,
    [LastPrintedDate]   DATETIME      NULL,
    [LastPrinterName]   NVARCHAR(255) NULL,
    [LastComputerName]  NVARCHAR(100) NULL,
    [CreatedBy]         NVARCHAR(50)  NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_CHQ_REG_Created] DEFAULT (GETDATE()),
    [ModifiedBy]        NVARCHAR(50)  NULL,
    [ModifiedDate]      DATETIME      NULL,
    [RowVersion]        ROWVERSION    NOT NULL,
    CONSTRAINT [PK_CHEQUE_PRINT_REGISTER] PRIMARY KEY CLUSTERED ([RegisterID]),
    CONSTRAINT [FK_CHQ_REG_BANK] FOREIGN KEY ([BankID]) REFERENCES [dbo].[BANK_MASTER]([BankID]),
    CONSTRAINT [FK_CHQ_REG_LAYOUT] FOREIGN KEY ([LayoutID]) REFERENCES [dbo].[CHEQUE_LAYOUT_MASTER]([LayoutID]),
    CONSTRAINT [FK_CHQ_REG_BOOK] FOREIGN KEY ([ChequeBookID]) REFERENCES [dbo].[CHEQUE_BOOK]([ChequeBookID]),
    CONSTRAINT [UQ_CHQ_REG_Cheque] UNIQUE ([CompanyID], [BankID], [ChequeNo])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_PRINT_AUDIT — every print / reprint / cancel / preview export
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_AUDIT]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_PRINT_AUDIT] (
    [AuditID]           BIGINT IDENTITY(1,1) NOT NULL,
    [RegisterID]        BIGINT        NULL,
    [ActionCode]        NVARCHAR(30)  NOT NULL,  -- PRINT, REPRINT, CANCEL, VOID, PREVIEW, EXPORT_PDF, EXPORT_IMG
    [VoucherNo]         NVARCHAR(40)  NULL,
    [ChequeNo]          NVARCHAR(40)  NULL,
    [LayoutID]          INT           NULL,
    [PrintedBy]         NVARCHAR(50)  NOT NULL,
    [PrintedDate]       DATETIME      NOT NULL CONSTRAINT [DF_CHQ_AUD_Date] DEFAULT (GETDATE()),
    [PrintedTime]       NVARCHAR(20)  NULL,
    [PrinterName]       NVARCHAR(255) NULL,
    [ComputerName]      NVARCHAR(100) NULL,
    [Copies]            INT           NOT NULL CONSTRAINT [DF_CHQ_AUD_Copies] DEFAULT (1),
    [Remarks]           NVARCHAR(500) NULL,
    [IsReprint]         BIT           NOT NULL CONSTRAINT [DF_CHQ_AUD_IsRep] DEFAULT (0),
    CONSTRAINT [PK_CHEQUE_PRINT_AUDIT] PRIMARY KEY CLUSTERED ([AuditID]),
    CONSTRAINT [FK_CHQ_AUD_REG] FOREIGN KEY ([RegisterID]) REFERENCES [dbo].[CHEQUE_PRINT_REGISTER]([RegisterID])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_PRINTER_CALIBRATION — per user / printer offsets (mm)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINTER_CALIBRATION]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_PRINTER_CALIBRATION] (
    [CalibrationID]     INT IDENTITY(1,1) NOT NULL,
    [CompanyID]         INT           NOT NULL CONSTRAINT [DF_CHQ_CAL_Co] DEFAULT (1),
    [UserID]            NVARCHAR(50)  NOT NULL,
    [PrinterName]       NVARCHAR(255) NOT NULL,
    [BankID]            INT           NULL,
    [LayoutID]          INT           NULL,
    [OffsetLeft]        DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_CAL_OL] DEFAULT (0),
    [OffsetRight]       DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_CAL_OR] DEFAULT (0),
    [OffsetTop]         DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_CAL_OT] DEFAULT (0),
    [OffsetBottom]      DECIMAL(10,3) NOT NULL CONSTRAINT [DF_CHQ_CAL_OB] DEFAULT (0),
    [ModifiedDate]      DATETIME      NOT NULL CONSTRAINT [DF_CHQ_CAL_Mod] DEFAULT (GETDATE()),
    CONSTRAINT [PK_CHEQUE_PRINTER_CALIBRATION] PRIMARY KEY CLUSTERED ([CalibrationID]),
    CONSTRAINT [UQ_CHQ_CAL] UNIQUE ([CompanyID], [UserID], [PrinterName], [LayoutID])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_USER_PREFERENCE — last printer / layout choice
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_USER_PREFERENCE]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_USER_PREFERENCE] (
    [PrefID]            INT IDENTITY(1,1) NOT NULL,
    [CompanyID]         INT           NOT NULL CONSTRAINT [DF_CHQ_PREF_Co] DEFAULT (1),
    [UserID]            NVARCHAR(50)  NOT NULL,
    [PrefKey]           NVARCHAR(50)  NOT NULL,  -- LAST_PRINTER, PRINTER_MODE, LAST_LAYOUT
    [PrefValue]         NVARCHAR(255) NOT NULL,
    [ModifiedDate]      DATETIME      NOT NULL CONSTRAINT [DF_CHQ_PREF_Mod] DEFAULT (GETDATE()),
    CONSTRAINT [PK_CHEQUE_USER_PREFERENCE] PRIMARY KEY CLUSTERED ([PrefID]),
    CONSTRAINT [UQ_CHQ_PREF] UNIQUE ([CompanyID], [UserID], [PrefKey])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_PERMISSION (VB6 / ERP local rights — complements auth DB)
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_PERMISSION]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_PERMISSION] (
    [PermID]            INT IDENTITY(1,1) NOT NULL,
    [UserID]            NVARCHAR(50)  NOT NULL,
    [PermissionCode]    NVARCHAR(50)  NOT NULL,
    [Allowed]           BIT           NOT NULL CONSTRAINT [DF_CHQ_PERM_Allow] DEFAULT (1),
    CONSTRAINT [PK_CHEQUE_PERMISSION] PRIMARY KEY CLUSTERED ([PermID]),
    CONSTRAINT [UQ_CHQ_PERM] UNIQUE ([UserID], [PermissionCode])
);
GO

-- -----------------------------------------------------------------------------
-- CHEQUE_POSITIVE_PAY_QUEUE — future Positive Pay file generation
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[CHEQUE_POSITIVE_PAY_QUEUE]') AND type = 'U')
CREATE TABLE [dbo].[CHEQUE_POSITIVE_PAY_QUEUE] (
    [QueueID]           BIGINT IDENTITY(1,1) NOT NULL,
    [RegisterID]        BIGINT        NOT NULL,
    [BankID]            INT           NOT NULL,
    [ExportStatus]      NVARCHAR(20)  NOT NULL CONSTRAINT [DF_CHQ_PP_Status] DEFAULT (N'Pending'),
    [ExportFileName]    NVARCHAR(260) NULL,
    [ExportedDate]      DATETIME      NULL,
    [CreatedDate]       DATETIME      NOT NULL CONSTRAINT [DF_CHQ_PP_Created] DEFAULT (GETDATE()),
    CONSTRAINT [PK_CHEQUE_POSITIVE_PAY_QUEUE] PRIMARY KEY CLUSTERED ([QueueID]),
    CONSTRAINT [FK_CHQ_PP_REG] FOREIGN KEY ([RegisterID]) REFERENCES [dbo].[CHEQUE_PRINT_REGISTER]([RegisterID])
);
GO

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_CHQ_LAY_D_Layout' AND object_id = OBJECT_ID(N'[dbo].[CHEQUE_LAYOUT_DETAIL]'))
    CREATE NONCLUSTERED INDEX [IX_CHQ_LAY_D_Layout]
        ON [dbo].[CHEQUE_LAYOUT_DETAIL]([LayoutID], [PrintOrder], [Visible]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_CHQ_REG_Voucher' AND object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_REGISTER]'))
    CREATE NONCLUSTERED INDEX [IX_CHQ_REG_Voucher]
        ON [dbo].[CHEQUE_PRINT_REGISTER]([CompanyID], [VoucherNo], [StatusCode]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_CHQ_REG_PayeeDate' AND object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_REGISTER]'))
    CREATE NONCLUSTERED INDEX [IX_CHQ_REG_PayeeDate]
        ON [dbo].[CHEQUE_PRINT_REGISTER]([PayeeName], [ChequeDate], [Amount]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_CHQ_REG_Status' AND object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_REGISTER]'))
    CREATE NONCLUSTERED INDEX [IX_CHQ_REG_Status]
        ON [dbo].[CHEQUE_PRINT_REGISTER]([StatusCode], [LastPrintedDate]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_CHQ_AUD_Register' AND object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_AUDIT]'))
    CREATE NONCLUSTERED INDEX [IX_CHQ_AUD_Register]
        ON [dbo].[CHEQUE_PRINT_AUDIT]([RegisterID], [PrintedDate]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_CHQ_AUD_Action' AND object_id = OBJECT_ID(N'[dbo].[CHEQUE_PRINT_AUDIT]'))
    CREATE NONCLUSTERED INDEX [IX_CHQ_AUD_Action]
        ON [dbo].[CHEQUE_PRINT_AUDIT]([ActionCode], [PrintedBy], [PrintedDate]);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = N'IX_BANK_MASTER_Active' AND object_id = OBJECT_ID(N'[dbo].[BANK_MASTER]'))
    CREATE NONCLUSTERED INDEX [IX_BANK_MASTER_Active]
        ON [dbo].[BANK_MASTER]([CompanyID], [Active], [BankName]);
GO

PRINT 'Cheque Printing schema created successfully.';
GO
