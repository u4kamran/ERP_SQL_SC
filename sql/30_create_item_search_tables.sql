-- Item search aliases + anonymous search log (business DB).
-- Safe to rerun. Does not duplicate FIN_ITEM.
USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

IF OBJECT_ID(N'dbo.item_search_alias', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_search_alias (
        id INT IDENTITY(1,1) NOT NULL,
        alias_text NVARCHAR(80) NOT NULL,
        expand_text NVARCHAR(120) NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_item_search_alias_active DEFAULT (1),
        created_at DATETIME2 NOT NULL CONSTRAINT DF_item_search_alias_created DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_search_alias PRIMARY KEY CLUSTERED (id),
        CONSTRAINT UQ_item_search_alias UNIQUE (alias_text)
    );
END;
GO

IF OBJECT_ID(N'dbo.item_search_log', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_search_log (
        id INT IDENTITY(1,1) NOT NULL,
        query_text NVARCHAR(120) NOT NULL,
        cleaned_query NVARCHAR(120) NULL,
        result_count INT NOT NULL CONSTRAINT DF_item_search_log_count DEFAULT (0),
        selected_manual_id INT NULL,
        channel NVARCHAR(20) NOT NULL CONSTRAINT DF_item_search_log_channel DEFAULT (N'web'),
        created_at DATETIME2 NOT NULL CONSTRAINT DF_item_search_log_created DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_search_log PRIMARY KEY CLUSTERED (id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_search_log_created'
      AND object_id = OBJECT_ID(N'dbo.item_search_log')
)
    CREATE NONCLUSTERED INDEX IX_item_search_log_created
        ON dbo.item_search_log (created_at DESC, result_count);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_FIN_ITEM_TITLE'
      AND object_id = OBJECT_ID(N'dbo.FIN_ITEM')
)
    CREATE NONCLUSTERED INDEX IX_FIN_ITEM_TITLE
        ON dbo.FIN_ITEM (ITEM_TITLE)
        INCLUDE (manualid, ITEM_SHORT, barcodeid, SALES_RATE, CQTY, ED_STATUS);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_FIN_ITEM_BARCODE'
      AND object_id = OBJECT_ID(N'dbo.FIN_ITEM')
)
    CREATE NONCLUSTERED INDEX IX_FIN_ITEM_BARCODE
        ON dbo.FIN_ITEM (barcodeid)
        INCLUDE (manualid, ITEM_TITLE);
GO

-- Seed a small maintainable Roman Urdu / typo alias set (not hundreds of guesses).
IF NOT EXISTS (SELECT 1 FROM dbo.item_search_alias)
BEGIN
    INSERT INTO dbo.item_search_alias (alias_text, expand_text) VALUES
        (N'doodh', N'milk'),
        (N'chai', N'tea'),
        (N'cheeni', N'sugar'),
        (N'chini', N'sugar'),
        (N'aata', N'atta'),
        (N'atta', N'flour'),
        (N'coke', N'coca cola'),
        (N'cola', N'coca cola'),
        (N'biscut', N'biscuit'),
        (N'biscuit', N'biscuit'),
        (N'talbena', N'talbeena'),
        (N'talbina', N'talbeena'),
        (N'brad', N'bread'),
        (N'bred', N'bread'),
        (N'cornflake', N'corn flakes'),
        (N'cornflakes', N'corn flakes');
END;
GO
