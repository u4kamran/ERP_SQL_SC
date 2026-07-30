# API Reference

Base URL: `{BASE_URL}/api/v1`

Authentication: Bearer token in `Authorization` header or `access_token` cookie.

---

## POST /auth/login

Authenticate user.

**Request:**
```json
{
  "username": "admin",
  "password": "ChangeMe@2026!",
  "remember_me": false
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "must_change_password": true
}
```

**Errors:** 401 (invalid credentials), 403 (inactive), 423 (locked)

---

## POST /auth/refresh

**Request:**
```json
{ "refresh_token": "eyJ..." }
```

**Response (200):** Same as login response.

---

## POST /auth/logout

Requires authentication.

**Response (200):**
```json
{ "message": "Logged out successfully.", "success": true }
```

---

## POST /auth/change-password

**Request:**
```json
{
  "current_password": "ChangeMe@2026!",
  "new_password": "NewSecure@Pass123"
}
```

---

## POST /auth/forgot-password

**Request:**
```json
{ "email": "user@example.com" }
```

Always returns success message (prevents email enumeration).

---

## GET /users/

List users. Requires `auth.users.view`.

**Query params:** `skip`, `limit`

---

## POST /users/

Create user (admin only). Requires `auth.users.create`.

**Request:**
```json
{
  "username": "jdoe",
  "email": "jdoe@ahsteellab.com",
  "password": "TempPass@123",
  "first_name": "John",
  "last_name": "Doe",
  "role_ids": [3]
}
```

---

## GET /profile/

Get current user profile with roles, permissions, and preferences.

---

## GET /sessions/

List current user's active sessions.

---

## DELETE /sessions/{session_id}

Force revoke a session. Requires `auth.sessions.revoke`.

---

## GET /audit/

List audit logs. Requires `auth.audit.view`.

**Query params:** `skip`, `limit`, `user_id`

---

## GET /health

Public health check endpoint.

**Response:**
```json
{ "status": "healthy", "app": "AH Steel Lab", "env": "development" }
```
