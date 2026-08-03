-- =============================================================================
-- ARP (NAHSL2627) — Sales Dashboard view fix
-- Run on: shaheenhp / database NAHSL2627
-- Purpose: Fix single-day / Yesterday / business-hour date filtering
-- =============================================================================

USE [NAHSL2627];
GO

-- Backup current definition (optional — run manually if you want a copy first)
-- SELECT m.definition
-- FROM sys.sql_modules m
-- JOIN sys.views v ON m.object_id = v.object_id
-- WHERE v.name = 'V_FIN_SALE_DISC_NEW2';

IF OBJECT_ID('dbo.V_FIN_SALE_DISC_NEW2', 'V') IS NULL
BEGIN
    RAISERROR('View dbo.V_FIN_SALE_DISC_NEW2 not found on NAHSL2627.', 16, 1);
    RETURN;
END;
GO

ALTER VIEW dbo.V_FIN_SALE_DISC_NEW2
AS
SELECT
    dbo.GC0002.l_uid,
    dbo.FIN_INV_D.COST_AMT,
    dbo.FIN_INV_M.DOC_DATE_T,   -- was DOC_DATE (midnight only — breaks single-day filters)
    dbo.FIN_INV_D.QTY,
    dbo.FIN_INV_D.DISC_AMT,
    dbo.FIN_INV_D.INV_ID,
    dbo.FIN_INV_D.TOTAL_AMT
FROM dbo.GC0002
RIGHT OUTER JOIN dbo.FIN_INV_D
    ON dbo.GC0002.serial_no = dbo.FIN_INV_D.SERIAL_NO
LEFT OUTER JOIN dbo.FIN_INV_M
    ON dbo.FIN_INV_D.SERIAL_NO = dbo.FIN_INV_M.SERIAL_NO
WHERE dbo.FIN_INV_D.INV_ID BETWEEN 1 AND 99999999;
GO

-- Quick verification
SELECT TOP 5 DOC_DATE_T, TOTAL_AMT, INV_ID
FROM dbo.V_FIN_SALE_DISC_NEW2
ORDER BY DOC_DATE_T DESC;
GO
