# Enterprise Cheque Printing Module (VB6)

Database-driven cheque printing for the existing VB6 ERP. New bank formats require **only a new layout in the database** — no program changes.

## Quick start

1. Run SQL scripts (in order) against the ERP database / auth DB:
   - `sql/22_create_cheque_printing_tables.sql`
   - `sql/23_seed_cheque_printing_permissions.sql`
   - `sql/24_seed_cheque_sample_layout.sql`
2. Add all files in this folder to your VB6 project (`.bas`, `.cls`, `.frm`).
3. References: **ADODB**, **MSFLXGRD**, **MSCOMCT2** (search form).
4. Ensure global `Con` (ADODB.Connection) is open — same as rest of ERP.
5. Paste `integration/VoucherM_PrintCheque.bas.txt` into `VoucherM` (Print Cheque button).
6. Paste `integration/GlMenu_ChequeHooks.bas.txt` menu handlers into `GlMenu`.
7. Grant `CHEQUE_PERMISSION` rows (seed grants `ADMIN`).
8. Open **Layout Designer**, adjust sample layout to your physical cheque, then **Alignment Wizard**.

## Components

| Layer | Files |
|-------|-------|
| Enums / WinAPI / Utils | `modChequeEnums.bas`, `modChequeWinAPI.bas`, `modChequeUtils.bas` |
| Engine | `clsChequePrinter.cls`, `clsLayoutManager.cls`, `clsPrinterManager.cls` |
| Data / Words / Audit | `clsChequeData.cls`, `clsAmountToWords.cls`, `clsChequeAudit.cls`, `clsLayoutObject.cls` |
| UI | `frmChequePrint`, `frmChequeLayoutDesigner`, `frmChequeCalibration`, `frmChequeHistory`, `frmChequeSearch`, `frmChequeBatch` |

## Architecture

See [docs/VB6_CHEQUE_PRINTING.md](../../docs/VB6_CHEQUE_PRINTING.md).

## Design rules

- Coordinates in **millimetres** in `CHEQUE_LAYOUT_DETAIL` — never hard-code in forms.
- Print engine does not reference UI forms.
- Layouts are cached per session in `clsLayoutManager`.
- Duplicate print → confirm Reprint? → requires `cheque.reprint` → full audit row.

## Mapping voucher fields

Edit `clsChequeData.MapGl0002` / `LoadFromVoucher` if your voucher column names differ (`AC_TITLE`, `CHEQUE_NO`, `AMOUNT`, etc.). That class is the **only** voucher mapping point.

## Future hooks already in schema

- `CHEQUE_POSITIVE_PAY_QUEUE`
- Object codes: `LOGO`, `QR_CODE`, `WATERMARK`, `MICR_IGNORE`
- `CHEQUE_BOOK` for multi-book sequencing
- `CompanyID` on masters for multi-company
