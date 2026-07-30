# AH Steel Lab — NSDS2626 Site (shahenhp)

Separate deployment for SQL Server **shahenhp**, business DB **nsds2626**, auth DB **NSDS2626_AUTH**.

> Original project (unchanged): `d:\CursorProject\ahsteellab-auth`  
> Install guide: [README-NSDS2626.md](README-NSDS2626.md)

---

# AH Steel Lab — Phase 1: Enterprise Authentication System

Production-ready authentication foundation for the future AH Steel Lab ERP web application. This phase replaces VB6 desktop login functionality while keeping the legacy **nsds2626** business database completely untouched.

---

## Database Architecture Recommendation

### Option A: Separate Authentication Database (`NSDS2626_AUTH`) — **RECOMMENDED**

| Advantages | Disadvantages |
|---|---|
| Complete isolation from VB6 production data | Two databases to manage |
| Zero risk of altering legacy tables | Future cross-DB joins need explicit linking |
| Independent backup/restore for auth | Slightly more complex connection config |
| Separate security permissions at DB level | |
| Auth schema can evolve without DBA approval on prod DB | |
| Failed migration cannot affect VB6 app | |

### Option B: Separate Schema in Existing Database (`nsds2626.auth`)

| Advantages | Disadvantages |
|---|---|
| Single database connection for future ERP | Same backup file as production data |
| Easier joins to business tables later | Any DDL mistake risks production |
| Simpler deployment (one DB) | DBA may resist changes on prod DB |
| | VB6 and web app share same DB instance load |

### Decision: **Separate Database (`NSDS2626_AUTH`)**

This is the enterprise-standard approach when migrating from a legacy system. The VB6 application continues using **nsds2626** unchanged. All authentication tables live in **NSDS2626_AUTH** on SQL Server `shahenhp`.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2 |
| Frontend | HTML5, Bootstrap 5, Jinja2, JavaScript |
| Database | SQL Server 2008, ODBC Driver 18 |
| Auth | JWT (access + refresh), BCrypt, RBAC |
| Security | CSRF, CORS, Security Headers, Audit Logging |

---

## Project Structure

```
ahsteellab-auth/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── api/
│   │   ├── deps.py          # Auth dependencies (JWT, permissions)
│   │   └── v1/              # REST API v1 endpoints
│   │       ├── auth.py      # Login, logout, password
│   │       ├── users.py     # User CRUD (admin)
│   │       ├── roles.py     # Role management
│   │       ├── permissions.py
│   │       ├── sessions.py  # Session management
│   │       ├── audit.py     # Audit log viewer
│   │       └── profile.py   # User profile & preferences
│   ├── config/
│   │   └── settings.py      # Environment-based configuration
│   ├── database/
│   │   ├── base.py          # SQLAlchemy base + audit mixins
│   │   └── session.py       # Engine and session factory
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic layer
│   ├── security/            # JWT, BCrypt, CSRF
│   ├── middleware/          # Security headers, CSRF
│   ├── templates/           # Jinja2 HTML templates
│   ├── static/              # CSS, JS assets
│   ├── utils/               # IP detection, user-agent parsing
│   └── logging/             # Application logger
├── sql/                     # SQL Server DDL scripts
├── alembic/                 # Database migrations
├── scripts/
│   └── seed_database.py     # Admin user seed
├── tests/                   # Unit tests
├── docs/                    # Detailed documentation
├── requirements.txt
├── .env.example
└── run.py
```

---

## Quick Start

### Install on another PC (shahenhp / nsds2626)

Copy this folder (`ahsteellab-nsds2626`, without `venv`), then on the new computer:

1. `install\setup-database.bat` — create auth DB `NSDS2626_AUTH` on shahenhp (one time)
2. `install\install.bat` — install Python packages and seed admin user
3. `install\start.bat` — run the app

See [install/SETUP-SHAHENHP.txt](install/SETUP-SHAHENHP.txt) or [README-NSDS2626.md](README-NSDS2626.md).

### 1. Prerequisites

