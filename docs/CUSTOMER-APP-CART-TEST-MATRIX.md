# Customer App Cart — Test Matrix (Phase 1.5)

## Customer mobile

| # | Scenario | Expected |
|---|----------|----------|
| C1 | New mobile → register + save | CUST_SMS created; cart `SAVED`; ref `CART-…` |
| C2 | Existing mobile → save | Reuses CUST_SMS; no duplicate customer |
| C3 | Duplicate mobile register | Message: already registered; no second row |
| C4 | Add / qty / remove products | Local cart updates; validate refreshes prices |
| C5 | Save cart | ERP header + lines + history `CART_CREATED` |
| C6 | Save twice (same idempotency key) | One cart; second returns same ref |
| C7 | Save twice (new key) | Two carts OK (same customer) |
| C8 | Network fail mid-save | No partial cart (transaction rollback) |
| C9 | OTP required, not verified | 403; cart not saved |
| C10 | My Saved Carts | Only this mobile’s carts |
| C11 | Open another customer’s ref | 404 |
| C12 | App restart | Local cart restored; saved carts from API |

## ERP staff

| # | Scenario | Expected |
|---|----------|----------|
| E1 | Menu Customer App Carts | Visible with `marketing.customer_app_carts.view` |
| E2 | List / search / filter / dates | Server-side; paginated |
| E3 | Open cart | Customer + lines + totals + history |
| E4 | Status Under Review / Contacted / Confirm | History row written |
| E5 | Cancel | Requires cancel permission |
| E6 | Convert | 501; status unchanged |
| E7 | Unauthorized user | 403 / menu hidden |
| E8 | WhatsApp WO orders | Unchanged; not listed here |

## Data integrity

| # | Check | Expected |
|---|-------|----------|
| D1 | Stock after save | Unchanged |
| D2 | GL / invoice after save | None created |
| D3 | Orphan lines | None (FK + single transaction) |
| D4 | Partial header | None |
| D5 | Duplicate customers same mobile key | Blocked |

## Manual smoke (after setup)

1. Run `python scripts/setup_customer_app_carts.py`
2. Restart ERP
3. Mobile: add item → Save cart → OTP if required → note `CART-…`
4. ERP: Admin → Customer App Carts → find ref → change status
5. Confirm WhatsApp Bot / delivery / sales screens still work
