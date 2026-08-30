# OTP / SMS Master Control

Central administrator switch for OTP SMS on **web** (guest chat) and **mobile** (customer app).

The backend is the source of truth. Clients must not decide locally whether OTP is required.

## Effective rule

```text
OTP_ALLOWED = MASTER_OTP_ENABLED AND CHANNEL_OTP_ENABLED
```

| Master | Web | Mobile | Web OTP | Mobile OTP |
| ------ | --- | ------ | ------- | ---------- |
| OFF    | ON  | ON     | OFF     | OFF        |
| ON     | OFF | ON     | OFF     | ON         |
| ON     | ON  | OFF    | ON      | OFF        |
| ON     | ON  | ON     | ON      | ON         |
| OFF    | OFF | OFF    | OFF     | OFF        |

Master OFF always overrides channel ON.

## Database

Business database (`nsds2626` on ERP):

```text
dbo.otp_sms_control   (single row, id = 1)
```

| Column | Meaning |
| ------ | ------- |
| `master_otp_enabled` | Global OTP SMS master |
| `web_otp_enabled` | Guest web chat / public WhatsApp OTP |
| `mobile_otp_enabled` | Customer mobile app OTP |
| `row_version` | Optimistic concurrency |
| `updated_by_user_id` / `updated_by_username` | Last administrator |
| `updated_at` | Last change |
| `comment` | Optional reason |

Defaults for a new row (and new installations): all **ON**, matching current production OTP behavior (`CUSTOMER_APP_OTP_REQUIRED` / `GUEST_MOBILE_OTP_REQUIRED`).

SQL: `sql/28_create_otp_sms_control.sql`

Permissions (auth DB): `sql/29_seed_otp_sms_control_permissions.sql`

Setup:

```bash
venv\Scripts\python.exe scripts\setup_otp_sms_control.py --site erp
```

Administrators must **re-login** so JWT permissions include the new codes.

## Channel identification

The server does **not** trust a client `channel` field.

| Channel | OTP service | Public APIs |
| ------- | ----------- | ----------- |
| **web** | `MobileOtpService` | `/api/v1/public/whatsapp/mobile-otp/*` |
| **mobile** | `CustomerAppOtpService` | `/api/v1/public/customer-app/mobile-otp/*` |

## API

Admin (JWT + permission):

```text
GET  /api/v1/auth/security/otp-settings    auth.otp_sms_control.view
PUT  /api/v1/auth/security/otp-settings    auth.otp_sms_control.manage
```

PUT body:

```json
{
  "master_enabled": true,
  "web_enabled": true,
  "mobile_enabled": true,
  "row_version": 1,
  "comment": "optional reason"
}
```

If another administrator saved first, PUT returns **409**. Reload and retry.

Public (no admin flags):

```text
GET /api/v1/public/whatsapp/mobile-otp/status
GET /api/v1/public/customer-app/mobile-otp/status
```

Response includes `required` / `otp_required` (effective for that channel only).

## When OTP is disabled

The OTP service:

- does **not** generate an OTP
- does **not** store an OTP hash
- does **not** insert `SMS_DB_`
- does **not** mark the user as authenticated (`verified` stays `false`)

`require_verified()` is skipped, so cart save / customer register can continue using the existing non-OTP identity (mobile number), as before when env OTP was off.

Request OTP response example:

```json
{
  "ok": true,
  "otp_required": false,
  "verified": false,
  "message": "OTP verification is not required."
}
```

## When OTP is enabled

Unchanged:

```text
Generate OTP → hash in customer_app_otp (mobile) or mobile_otp.json (web)
→ INSERT SMS_DB_ (STATUS=1) → existing SendSMSActive sender
```

## Web UI

- Admin page: `/admin/otp-sms-control`
- Sidebar: Administration → **OTP / SMS Control**
- Guest chat reads `/mobile-otp/status` on load (not a hardcoded client flag)

Disabling a switch shows a confirmation dialog. Master OFF uses a stronger warning.

## Mobile app

Ask the backend:

```text
GET /api/v1/public/customer-app/mobile-otp/status
```

If `otp_required` is `false`, do not show the OTP screen. Do not hard-code the decision in React Native.

## Permissions

| Code | Use |
| ---- | --- |
| `auth.otp_sms_control.view` | Open the control panel |
| `auth.otp_sms_control.manage` | Save changes |

Seeded to `SUPER_ADMIN` and `ADMIN`.

## Audit

Every successful save writes `auth.AuditLogs`:

- Action: `OTP_SMS_CONTROL_CHANGED`
- Old / new JSON (master, web, mobile, version)
- User id, username, IP, user agent
- No OTP codes or passwords

## Caching

In-process cache, **5 seconds**, cleared immediately on save in the worker that handled PUT. Other workers refresh within 5 seconds. No app rebuild or restart is required.

## Fail-safe

If `otp_sms_control` cannot be read (table missing, DB error):

- OTP is treated as **required** (do not silently turn OTP off)
- Request-OTP APIs return **503**: `Unable to determine OTP configuration. Please try again.`

## SMS

Uses existing `nsds2626.dbo.SMS_DB_` only. No second gateway.

## Test matrix

1. Master ON, Web ON, Mobile ON → both OTP ON  
2. Master ON, Web OFF, Mobile ON → web OFF, mobile ON  
3. Master ON, Web ON, Mobile OFF → web ON, mobile OFF  
4. Master OFF, Web ON, Mobile ON → both OFF (no `SMS_DB_` insert)  
5. Master OFF, Web OFF, Mobile OFF → both OFF  

SQL check after a disabled request:

```sql
SELECT TOP 20 * FROM dbo.SMS_DB_ ORDER BY ID DESC;
SELECT TOP 20 * FROM dbo.customer_app_otp ORDER BY id DESC;
```
