# VB6 Purchase Receipt Modernization — Fin_PurM / Fin_PurD / Fin_PurDed

**Source of truth:** `Fin_PurM.frm`, `Fin_PurD.frm`, `Fin_PurDed.frm`  
**Web path:** `/admin/fin-pur` · **API:** `/api/v1/fin-pur`  
**Company config:** `cSTaxType = 1` (flat-rate GL from `fin_c003`, Shafique Departmental Store)

---

## 1. Understanding Summary

Master–detail **Purchase Receipt (GRN)**:

| Form | Role |
|------|------|
| **Fin_PurM** | Header (GRN ID, date, supplier, payment terms, remarks, totals grid) + Save/Delete/Clear |
| **Fin_PurD** | Line entry modal (item, qty, rate, S-Tax, on/off invoice discount, exp date) |
| **Fin_PurDed** | Header discount/charges modal (maps into hidden H* labels on master) |

Document type: `cDoc_Type = 2` (`fin_c001`), book from `doc_book_id` (live: **102**, abbr **PUR**).  
Fiscal mode in Form_Load: `MFiscal = 0`, `MVMode = 1` (combined), `MBookType = 2`.

Persist targets: `Fin_Pur_M`, `Fin_Pur_D`, `gl0002`, `gl0003`, `fin_ldgr`, `fin_item` balances, `fin_supp_items`, serial via `gc0002`.

---

## 2. UI Analysis (Master Fin_PurM)

Title bar: **Purchase Receipt** (`Line2`). Caption = company name.

| Control | Type | Caption / Purpose | Tab |
|---------|------|-------------------|-----|
| TxtDocID | TextBox | GRN ID | 1 |
| TxtDocDAte | DTPicker | Document date | 2 |
| TxtGPID | TextBox | Ref # | 4 |
| TxtTime | TextBox | Time | 6 |
| CboPayment | Combo | Terms: Credit / Cash Reg. / Cash Un-Reg. | 7 |
| TxtID | TextBox | Supplier ID | 9 |
| TxtTitle | Label | Supplier title | — |
| LblRegistration | Label | Registered / UN-Registered / Other | — |
| VGrid | MSFlexGrid | 15 cols lines | 22 |
| TxtRemarks | TextBox | Remarks | 12 |
| CmdAddTrans | Button | &Add Trans. | 13 |
| CmdSave / Clear / Delete / Close | Buttons | CRUD + close | 14–17 |
| CmdShowAddr | Button | S&how Address | 18 |
| CmdDiscount | Button | Discoun&t → Fin_PurDed | 19 |
| CmdShowItem / Print Grid / Upload / Download / Check / Pur Order / Assign Co | Buttons | Aux (SA-gated for some) | — |
| Totals labels | Labels | Qty, Gross, Disc, S-Tax, Excl, Included, Off Inv Disc, Net, Diff, Charges | — |
| HDiscount…HOtherCharges | Labels | Hidden header charge buckets | Visible=False |
| FrameAddress | Frame | Cash vendor address (hidden until Show Address) | — |

**Grid columns (0–14):** Sr#, Item ID, Item Title, Qty, Rate, Amount, S-Tax %, S-Tax Amt, Disc %, Disc Amt, DOI %, DOI Amt, Included Amt, Remarks, ExpDate.

---

## 3. Database Analysis

### Fin_Pur_M (header)

| Column | Type | Notes |
|--------|------|-------|
| PROD_ID | int PK part | Document number |
| DOC_TYPE_ID | smallint | Always 2 |
| FISCAL | smallint | 0 yearly in this build |
| DOC_DATE | datetime | |
| SERIAL_NO | int | Links GL / detail |
| SUPPLIER_ID | int | Vendor / GL account |
| REMARKS, PAYMENT_TYPE, STAX_TYPE, GP_ID, GP_TIME | | |
| vendor_title, address, STAX_ID, CITY_ID | | Cash address fields |
| DISCOUNT_AMT, CLAIM_AMT, OTHER_DED_AMT, LOADING_AMT, CARRIAGE_AMT, OTHER_CHARGES_AMT | money | Header charges |
| SYS_STATUS | | 1 = posted (block edit) |
| TOTAL_AMT, AMOUNT, COUNTRY_ID | | Present; not always written by VB6 save |

