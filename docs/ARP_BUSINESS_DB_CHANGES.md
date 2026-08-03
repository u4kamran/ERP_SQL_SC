# ARP Business Database Changes — Sales Dashboard (Single Date Fix)

Database: **NAHSL2627** on **shaheenhp**  
Applies to: Al Haram Steel Lab (ARP) sales dashboard — **Today**, **Yesterday**, and manual single-day ranges.

---

## Problem

Single-day filters return **0 rows** (or wrong totals) on ARP, while month ranges may look partially OK.

| Check | ERP (`nsds2626`) | ARP (`NAHSL2627`) today |
|---|---|---|
| View `V_FIN_SALE_DISC_NEW2` date column | `DOC_DATE_T` | `DOC_DATE` |
| Sample time on date column | `2026-08-01 00:07:29` | `2026-07-20 00:00:00` (always midnight) |
| `FIN_INV_M.DOC_DATE_T` exists? | Yes | **Yes — already populated** |
| Yesterday business window (08:00 → 05:00) | Works | **0 rows** |
| Example: 20-Jul-2026 single day | Works via `DOC_DATE_T` | **0 rows** with current view |

**Root cause:** The ARP view exposes `FIN_INV_M.DOC_DATE` (accounting date at **00:00:00**).  
The web dashboard filters with **business hours** (e.g. 20-Jul **08:00** → 21-Jul **05:00**).  
Midnight (`00:00:00`) is **before 08:00**, so single-day queries miss all rows.

`DOC_DATE_T` (actual invoice timestamp) already exists on `FIN_INV_M` and is used correctly on ERP.

---

## Required change (1 item)

### 1. Update view `dbo.V_FIN_SALE_DISC_NEW2`

**Change:** Use `FIN_INV_M.DOC_DATE_T` instead of `FIN_INV_M.DOC_DATE`.

**Before (ARP):**
```sql
SELECT ... dbo.FIN_INV_M.DOC_DATE, ...
```

**After (match ERP):**
```sql
SELECT ... dbo.FIN_INV_M.DOC_DATE_T, ...
```

**Script:** `sql/10_fix_arp_sales_view.sql`

**How to run:**
```bat
sqlcmd -S shaheenhp -U sa -P your_password -d NAHSL2627 -i sql\10_fix_arp_sales_view.sql
```

Or open the file in **SQL Server Management Studio**, connect to `NAHSL2627`, and execute.

**After running:** Restart ARP app (`START-ARP.bat`) so the site picks up the new column name.

---

## What you do NOT need to change

| Item | Action |
|---|---|
| `FIN_INV_M.DOC_DATE` data | **Keep as-is** — accounting date, different purpose |
| `FIN_INV_M.DOC_DATE_T` data | **Already filled** — no backfill needed |
| New tables | **Not required** |
| Auth database `NAHSL2627_AUTH` | **Not affected** — this is business DB only |
| ERP database `nsds2626` | **No change** — already correct |

---

## Optional (only if you need accounting date in reports later)

Not required for the sales dashboard fix.

| Optional change | Why |
|---|---|
| Add `DOC_DATE` as an extra column in the view (alongside `DOC_DATE_T`) | If you want both transaction time and accounting date in custom reports |
| Create a second view e.g. `V_FIN_SALE_DISC_ACCT` using `DOC_DATE` | For GL/accounting-date reports only |

The web sales dashboard is designed for **business-day hours** and expects **`DOC_DATE_T`**, same as VB6 ERP on Shafique Center.

---

## Verification after fix

Run on **NAHSL2627**:

```sql
-- 1) View must expose DOC_DATE_T
SELECT TOP 5 DOC_DATE_T, TOTAL_AMT
FROM dbo.V_FIN_SALE_DISC_NEW2
ORDER BY DOC_DATE_T DESC;

-- 2) Single business day example (20-Jul-2026, 08:00 → 21-Jul 05:00)
SELECT COUNT(*) AS row_count
FROM dbo.V_FIN_SALE_DISC_NEW2
WHERE INV_ID BETWEEN 1 AND 999999999
  AND DOC_DATE_T BETWEEN '2026-07-20 08:00:00' AND '2026-07-21 05:00:00';
-- Expected: > 0 if you have sales in that period (test showed 27 rows before fix)
```

Then in the browser:
1. Open https://arp.ahsteellab.com/admin/sales-dashboard  
2. Click **Yesterday** or set **From/To** to the same business day  
3. Click **Refresh** — totals should appear (not 0 / not Internal Server Error)

---

## Summary checklist

- [ ] Run `sql/10_fix_arp_sales_view.sql` on **NAHSL2627**
- [ ] Confirm view column is `DOC_DATE_T` (not `DOC_DATE`)
- [ ] Restart ARP: `START-ARP.bat`
- [ ] Test **Yesterday** and one manual single-day range on sales dashboard

---

## Reference — column meaning on `FIN_INV_M`

| Column | Meaning | Example (ARP) |
|---|---|---|
| `DOC_DATE` | Accounting / voucher date (stored at midnight) | `2026-07-20 00:00:00` |
| `DOC_DATE_T` | Actual transaction timestamp | `2026-07-21 14:24:00` |

Sales dashboard (web + VB6 ERP) uses **`DOC_DATE_T`** for business-day logic (08:00 → next day 05:00).
