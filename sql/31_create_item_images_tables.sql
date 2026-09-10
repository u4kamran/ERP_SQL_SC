-- Item Image Scraping & Linking (separate tables only).
-- READ-ONLY toward dbo.FIN_ITEM — never ALTER / UPDATE / INSERT into FIN_ITEM.
-- Safe to rerun. SQL Server compatible.
USE [nsds2626];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

-- ---------------------------------------------------------------------------
-- Settings (single-row)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.item_image_settings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_settings (
        id INT NOT NULL,
        auto_accept_min INT NOT NULL CONSTRAINT DF_iis_auto DEFAULT (90),
        review_min INT NOT NULL CONSTRAINT DF_iis_review DEFAULT (70),
        requests_per_minute INT NOT NULL CONSTRAINT DF_iis_rpm DEFAULT (20),
        max_concurrent INT NOT NULL CONSTRAINT DF_iis_conc DEFAULT (2),
        timeout_seconds INT NOT NULL CONSTRAINT DF_iis_timeout DEFAULT (15),
        retry_count INT NOT NULL CONSTRAINT DF_iis_retry DEFAULT (2),
        min_width INT NOT NULL CONSTRAINT DF_iis_minw DEFAULT (80),
        min_height INT NOT NULL CONSTRAINT DF_iis_minh DEFAULT (80),
        download_enabled BIT NOT NULL CONSTRAINT DF_iis_dl DEFAULT (1),
        open_food_facts_enabled BIT NOT NULL CONSTRAINT DF_iis_off DEFAULT (1),
        upcitemdb_enabled BIT NOT NULL CONSTRAINT DF_iis_upc DEFAULT (0),
        updated_by_user_id INT NULL,
        updated_by_username NVARCHAR(100) NULL,
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_iis_updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_image_settings PRIMARY KEY CLUSTERED (id),
        CONSTRAINT CK_item_image_settings_id CHECK (id = 1)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.item_image_settings WHERE id = 1)
BEGIN
    INSERT INTO dbo.item_image_settings (id) VALUES (1);
END;
GO

-- ---------------------------------------------------------------------------
-- Per-item image status (logical link to FIN_ITEM.ITEM_ID)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.item_image_status', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_status (
        item_id FLOAT NOT NULL,
        manual_id INT NULL,
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_iist_status DEFAULT (N'NO_IMAGE'),
        primary_image_id BIGINT NULL,
        last_match_score INT NULL,
        last_source_name NVARCHAR(80) NULL,
        last_search_query NVARCHAR(200) NULL,
        last_searched_at DATETIME2 NULL,
        last_error NVARCHAR(400) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_iist_created DEFAULT (SYSDATETIME()),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_iist_updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_image_status PRIMARY KEY CLUSTERED (item_id),
        CONSTRAINT CK_item_image_status_status CHECK (
            status IN (
                N'NO_IMAGE', N'SEARCHING', N'IMAGE_FOUND',
                N'NEEDS_REVIEW', N'APPROVED', N'FAILED'
            )
        )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_image_status_status'
      AND object_id = OBJECT_ID(N'dbo.item_image_status')
)
    CREATE NONCLUSTERED INDEX IX_item_image_status_status
        ON dbo.item_image_status (status, updated_at DESC);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_image_status_manual'
      AND object_id = OBJECT_ID(N'dbo.item_image_status')
)
    CREATE NONCLUSTERED INDEX IX_item_image_status_manual
        ON dbo.item_image_status (manual_id)
        WHERE manual_id IS NOT NULL;
GO

-- ---------------------------------------------------------------------------
-- Linked images
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.item_images', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_images (
        image_id BIGINT IDENTITY(1,1) NOT NULL,
        item_id FLOAT NOT NULL,
        image_url NVARCHAR(1000) NULL,
        local_image_path NVARCHAR(500) NULL,
        thumb_path NVARCHAR(500) NULL,
        source_url NVARCHAR(1000) NULL,
        source_name NVARCHAR(80) NULL,
        search_query NVARCHAR(200) NULL,
        match_score INT NULL,
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_ii_status DEFAULT (N'IMAGE_FOUND'),
        is_primary BIT NOT NULL CONSTRAINT DF_ii_primary DEFAULT (0),
        content_hash NVARCHAR(64) NULL,
        width_px INT NULL,
        height_px INT NULL,
        mime_type NVARCHAR(40) NULL,
        created_by_user_id INT NULL,
        created_by_username NVARCHAR(100) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_ii_created DEFAULT (SYSDATETIME()),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_ii_updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_images PRIMARY KEY CLUSTERED (image_id),
        CONSTRAINT CK_item_images_status CHECK (
            status IN (
                N'IMAGE_FOUND', N'NEEDS_REVIEW', N'APPROVED',
                N'REJECTED', N'FAILED', N'MANUAL'
            )
        )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_images_item'
      AND object_id = OBJECT_ID(N'dbo.item_images')
)
    CREATE NONCLUSTERED INDEX IX_item_images_item
        ON dbo.item_images (item_id, is_primary DESC, status);
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UQ_item_images_item_url'
      AND object_id = OBJECT_ID(N'dbo.item_images')
)
    CREATE UNIQUE NONCLUSTERED INDEX UQ_item_images_item_url
        ON dbo.item_images (item_id, image_url)
        WHERE image_url IS NOT NULL;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_images_hash'
      AND object_id = OBJECT_ID(N'dbo.item_images')
)
    CREATE NONCLUSTERED INDEX IX_item_images_hash
        ON dbo.item_images (item_id, content_hash)
        WHERE content_hash IS NOT NULL;