### Fin_Pur_D (lines)

PROD_ID, SERIAL_NO, SERIAL_ORDER, ITEM_ID, QTY, RATE, PUR_AMT, STAX_RATE, STAX_AMT, TOTAL_AMT, remarks, DISC_PER, DISC_AMT, DISC_PER_OI, DISC_AMT_OI, EXP_DATE, doc_date

### Related

- `fin_c001` / `fin_c003` (doc_id=2) — abbr, book, GL integration IDs  
- `GL0004` / `Gc0003` — book + permission  
- `gl0006` + `City` — supplier  
- `gl0002` / `gl0003` / `gl0001` — voucher + balances  
- `fin_ldgr`, `fin_item`, `fin_supp_items`, `gc0002`  
- Views: `v_fin_item`, `V_FIN_STOCK_SUPPLIER`

---

## 4. Business Rules (verbatim behaviour)

1. No lines (`nCounter = 1`) → *"No transaction to slave"* — cannot save.  
2. Empty remarks → `"Nil"`.  
3. Doc date must be within `gsetup.fiscal_start` … `Fiscal_end`.  
4. Book permission via `Gc0003`; denied → block on DocID validate.  
5. Book `ed_status = 1` → stopped.  
6. Posted (`sys_status = 1`) → cannot open for edit.  
7. Edit path: reverse prior `fin_item` qty/amt and `gl0001` from old `gl0003`, delete old `Fin_Pur_d`, then rewrite.  
8. New number: `MAX(prod_id)+1` where `fiscal = MFiscal`; serial from `gc0002` (`nSerialNo`).  
9. Inventory on save: `Cqty += qty`, `CAMT += (pur+stax-disc-doi)`, `cost_Rate = that/qty`, `Tnot += 1`.  
10. Inventory reverse on edit/delete uses **`pur_Amt` only** (VB6 as written).  
11. `cSTaxType = 1`: summed purchase Dr to `sp_ac_id` / `sp_ac_id_local`, S-Tax Dr to `stax_id`; per-line purchase GL skipped.  
12. Supplier Cr = `lTsale - LDiscount - LblOffInvDisc + lTSalesTax + mCharges`.  
13. Header Loading/Carriage UI fields are **double-swapped** through Fin_PurDed ↔ H* ↔ GL accounts (preserve).  
14. Duplicate item ID on new line rejected in Fin_PurD.  
15. Delete requires `cUPwordStr` position 5 = `1` (mapped to `inventory.fin_pur.delete`).  
16. After save, `checkDetailData`: if `gl0002` exists without `gl0003` for book 102, force re-save message.  
17. SA-only: Assign Co, Upload, Download, Check visibility.  
18. Item disabled (`ed_status=1`) cannot be used on lines.

---

## 5. Validation Rules

| Area | Rule |
|------|------|
| Supplier | Must exist in `gl0006`; empty title invalid |
| GRN load | Exists for prod_id + doc_type_id=2 + fiscal |
| Line | Qty required; Company ID required; Rate optional if `cAudit` |
| Item ID | Length ≥ 10 (VB6); must exist in `FIN_ITEM` |
| Barcode / Manual / WS | Lookup via `v_fin_item` |
| Book | Permission + not stopped |
| Delete | Confirm + delete permission |

---

## 6. Event Mapping

