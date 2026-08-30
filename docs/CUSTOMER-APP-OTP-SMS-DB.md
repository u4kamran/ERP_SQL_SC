# Customer App OTP via SMS_DB_ (recommended defaults)

## Policy

- **One-time mobile ownership proof** (verified ~30 days), **not** OTP on every cart or invoice.
- Saving a cart is **not** a sales invoice.
- Delivery uses existing **`dbo.SMS_DB_`** queue — no new SMS gateway.

## Conventions (from live data)

| Field | Value |
|-------|--------|
| `STATUS` | `1` = pending queue → sender sets `0` after process |
| `SUBJECT` | `NIL` |
| `RECIPIENT` | `92` + last 10 digits |
| `SENDER` | Modem/SIM — default `923004017067` (`CUSTOMER_APP_OTP_SMS_SENDER`) |
| `SENT` | `GETDATE()` at insert (NOT NULL) |

## Flow

```text
Request OTP → hash in customer_app_otp → INSERT SMS_DB_ (STATUS=1) → COMMIT
→ launch `consoleapp2_lock.exe` (SendSMSActive) → Verify OTP → VERIFIED for 30 days
→ Register / Save Cart
```

## Security

- Crypto OTP (`secrets`), SHA-256 hash + salt, never plain OTP in DB
- Never return OTP in API (except local `test` + `CUSTOMER_APP_OTP_DEV_ECHO`)
- Cooldown 45s, max 3 requests / 15 min, max 5 attempts, one-time use, supersede old PENDING
- Masked mobile in logs

## Settings

| Setting | Default |
|---------|---------|
| `CUSTOMER_APP_OTP_REQUIRED` | env fallback only; live switch is [OTP Master Control](OTP-MASTER-CONTROL.md) |
| `CUSTOMER_APP_OTP_PROVIDER` | `sms_db` (`test` only for local) |
| `CUSTOMER_APP_OTP_TTL_SECONDS` | `300` |
| `CUSTOMER_APP_OTP_VERIFIED_DAYS` | `30` |
| `CUSTOMER_APP_OTP_SMS_SENDER` | `923004017067` |
| `CUSTOMER_APP_OTP_SMS_SENDER_EXE` | `\\shaheenhp\Backup\localfiles\SendSMSActive\consoleapp2_lock.exe` |

## Setup

```bash
venv\Scripts\python.exe scripts\setup_customer_app_otp.py
```

Restart ERP app process after deploy.