- Python 3.13+ (3.14 compatible)
- SQL Server (`shahenhp`)
- [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### 2. Install Dependencies

```bash
cd ahsteellab-nsds2626
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your database credentials and secrets.

### 4. Create Database

Run SQL scripts in order via SQL Server Management Studio:

```
sql/01_create_database.sql
sql/02_create_schema.sql
sql/03_create_tables.sql
sql/04_create_indexes.sql
sql/05_seed_data.sql
```

### 5. Seed Admin User

```bash
python -m scripts.seed_database
```

**Default credentials:**
- Username: `admin`
- Password: `ChangeMe@2026!` (must change on first login)

### 6. Run Application

```bash
python run.py
```

- Login page: http://localhost:8000/login
- API docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

---

## Cloudflare Production Deployment

To publish online at **https://app.ahsteellab.com** (Cloudflare Tunnel):

```powershell
.\deploy\setup-cloudflare.ps1      # one-time: login, tunnel, DNS
copy .env.production.example .env   # edit secrets
.\deploy\start-production.ps1       # test run
.\deploy\install-services.ps1       # always-on (run as Admin)
```

Full guide: [docs/CLOUDFLARE_DEPLOY.md](docs/CLOUDFLARE_DEPLOY.md)

---

| Variable | Development | Production |
|---|---|---|
| `APP_ENV` | `development` | `production` |
| `BASE_URL` | `http://localhost:8000` | `https://ahsteellab.com` |
| `SECURE_COOKIES` | `false` | `true` |
| `CORS_ORIGINS` | `http://localhost:8000` | `https://ahsteellab.com` |

No source code changes are needed between environments — only `.env` values change.

---

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/login` | User login |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Logout and revoke tokens |
| POST | `/change-password` | Change password |
| POST | `/forgot-password` | Request password reset |
| POST | `/reset-password` | Confirm password reset |

### Users (`/api/v1/users`)

| Method | Endpoint | Permission Required |
|---|---|---|
| GET | `/` | `auth.users.view` |
| POST | `/` | `auth.users.create` |
| GET | `/{id}` | `auth.users.view` |
| PUT | `/{id}` | `auth.users.update` |
| DELETE | `/{id}` | `auth.users.delete` |

### Roles (`/api/v1/roles`)

| Method | Endpoint | Permission Required |
|---|---|---|
| GET | `/` | `auth.roles.view` |
| POST | `/` | `auth.roles.manage` |
| PUT | `/{id}` | `auth.roles.manage` |

### Permissions (`/api/v1/permissions`)

| Method | Endpoint | Permission Required |
|---|---|---|
| GET | `/` | `auth.permissions.view` |

### Sessions (`/api/v1/sessions`)

| Method | Endpoint | Permission Required |
|---|---|---|
| GET | `/` | `auth.sessions.view` |
| DELETE | `/{id}` | `auth.sessions.revoke` |

### Audit (`/api/v1/audit`)

| Method | Endpoint | Permission Required |
|---|---|---|
| GET | `/` | `auth.audit.view` |

### Profile (`/api/v1/profile`)

| Method | Endpoint | Permission Required |
|---|---|---|
| GET | `/` | `auth.profile.view` |
| PUT | `/` | `auth.profile.update` |
| PUT | `/preferences` | Authenticated |

---

## Login Flow

```
1. User submits username + password
2. Validate credentials (BCrypt)
3. Check account status (active, not deleted)
4. Check account lock (failed attempts)
5. Check password expiry
6. Enforce concurrent session limit
7. Generate JWT access token (30 min)
8. Generate JWT refresh token (7 days / 30 days remember-me)
9. Save active session to database
10. Record login history (IP, browser, device)
11. Record audit log entry
12. Set secure HTTP-only cookies
13. Redirect to dashboard
```

---

## Security Features

- **JWT Access + Refresh Tokens** with JTI revocation blacklist
- **BCrypt** password hashing (12 rounds)
- **RBAC** with roles, permissions, modules, and features
- **Account lockout** after 5 failed attempts (30 min)
- **Password policy** (length, complexity, history, expiry)
- **CSRF protection** via cookie tokens
- **Security headers** (CSP, X-Frame-Options, etc.)
- **Cloudflare support** (CF-Connecting-IP, X-Forwarded-For/Proto)
- **Audit trail** for all critical operations
- **SQL injection prevention** via SQLAlchemy parameterized queries

---

## Cloudflare / Reverse Proxy

The application detects real client IP and HTTPS status from:

1. `CF-Connecting-IP` (Cloudflare)
2. `X-Forwarded-For`
3. `X-Forwarded-Proto`
4. `CF-Visitor`

Set `TRUST_PROXY_HEADERS=true` in production behind Cloudflare Tunnel or any reverse proxy.

---

## Running Tests

```bash
pytest
```

---

## Rollback

To remove the authentication database entirely:

```
sql/99_rollback.sql
```

This does **not** affect the legacy `nsds2626` database.

---

## Phase 1 Scope

This phase implements **authentication only**. Business modules (Inventory, Sales, POS, etc.) will be added in future phases after approval.

---

## Documentation

See `docs/` for detailed guides:

- [Database Design](docs/DATABASE.md)
- [API Reference](docs/API.md)
- [Security Architecture](docs/SECURITY.md)
- [Authentication Flow](docs/AUTH_FLOW.md)
