# VB6 Sales Dashboard

Sales summary dashboard for the legacy VB6 ERP project, matching the web app at `/admin/sales-dashboard`.

## Files

| File | Location |
|---|---|
| `FrmSalesDashboard.frm` | VB6 project root (also copied to `vb6/` in this repo) |
| Menu hook | `GlMenu.frm` → **Management Reports → Sales Dashboard** (Ctrl+D) |
| Project | `GL_Shafique_SingleINV_WS.vbp` and `GL_Shafique_SingleINV.vbp` |

## Open in VB6

1. Open **`E:\AccesToSQL_Barcode_20130316 - SI_BC_AutoInv_WholeSaleQty_V1_JanDec\GL_Shafique_SingleINV_WS.vbp`** in Visual Basic 6
2. If VB6 asks to reload changed files (`FrmSalesDashboard.frm`, `GlMenu.frm`), click **Yes**
3. Run the project (F5)
4. Open dashboard any of these ways:
   - Menu: **Reports → Management Reports → Sales Dashboard**
   - Shortcut: **Ctrl+D**
   - Toolbar: **Graph** button

## Features

- **KPI cards:** Total Sale, Total Cost, Profit, Profit %, Avg Sale/Day
- **Comparison:** Last month amount + % change under each KPI (matches web app)
- **Last month period** shown above the grids
- **Quick ranges:** Today, Yesterday, This Month, Last Month, Last 7, Last 30
- **Day-wise grid:** sales by business day
- **Top 10 invoices** by amount
- **Business day:** 08:00 today → 05:00 next morning (same as web app)

## Data source

```sql
dbo.V_FIN_SALE_DISC_NEW2
```

Same view used by the Python web sales dashboard.

## Install on another PC

Copy `FrmSalesDashboard.frm` into your VB6 project folder, then:

1. **Project → Add File** → select `FrmSalesDashboard.frm`
2. Add menu item in `GlMenu.frm` (or call `FrmSalesDashboard.Show vbModal` from any button)
3. Recompile the `.exe`

## Troubleshooting

| Problem | Fix |
|---|---|
| Invalid object name `V_FIN_SALE_DISC_NEW2` | Create/restore the view on SQL Server `nsds2626` |
| Invalid column name `DOC_DATE_T` | ARP/NAHSL2627 uses `DOC_DATE` — web app auto-detects; VB6 must use the column name from your view |
| Form not in project | Project → Add File → `FrmSalesDashboard.frm` |
| Wrong totals vs web | Check date range and business-day hours (08:00–05:00) |
