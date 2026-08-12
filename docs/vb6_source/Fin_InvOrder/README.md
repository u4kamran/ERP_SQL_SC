# Fin_InvM_Order — VB6 Reverse Engineering & Web Migration

**VB6 source:** `E:\AccesToSQL_Barcode_20130316 - SI_BC_AutoInv_WholeSaleQty_V1_JanDec\Fin_InvM_Order.frm`  
**Web route:** `/admin/fin-inv-order`  
**API prefix:** `/api/v1/fin-inv-order`

## Summary

`Fin_InvM_Order` is the **Purchase Order** form (`doc_type_id = 33`). It is a supplier-centric variant of `Fin_InvM` (sales invoice, doc_type 21).

| Aspect | Value |
|--------|-------|
| Master table | `fin_inv_m_order` |
| Detail table | `fin_inv_d_order` |
| Number sequence | `fin_inv_no_order` via `NextInvNoOrder()` |
| Primary grid | `grd(0)` — inline line entry with line discount |
| Save buffer | Hidden `VGrid` — maps disc %/amt/net to `stax_rate`/`stax_amt`/`total_amt` |
| Print view | `v_inv1Order` → ActiveReports `LstInvStore_shortOrder` |

## Critical DB mapping (line discount)

VB6 stores **line discount** in columns originally named for sales tax:

| VGrid col | UI column | DB column |
|-----------|-----------|-----------|
| 5 | Amount (gross) | `sale_amt` |
| 6 | Disc % | `stax_rate` |
| 7 | D. Amt | `stax_amt` |
| 8 | Net Amt | `total_amt` |

Master `sale_amt` = header **net** total (`LblNetInvoice`), not gross.

## Save workflow (VB6 CmdSave_Click)

1. Validate grid: no zero qty, no blank items, no zero net
2. `cmdNewValues_Click` — sync `grd(0)` → `VGrid`
3. `CalDiscount` — `LblNetInvoice = T_Amount - header_discount + header_charges`
4. Date range + not-future validation
5. Supplier / cash-sales address validation
6. If editing: `DELETE fin_inv_d_order WHERE serial_no`
7. Upsert `fin_inv_m_order` (new: `NextInvNoOrder()` + `nSerialNo()`)
8. `DELETE fin_ldgr`, `DELETE gl0003` by serial
9. Insert `fin_inv_d_order` lines from VGrid
10. GL/inventory posting **commented out** in VB6 for this form

## Delete workflow (VB6 CmdDelete_Click)

1. DELETE `fin_inv_d_order`, `fin_inv_m_order`, `fin_ldgr`, `gl0003`, `gl0002`
2. **Does not update `fin_item` stock** (web implementation — PO save also skips inventory posting)

## Web implementation

| Layer | File |
|-------|------|
| Schemas | `app/schemas/fin_inv_order.py` |
| Repository | `app/repositories/fin_inv_order_repository.py` |
| Service | `app/services/fin_inv_order_service.py` |
| API | `app/api/v1/fin_inv_order.py` |
| UI | `app/templates/admin/fin_inv_order.html` |
| JS | `app/static/js/fin_inv_order.js` |
| CSS | `app/static/css/fin_inv_order.css` |
| Permissions | `sql/21_seed_fin_inv_order_permissions.sql` |

## Deployment

1. Run `sql/21_seed_fin_inv_order_permissions.sql` on `NSDS2626_AUTH`
2. Ensure business DB connection points to live SQL Server (existing `fin_inv_m_order` tables)
3. Open `/admin/fin-inv-order` after login with `inventory.fin_inv_order.view`

## Permissions

- `inventory.fin_inv_order.view` — open form, load, search
- `inventory.fin_inv_order.create` — save new PO
- `inventory.fin_inv_order.edit` — edit existing PO, supplier catalog
- `inventory.fin_inv_order.delete` — delete PO

## API endpoints

| Method | Path | VB6 equivalent |
|--------|------|----------------|
| GET | `/config` | Form_Load |
| GET | `/documents/{inv_id}` | TxtDocID_Validate |
| POST | `/documents` | CmdSave_Click |
| DELETE | `/documents/{inv_id}` | CmdDelete_Click |
| GET | `/next-id` | Label1_Click / NextInvNoOrder preview |
| GET | `/suppliers/{id}` | TxtCustID_Validate |
| GET | `/suppliers/{id}/items` | CmdShowItem_Click |
| POST | `/suppliers/{id}/items` | cmdAddItem_Click |
| GET | `/items/by-manual/{id}` | grd_AfterEdit DtlManualid |
| GET | `/items/by-barcode/{code}` | grd_AfterEdit DtlBarcodeid |
| GET | `/items/{id}/history` | callPurSaleHistory |
| GET | `/suppliers/{id}/po-history` | PurchasOrderHistory |
| GET | `/print/{inv_id}` | cmdPrint_Click |

## Validations preserved

- Item must exist in `V_FIN_STOCK_SUPPLIER` for selected supplier
- No duplicate items on same PO
- Zero qty / zero net / zero rate blocked
- Fiscal date range and not-future date
- Cash Un-Reg. requires title, address, city
- Posted documents (`sys_status = 1`) read-only
