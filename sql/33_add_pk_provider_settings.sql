-- PK provider settings columns (safe to rerun).
USE [nsds2626];
GO

SET NOCOUNT ON;
GO

IF COL_LENGTH('dbo.item_image_settings', 'naheed_enabled') IS NULL
    ALTER TABLE dbo.item_image_settings ADD naheed_enabled BIT NOT NULL
        CONSTRAINT DF_iis_naheed DEFAULT (1);
GO

IF COL_LENGTH('dbo.item_image_settings', 'metro_enabled') IS NULL
    ALTER TABLE dbo.item_image_settings ADD metro_enabled BIT NOT NULL
        CONSTRAINT DF_iis_metro DEFAULT (0);
GO

IF COL_LENGTH('dbo.item_image_settings', 'carrefour_enabled') IS NULL
    ALTER TABLE dbo.item_image_settings ADD carrefour_enabled BIT NOT NULL
        CONSTRAINT DF_iis_carrefour DEFAULT (0);
GO

IF COL_LENGTH('dbo.item_image_settings', 'imtiaz_enabled') IS NULL
    ALTER TABLE dbo.item_image_settings ADD imtiaz_enabled BIT NOT NULL
        CONSTRAINT DF_iis_imtiaz DEFAULT (0);
GO

IF COL_LENGTH('dbo.item_image_settings', 'alfatah_enabled') IS NULL
    ALTER TABLE dbo.item_image_settings ADD alfatah_enabled BIT NOT NULL
        CONSTRAINT DF_iis_alfatah DEFAULT (0);
GO

IF COL_LENGTH('dbo.item_image_settings', 'no_match_min') IS NULL
    ALTER TABLE dbo.item_image_settings ADD no_match_min INT NOT NULL
        CONSTRAINT DF_iis_no_match DEFAULT (50);
GO

UPDATE dbo.item_image_settings
SET naheed_enabled = 1,
    metro_enabled = ISNULL(metro_enabled, 0),
    carrefour_enabled = ISNULL(carrefour_enabled, 0),
    imtiaz_enabled = ISNULL(imtiaz_enabled, 0),
    alfatah_enabled = ISNULL(alfatah_enabled, 0),
    open_food_facts_enabled = 0,
    no_match_min = ISNULL(no_match_min, 50),
    requests_per_minute = CASE WHEN requests_per_minute > 12 THEN 12 ELSE requests_per_minute END,
    max_concurrent = CASE WHEN max_concurrent > 1 THEN 1 ELSE max_concurrent END
WHERE id = 1;
GO
