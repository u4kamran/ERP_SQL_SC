# Database Design

## Overview

All authentication tables reside in database **NSDS2626_AUTH**, schema **auth**. The legacy business database **nsds2626** is never modified.

## Standard Columns

Every table includes these audit columns:

| Column | Type | Purpose |
|---|---|---|
| CreatedDate | DATETIME | Record creation timestamp (UTC) |
| CreatedBy | INT | User ID who created the record |
| ModifiedDate | DATETIME | Last modification timestamp |
| ModifiedBy | INT | User ID who last modified |
| IsActive | BIT | Soft enable/disable flag |
| IsDeleted | BIT | Soft delete flag |
| RowVersion | ROWVERSION | Optimistic concurrency control |

## Tables

### auth.Modules

ERP module registry for future expansion (Inventory, Sales, POS, etc.).

| Column | Type | Description |
|---|---|---|
| ModuleId | INT PK | Auto-increment primary key |
| ModuleCode | NVARCHAR(50) | Unique code (e.g., INVENTORY) |
| ModuleName | NVARCHAR(100) | Display name |
| Description | NVARCHAR(500) | Module description |
| DisplayOrder | INT | Sort order in UI |
| IconClass | NVARCHAR(100) | Bootstrap icon class |

### auth.Features

Sub-features within modules (e.g., USERS under AUTH module).

### auth.Permissions

Granular permissions using dot notation: `module.feature.action`

Examples: `auth.users.view`, `auth.roles.manage`, `auth.admin.full`

### auth.Roles

Role definitions: SUPER_ADMIN, ADMIN, USER (seeded by default).

### auth.RolePermissions

Many-to-many mapping between roles and permissions.

### auth.Users

| Column | Type | Description |
|---|---|---|
| UserId | INT PK | Primary key |
| Username | NVARCHAR(100) | Unique login name |
| Email | NVARCHAR(255) | Unique email address |
| PasswordHash | NVARCHAR(255) | BCrypt hash |
| MustChangePassword | BIT | Force change on next login |
| PasswordExpiryDate | DATETIME | Password expiration |
| FailedLoginAttempts | INT | Counter for lockout |
| LockoutEndDate | DATETIME | Account lock expiry |
| LastLoginDate | DATETIME | Last successful login |
| LastLoginIp | NVARCHAR(45) | Last login IP address |

### auth.UserRoles

Many-to-many mapping between users and roles.

### auth.UserSessions

Active session tracking with device/browser/IP information.

### auth.RefreshTokens

Refresh token storage with revocation support.

### auth.RevokedTokens

JWT JTI blacklist for access and refresh token revocation.

### auth.PasswordHistory

Stores previous password hashes to prevent reuse.

### auth.PasswordResetTokens

Email-ready password reset token storage.

### auth.LoginHistory

Every login attempt (success and failure) with device details.

### auth.AuditLogs

Comprehensive audit trail for all critical operations.

### auth.UserPreferences

Key-value user preferences (theme, language, timezone).

## Entity Relationship

```
Modules 1──* Features
Modules 1──* Permissions
Features 1──* Permissions
Roles *──* Permissions (via RolePermissions)
Users *──* Roles (via UserRoles)
Users 1──* UserSessions
Users 1──* RefreshTokens
Users 1──* PasswordHistory
Users 1──* UserPreferences
Users 1──* LoginHistory
```

## Indexes

Performance indexes are created on:
- User lookup (IsActive, IsDeleted)
- Session queries (UserId, IsRevoked, ExpiresAt)
- Token hash lookups
- Audit log queries (UserId, Action, CreatedDate)
- Login history (UserId, Username, CreatedDate)

## Seed Data

Pre-seeded modules for all future ERP areas:
AUTH, DASHBOARD, INVENTORY, PURCHASE, SALES, ACCOUNTS, POS, PAYROLL, HR, PRODUCTION, CRM, REPORTS

Default roles: SUPER_ADMIN, ADMIN, USER

Default admin: username `admin`, password `ChangeMe@2026!`
