# Security Architecture

## Authentication

### JWT Access Token
- Algorithm: HS256
- Expiry: 30 minutes (configurable)
- Payload: user_id, username, roles, permissions, session_id, jti
- Stored in HTTP-only cookie and returned in API response

### JWT Refresh Token
- Expiry: 7 days (30 days with Remember Me)
- Stored hashed in database
- Rotation supported via ReplacedByTokenId

### Token Revocation
- JTI stored in `auth.RevokedTokens` on logout
- Refresh tokens marked `IsRevoked` in database
- Sessions marked `IsRevoked` with reason

## Password Security

### Hashing
- BCrypt with 12 rounds (configurable via `BCRYPT_ROUNDS`)

### Policy (configurable)
- Minimum 8 characters
- Uppercase, lowercase, digit, special character required
- Cannot reuse last 5 passwords
- Expires after 90 days

### Account Lockout
- 5 failed attempts → 30 minute lockout
- Counter resets on successful login

## Authorization (RBAC)

```
User → UserRoles → Role → RolePermissions → Permission
```

Permissions checked via FastAPI dependency `require_permission("auth.users.view")`.

Super admin has `auth.admin.full` which grants all permissions.

## CSRF Protection

- CSRF token generated on GET requests
- Stored in cookie (`csrftoken`)
- Validated on state-changing form submissions

## Security Headers

| Header | Value |
|---|---|
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| X-XSS-Protection | 1; mode=block |
| Referrer-Policy | strict-origin-when-cross-origin |
| Content-Security-Policy | Restricted to self + CDN |

## Cookie Security

| Setting | Development | Production |
|---|---|---|
| HttpOnly | true | true |
| Secure | false | true |
| SameSite | lax | lax |

## Cloudflare Integration

Real client IP resolution order:
1. `CF-Connecting-IP`
2. `X-Forwarded-For` (first IP)
3. `X-Real-IP`
4. Direct connection IP

HTTPS detection via `X-Forwarded-Proto` and `CF-Visitor`.

## SQL Injection Prevention

All database queries use SQLAlchemy ORM with parameterized statements. No raw SQL in application code.

## XSS Prevention

- Jinja2 auto-escaping enabled
- Content-Security-Policy headers
- Input validation via Pydantic schemas

## Audit Logging

All critical events logged to `auth.AuditLogs`:
- LOGIN / LOGOUT
- PASSWORD_CHANGE
- USER_CREATE / USER_UPDATE / USER_DELETE
- Session revocation

Login attempts (success and failure) logged to `auth.LoginHistory` with IP, browser, device, and OS.
