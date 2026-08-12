# VB6 Purchase Order Modernization — Fin_InvM_Order

**VB6 source:** `Fin_InvM_Order.frm`  
**Web path:** `/admin/fin-inv-order` · **API:** `/api/v1/fin-inv-order`

## Overview

Supplier-centric **Purchase Order** form (`doc_type_id = 33`). Uses `fin_inv_m_order` / `fin_inv_d_order` on the live SQL Server database — no schema changes.

## Key differences from Purchase Receipt (Fin_PurM)

| | Fin_PurM (GRN) | Fin_InvM_Order (PO) |
|--|----------------|---------------------|
| Doc type | 2 | 33 |
| Party | Supplier | Supplier (vendor_id) |
| Master key | `prod_id` | `inv_id` |
| Line entry | Modal Fin_PurD | Inline grid `grd(0)` |
| Line disc columns | Full tax/disc/DOI | Disc % / D.Amt / Net only |
| DB disc mapping | Multiple columns | `stax_rate` / `stax_amt` / `total_amt` |
| Inventory on save | Yes | No (commented in VB6) |
| Inventory on delete | Yes (Fin_Pur) | **No** (web — PO never posts stock) |

## Permissions

Seed with:

```bash
python scripts/seed_fin_inv_order_permissions.py
```

Or run `sql/21_seed_fin_inv_order_permissions.sql` on the auth database.

| Permission | Purpose |
|------------|---------|
| `inventory.fin_inv_order.view` | Open, load, search |
| `inventory.fin_inv_order.create` | Save new PO |
| `inventory.fin_inv_order.edit` | Edit PO, supplier catalog |
| `inventory.fin_inv_order.delete` | Delete PO |

Users must **re-login** after seeding permissions.

## Navigation

- Sidebar: **Inventory → Purchase Order**
- Dashboard: **Inventory & Sales → Purchase Order (VB6)**

## Files

- `app/schemas/fin_inv_order.py`
- `app/repositories/fin_inv_order_repository.py`
- `app/services/fin_inv_order_service.py`
- `app/api/v1/fin_inv_order.py`
- `app/templates/admin/fin_inv_order.html`
- `app/static/js/fin_inv_order.js`
- `app/static/css/fin_inv_order.css`
- `scripts/seed_fin_inv_order_permissions.py`
- `sql/21_seed_fin_inv_order_permissions.sql`

## Delete behaviour

Delete removes PO master/detail rows and any linked `fin_ldgr` / `gl0002` / `gl0003` records. It **does not** modify `fin_item` stock — consistent with save (no inventory posting on PO).
