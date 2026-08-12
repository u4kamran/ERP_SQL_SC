# Enterprise Cheque Printing Module (VB6)

**Module path:** `vb6/ChequePrinting/`  
**SQL:** `sql/22_create_cheque_printing_tables.sql`, `sql/23_seed_cheque_printing_permissions.sql`, `sql/24_seed_cheque_sample_layout.sql`  
**Integration host:** `VoucherM` (Voucher Entry) — button **Print Cheque** beside Print Voucher / Print  
**Design unit:** millimetres (ISO banking layout practice)  
**Print API:** VB6 `Printer` object + Win32 printer enumeration

---

## 1. Objectives

- Print cheques on any Windows laser/inkjet (dot-matrix optional) **without hard-coded coordinates**.
- Support **unlimited bank layouts** via database configuration only.
- Pull payee / amount / dates / narration from the **current voucher** — no re-entry.
- Enforce **duplicate-print protection**, full **audit trail**, and **role permissions**.
- Provide a **visual layout designer** (Crystal-Reports-style) and **alignment wizard**.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  UI Layer                                                        │
│  frmChequePrint | Designer | Calibration | History | Search | Batch│
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Service / Engine Layer (UI-independent)                         │
│  clsChequePrinter | clsLayoutManager | clsPrinterManager         │
│  clsAmountToWords | clsChequeData | clsChequeAudit               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Data Layer (ADO / SQL Server)                                   │
│  BANK_MASTER | CHEQUE_LAYOUT_* | CHEQUE_PRINT_* | CHEQUE_PERM_*  │
└─────────────────────────────────────────────────────────────────┘
```

**Rules**

| Rule | Implementation |
|------|----------------|
| No layout hard-coding | All objects from `CHEQUE_LAYOUT_DETAIL` |
| Engine ≠ UI | `clsChequePrinter` never references forms |
| Cache layouts | `clsLayoutManager` loads once per `LayoutID` per session |
| Scale by DPI | Design mm → inches → printer twips; apply calibration offsets |
| Transactions | Print status + audit written in one ADO transaction |

---

## 3. Coordinate & Scaling Model

Design coordinates are stored in **millimetres** relative to the cheque top-left (after paper margins).

```
X_twips = ((X_mm + LeftMargin_mm + OffsetLeft_mm) / 25.4) * 1440
Y_twips = ((Y_mm + TopMargin_mm  + OffsetTop_mm)  / 25.4) * 1440
W_twips = (Width_mm  / 25.4) * 1440
H_twips = (Height_mm / 25.4) * 1440
```

Optional DPI hint on layout is used for preview pixel mapping and high-DPI preview fidelity; physical print uses the selected printer’s scale.

Calibration offsets (`CHEQUE_PRINTER_CALIBRATION`) adjust Left/Right/Top/Bottom without editing the layout.

---

## 4. Printable Object Types

| ObjectCode | Description |
|------------|-------------|
| PAYEE_NAME | AC_TITLE / party name |
| AMOUNT | Numeric amount |
| AMOUNT_WORDS | Amount in words |
| CHEQUE_DATE | Formatted date |
| DATE_DD / DATE_MM / DATE_YYYY | Separate date boxes |
| CROSS_MARK | Crossing lines |
| AC_PAYEE | “A/C PAYEE” text |
| BEARER | Bearer text (often hidden) |
| COMPANY_NAME | Company |
| VOUCHER_NO | Source voucher |
| NARRATION | Narration / memo |
| CUSTOM_TEXT | Static text from `DefaultText` |
| SIGNATURE_AREA | Empty/signature box |
| MICR_IGNORE | Non-print / keep-out zone marker (preview only) |
| LOGO | Optional company logo (future) |
| WATERMARK | VOID / COPY / CANCELLED (status-driven) |
| QR_CODE | Reserved for future expansion |

---

## 5. Cheque Status Lifecycle

`Draft → Printed → Reprinted`  
Also: `Cancelled`, `Voided`, `Cleared`, `Bounced`

Reprint requires permission `cheque.reprint` and always appends an audit row.

---

## 6. Security & Permissions

| PermissionCode | Purpose |
|----------------|---------|
| cheque.print | Print Cheque |
| cheque.reprint | Confirm reprint |
| cheque.preview | Preview only |
| cheque.layout.create | New layout |
| cheque.layout.edit | Edit layout |
| cheque.layout.delete | Delete layout |
| cheque.cancel | Cancel / void |
| cheque.export_pdf | Export PDF/image |
| cheque.calibrate | Alignment wizard |
| cheque.batch | Batch print |
| cheque.history | View audit / search |

VB6 gates via `clsChequeAudit.HasPermission`; web auth seeds mirror the same codes for modernization parity.

---

## 7. Data Flow — Print Cheque from Voucher

1. User opens voucher on `VoucherM` and clicks **Print Cheque**.
2. Integration builds `clsChequeData` from voucher header/lines (`gl0002` / party `AC_TITLE`, bank line, amount, etc.).
3. `frmChequePrint` resolves bank → default layout → printer preference.
4. `clsChequePrinter.Preview` / `.PrintCheque`.
5. Duplicate check against `CHEQUE_PRINT_REGISTER`.
6. On success: register = Printed/Reprinted; audit row inserted; optional cheque number advance.

---

## 8. Future Expansion Hooks

Interfaces / reserved columns already present for:

- Positive Pay file export (`CHEQUE_POSITIVE_PAY_QUEUE`)
- Electronic signature blob path
- Multi-company `CompanyID` on all masters
- Multi-currency cheque books (`CHEQUE_BOOK`)
- QR / MICR / watermark / logo object types
- Automatic cheque number sequencing with unique constraint

---

## 9. File Inventory

| File | Role |
|------|------|
| `modChequeEnums.bas` | Enums & constants |
| `modChequeWinAPI.bas` | Printer API declarations |
| `modChequeUtils.bas` | Formatting, case, grid snap, errors |
| `clsAmountToWords.cls` | Multi-currency amount in words |
| `clsPrinterManager.cls` | Enumerate / select / remember printers |
| `clsLayoutManager.cls` | Load/cache/save layouts |
| `clsChequeData.cls` | Voucher → print DTO |
| `clsChequeAudit.cls` | Permissions, register, audit |
| `clsChequePrinter.cls` | Preview & print engine |
| `frmChequePrint.frm` | Print / preview dialog |
| `frmChequeLayoutDesigner.frm` | Visual designer |
| `frmChequeCalibration.frm` | Alignment wizard |
| `frmChequeHistory.frm` | Audit viewer |
| `frmChequeSearch.frm` | Search / export |
| `frmChequeBatch.frm` | Batch print |
| `integration/VoucherM_PrintCheque.bas.txt` | Drop-in voucher button code |
| `integration/GlMenu_ChequeHooks.bas.txt` | Menu hooks |

---

## 10. Installation (VB6 project)

1. Run SQL scripts 22 → 23 → 24 against the ERP database (and auth DB for web permissions).
2. Add all `.bas` / `.cls` / `.frm` to the VB6 group project.
3. References: **Microsoft ActiveX Data Objects 2.x**, **Microsoft Common Dialog Control** (optional), **stdole**.
4. Paste integration snippets into `VoucherM` and `GlMenu`.
5. Grant permissions; create first bank + layout via Designer or seed script.
6. Run Calibration Wizard once per physical printer.