| VB6 | Web |
|-----|-----|
| Form_Load | `GET /config` + init grid/payment combo |
| TxtDocID_Validate | `GET /documents/{prod_id}` |
| TxtID_Validate | `GET /suppliers/{id}` |
| CmdAddTrans / VGrid_DblClick | Open detail modal |
| Fin_PurD CmdSave | Client grid update + Calc_Rate |
| CmdDiscount | Discount/charges modal (Fin_PurDed) |
| UpdateBalance / CalDiscount | Client totals recalculation |
| CmdSave_Click | `POST /documents` |
| CmdDelete_Click | `DELETE /documents/{prod_id}` |
| CmdClear / clearform | Client reset |
| EnterKeyEnable | Enter → next tab stop |
| Form_KeyUp | Same |

---

## 7. CRUD Mapping

| Op | Behaviour |
|----|-----------|
| Create | Blank DocID → new prod_id + serial |
| Read | Load header + lines by prod_id |
| Update | Reverse old + rewrite master/detail/GL/stock |
| Delete | Reverse stock/GL + delete Pur_M/D, ldgr, gl0002/3 |
| Search | Supplier / item / barcode lookups |
| Refresh | Reload after save if checkDetailData |

---

## 8. API / Backend Logic

See `app/services/fin_pur_service.py` — mirrors CmdSave / CmdDelete / Validate.  
Permissions: `inventory.fin_pur.view|create|edit|delete`.

---

## 9. SQL Queries Used

Documented in repository: SELECT/INSERT/UPDATE/DELETE on tables listed above; `MAX(prod_id)`; `gc0002` serial; `DELETE FROM FIN_PUR_D WHERE ITEM_ID = 0`.

---

## 10. Files Created

- `docs/VB6_FIN_PUR_MODERNIZATION.md`
- `docs/vb6_source/Fin_Pur/*` (source copies + analysis)
- `app/schemas/fin_pur.py`
- `app/repositories/fin_pur_repository.py`
- `app/services/fin_pur_service.py`
- `app/api/v1/fin_pur.py`
- `app/templates/admin/fin_pur.html`
- `app/static/js/fin_pur.js`
- `app/static/css/fin_pur.css`
- `scripts/seed_fin_pur_permissions.py`

---

## 11. Folder Structure

```
app/
  api/v1/fin_pur.py
  repositories/fin_pur_repository.py
  services/fin_pur_service.py
  schemas/fin_pur.py
  templates/admin/fin_pur.html
  static/js/fin_pur.js
  static/css/fin_pur.css
docs/VB6_FIN_PUR_MODERNIZATION.md
scripts/seed_fin_pur_permissions.py
```

---

## 12. Testing Checklist

- [ ] Open screen with view permission  
- [ ] New GRN: supplier → add lines → discount modal → save → PUR number  
- [ ] Reload by GRN ID; edit line; save  
- [ ] Posted document blocked  
- [ ] Delete with confirm; stock/GL reversed  
- [ ] Duplicate item rejected  
- [ ] Fiscal date out of range rejected  
- [ ] Book permission denied message  
- [ ] Totals match VB6 UpdateBalance / CalDiscount  
- [ ] Enter key advances fields  

---

## 13. Missing Dependencies

- **Pur Order**, **Upload/Download image**, **Print Grid**, **Show Item stock grid**, **Check (CalculateWeeklyReorderLevel)** — UI present; full file/print/stock-browse parity may need follow-up if binary `.frx` assets or Crystal reports are required.  
- **Fin_PurDed** recreated as modal (no separate page).  
- Legacy `cUPwordStr` bit flags mapped to JWT permissions (not bit-string).

---

## 14. Assumptions

1. `cSTaxType = 1` for this deployment (from `GLModule2` company select) — not stored in `gsetup`.  
2. `MFiscal = 0` always (Form_Load).  
3. Delete/edit rights use web permissions instead of `cUPwordStr` mid positions.  
4. `VOUCHER_LEGACY_UID` / user preference `legacy_contpl_uid` used for `gc0002` / book ACL (same as voucher entry).