GO

-- ---------------------------------------------------------------------------
-- Search candidates (pending review / dry-run display)
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.item_image_candidates', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_candidates (
        candidate_id BIGINT IDENTITY(1,1) NOT NULL,
        item_id FLOAT NOT NULL,
        image_url NVARCHAR(1000) NOT NULL,
        source_url NVARCHAR(1000) NULL,
        source_name NVARCHAR(80) NULL,
        search_query NVARCHAR(200) NULL,
        match_score INT NULL,
        product_title NVARCHAR(200) NULL,
        product_brand NVARCHAR(120) NULL,
        product_barcode NVARCHAR(50) NULL,
        session_key NVARCHAR(40) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_iic_created DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_image_candidates PRIMARY KEY CLUSTERED (candidate_id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_image_candidates_item'
      AND object_id = OBJECT_ID(N'dbo.item_image_candidates')
)
    CREATE NONCLUSTERED INDEX IX_item_image_candidates_item
        ON dbo.item_image_candidates (item_id, created_at DESC);
GO

-- ---------------------------------------------------------------------------
-- Bulk jobs
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.item_image_jobs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_jobs (
        job_id BIGINT IDENTITY(1,1) NOT NULL,
        scope NVARCHAR(40) NOT NULL,
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_iij_status DEFAULT (N'PENDING'),
        dry_run BIT NOT NULL CONSTRAINT DF_iij_dry DEFAULT (0),
        test_limit INT NULL,
        total_count INT NOT NULL CONSTRAINT DF_iij_total DEFAULT (0),
        processed_count INT NOT NULL CONSTRAINT DF_iij_proc DEFAULT (0),
        found_count INT NOT NULL CONSTRAINT DF_iij_found DEFAULT (0),
        approved_count INT NOT NULL CONSTRAINT DF_iij_appr DEFAULT (0),
        review_count INT NOT NULL CONSTRAINT DF_iij_rev DEFAULT (0),
        not_found_count INT NOT NULL CONSTRAINT DF_iij_nf DEFAULT (0),
        failed_count INT NOT NULL CONSTRAINT DF_iij_fail DEFAULT (0),
        filter_status NVARCHAR(20) NULL,
        filter_query NVARCHAR(120) NULL,
        created_by_user_id INT NULL,
        created_by_username NVARCHAR(100) NULL,
        started_at DATETIME2 NULL,
        finished_at DATETIME2 NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_iij_created DEFAULT (SYSDATETIME()),
        updated_at DATETIME2 NOT NULL CONSTRAINT DF_iij_updated DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_image_jobs PRIMARY KEY CLUSTERED (job_id),
        CONSTRAINT CK_item_image_jobs_status CHECK (
            status IN (
                N'PENDING', N'RUNNING', N'PAUSED',
                N'CANCELLED', N'COMPLETED', N'FAILED'
            )
        )
    );
END;
GO

IF OBJECT_ID(N'dbo.item_image_job_items', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_job_items (
        job_item_id BIGINT IDENTITY(1,1) NOT NULL,
        job_id BIGINT NOT NULL,
        item_id FLOAT NOT NULL,
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_iiji_status DEFAULT (N'PENDING'),
        result_status NVARCHAR(20) NULL,
        match_score INT NULL,
        error_message NVARCHAR(400) NULL,
        processed_at DATETIME2 NULL,
        CONSTRAINT PK_item_image_job_items PRIMARY KEY CLUSTERED (job_item_id),
        CONSTRAINT UQ_item_image_job_items UNIQUE (job_id, item_id),
        CONSTRAINT CK_item_image_job_items_status CHECK (
            status IN (N'PENDING', N'PROCESSING', N'DONE', N'SKIPPED', N'FAILED')
        )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_image_job_items_pending'
      AND object_id = OBJECT_ID(N'dbo.item_image_job_items')
)
    CREATE NONCLUSTERED INDEX IX_item_image_job_items_pending
        ON dbo.item_image_job_items (job_id, status)
        INCLUDE (item_id);
GO

-- ---------------------------------------------------------------------------
-- Audit + errors
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.item_image_audit', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_audit (
        audit_id BIGINT IDENTITY(1,1) NOT NULL,
        item_id FLOAT NULL,
        image_id BIGINT NULL,
        action NVARCHAR(40) NOT NULL,
        source_name NVARCHAR(80) NULL,
        detail NVARCHAR(500) NULL,
        user_id INT NULL,
        username NVARCHAR(100) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_iia_created DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_image_audit PRIMARY KEY CLUSTERED (audit_id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_image_audit_item'
      AND object_id = OBJECT_ID(N'dbo.item_image_audit')
)
    CREATE NONCLUSTERED INDEX IX_item_image_audit_item
        ON dbo.item_image_audit (item_id, created_at DESC);
GO

IF OBJECT_ID(N'dbo.item_image_errors', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.item_image_errors (
        error_id BIGINT IDENTITY(1,1) NOT NULL,
        item_id FLOAT NULL,
        job_id BIGINT NULL,
        error_code NVARCHAR(40) NOT NULL,
        error_message NVARCHAR(500) NOT NULL,
        provider_name NVARCHAR(80) NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_iie_created DEFAULT (SYSDATETIME()),
        CONSTRAINT PK_item_image_errors PRIMARY KEY CLUSTERED (error_id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_item_image_errors_created'
      AND object_id = OBJECT_ID(N'dbo.item_image_errors')
)
    CREATE NONCLUSTERED INDEX IX_item_image_errors_created
        ON dbo.item_image_errors (created_at DESC);
GO
