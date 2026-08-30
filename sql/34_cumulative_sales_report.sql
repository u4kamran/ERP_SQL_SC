/*
================================================================================
  CUMULATIVE SALES REPORT — with Last Month comparison (SSMS)
  Compatible with SQL Server 2008 / 2008 R2 (no FORMAT, no CONCAT)

  Amount columns: comma-separated, 2 decimal places (e.g. 1,234,567.89)

  For each cumulative row (current month), the next row shows the same
  business-day span one calendar month earlier.

  ERP (nsds2626)  : DOC_DATE_T
  ARP (nahsl2627) : change DOC_DATE_T to DOC_DATE in the JOIN
================================================================================
*/

USE nsds2626;
GO

SET NOCOUNT ON;

-- ======================== CHANGE ONLY THESE TWO LINES ========================
DECLARE @FromDate DATETIME;
DECLARE @ToDate   DATETIME;

SET @FromDate = '2026-08-01 08:00:00';
SET @ToDate   = '2026-08-05 05:00:00';
-- ============================================================================

DECLARE @BizStartHour INT;
DECLARE @BizEndHour   INT;
DECLARE @StartBD      DATETIME;
DECLARE @EndBD        DATETIME;
DECLARE @FixedStart   DATETIME;
DECLARE @PrevStart    DATETIME;
DECLARE @DayCount     INT;

SET @BizStartHour = 8;
SET @BizEndHour   = 5;

SET @StartBD = CASE
    WHEN DATEPART(HOUR, @FromDate) < @BizStartHour
    THEN DATEADD(DAY, -1, CAST(FLOOR(CAST(@FromDate AS FLOAT)) AS DATETIME))
    ELSE CAST(FLOOR(CAST(@FromDate AS FLOAT)) AS DATETIME)
END;

SET @EndBD = CASE
    WHEN DATEPART(HOUR, @ToDate) < @BizStartHour
    THEN DATEADD(DAY, -1, CAST(FLOOR(CAST(@ToDate AS FLOAT)) AS DATETIME))
    ELSE CAST(FLOOR(CAST(@ToDate AS FLOAT)) AS DATETIME)
END;

SET @FixedStart = DATEADD(HOUR, @BizStartHour, @StartBD);
SET @PrevStart  = DATEADD(MONTH, -1, @FixedStart);
SET @DayCount   = DATEDIFF(DAY, @StartBD, @EndBD);

IF @DayCount < 0
BEGIN
    RAISERROR('To date is before From date — no business days in range.', 16, 1);
    RETURN;
END;

;WITH nums AS (
    SELECT 0 AS n
    UNION ALL
    SELECT n + 1
    FROM nums
    WHERE n < @DayCount
),
period_ends AS (
    SELECT
        n + 1 AS row_num,
        DATEADD(HOUR, @BizEndHour, DATEADD(DAY, n + 1, @StartBD)) AS period_end
    FROM nums
),
periods AS (
    SELECT
        pe.row_num,
        N'Current' AS period_type,
        0 AS sort_key,
        @FixedStart AS period_start,
        pe.period_end AS period_end
    FROM period_ends pe

    UNION ALL

    SELECT
        pe.row_num,
        N'Last Month' AS period_type,
        1 AS sort_key,
        @PrevStart AS period_start,
        DATEADD(MONTH, -1, pe.period_end) AS period_end
    FROM period_ends pe
),
sales AS (
    SELECT
        p.row_num,
        p.period_type,
        p.sort_key,
        p.period_start,
        p.period_end,
        ISNULL(SUM(v.TOTAL_AMT), 0) AS total_sale,
        ISNULL(SUM(v.COST_AMT * v.QTY), 0) AS total_cost,
        ISNULL(SUM(v.TOTAL_AMT), 0) - ISNULL(SUM(v.COST_AMT * v.QTY), 0) AS profit,
        COUNT(DISTINCT v.INV_ID) AS invoice_count
    FROM periods p
    LEFT JOIN dbo.V_FIN_SALE_DISC_NEW2 v
        ON v.INV_ID BETWEEN 1 AND 999999999
       AND v.DOC_DATE_T >= p.period_start
       AND v.DOC_DATE_T <= p.period_end
    GROUP BY
        p.row_num,
        p.period_type,
        p.sort_key,
        p.period_start,
        p.period_end
),
calc AS (
    SELECT
        s.*,
        CASE
            WHEN s.total_cost = 0 THEN NULL
            ELSE ROUND(s.profit / s.total_cost * 100.0, 2)
        END AS profit_pct,
        ROUND(s.total_sale / s.row_num, 2) AS avg_sale_per_day
    FROM sales s
)
SELECT
    CASE WHEN c.period_type = N'Current' THEN c.row_num ELSE NULL END AS [#],
    c.period_type AS [Period],
    CONVERT(VARCHAR(11), c.period_start, 106)
        + ' '
        + RIGHT('0' + CAST(DATEPART(HOUR, c.period_start) AS VARCHAR(2)), 2)
        + ':'
        + RIGHT('0' + CAST(DATEPART(MINUTE, c.period_start) AS VARCHAR(2)), 2)
        + ' -> '
        + CONVERT(VARCHAR(11), c.period_end, 106)
        + ' '
        + RIGHT('0' + CAST(DATEPART(HOUR, c.period_end) AS VARCHAR(2)), 2)
        + ':'
        + RIGHT('0' + CAST(DATEPART(MINUTE, c.period_end) AS VARCHAR(2)), 2)
        AS [Cumulative Business Period],
    CONVERT(VARCHAR(30), CAST(ROUND(c.total_sale, 2) AS MONEY), 1) AS [Sale],
    CONVERT(VARCHAR(30), CAST(ROUND(c.total_cost, 2) AS MONEY), 1) AS [Cost],
    CONVERT(VARCHAR(30), CAST(ROUND(c.profit, 2) AS MONEY), 1) AS [Profit],
    CASE
        WHEN c.profit_pct IS NULL THEN NULL
        ELSE CONVERT(VARCHAR(20), CAST(c.profit_pct AS MONEY), 1) + '%'
    END AS [Profit %],
    CONVERT(VARCHAR(30), CAST(c.avg_sale_per_day AS MONEY), 1) AS [Avg Sale / Day],
    c.invoice_count AS [Invoices]
FROM calc c
ORDER BY c.row_num, c.sort_key
OPTION (MAXRECURSION 366);

GO
