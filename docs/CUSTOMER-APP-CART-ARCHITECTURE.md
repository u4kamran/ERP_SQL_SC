# Customer App Cart — Architecture (Phase 1.5)

## Business rule

**Saving a cart is not creating a sales invoice.**

| Concept | Meaning |
|--------|---------|
| Customer cart (phone) | Local shopping basket (Zustand + AsyncStorage) |
| Saved Customer App Cart | ERP SQL record for store review (`MOBILE_APP`) |
| WhatsApp `WO-…` | Guest/WhatsApp chat orders (JSON) — separate |
| Sales invoice | Formal ERP sale (`FIN_INV_M`) — Phase 2 convert |

Saving a cart does **not** post stock, GL, or accounting.

## Existing ERP reuse

- **Customer master:** `dbo.CUST_SMS` (name, mobile, address). Mobile match uses last-10-digit key; stored as `03XXXXXXXXX`.
- **Catalog / price / stock check:** existing public catalog validate (no stock post).
- **OTP:** `MobileOtpService` (hashed codes; WhatsApp delivery when configured).
- **Not reused:** `data/whatsapp_orders.json`, WhatsApp Bot admin UI.

## Database (business DB `nsds2626`)

| Table | Role |
|-------|------|
| `customer_app_cart_seq` | Daily sequence for `CART-YYYYMMDD-NNNN` |
| `customer_app_carts` | Header + unique `idempotency_key` |
| `customer_app_cart_lines` | Snapshot lines |
| `customer_app_cart_status_history` | Audit |

Source: always `MOBILE_APP`.

Statuses: `SAVED` → `UNDER_REVIEW` → `CONTACTED` → `CONFIRMED` (+ `CANCELLED` / `EXPIRED`; `CONVERTED` reserved).

## APIs

### Public (`/api/v1/public/customer-app`)

- `POST /mobile-otp/send|verify`, `GET /mobile-otp/status`
- `POST /customers/lookup`, `POST /customers/register`
- `POST /carts` (idempotent save)
- `GET /carts?mobile=`, `GET /carts/{cart_ref}?mobile=`

Identity: verified mobile (when OTP required). Never trust a client-supplied `cust_id` for authorization; carts are scoped by `mobile_key`.

### Staff (`/api/v1/marketing/customer-app-carts`)

- `GET /`, `GET /{id}`
- `PUT /{id}/status`
- `POST /{id}/convert` → **501 stub** (no sales-invoice API yet)

Permissions: `marketing.customer_app_carts.view|update|cancel|convert`

## ERP UI

Admin → **Customer App Carts** (`/admin/customer-app-carts`) — not under WhatsApp Bot.

## Mobile app (`ahsteellab-sds-customer`)

Flow: Browse → Cart → **Save cart** → Register/OTP if needed → Confirm → ERP reference → My Saved Carts.

## Convert (Phase 2)

Architecture prepared; endpoint returns 501 until a real sales-order create path exists. Double-convert must be prevented when implemented (status `CONVERTED` + unique doc ref).

## Setup

```bash
python scripts/setup_customer_app_carts.py
```

Then restart the ERP app process so routes load.
