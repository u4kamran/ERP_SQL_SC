# Disaster Recovery — Install on Another Computer

This guide restores **AH Steel Lab (NSDS2626)** after hardware failure, PC replacement, or when moving to a new machine. You can recover from **GitHub** or by **copying the project folder**.

---

## What you need before starting

| Requirement | Notes |
|---|---|
| Windows PC | App runs on Windows (Python + SQL Server ODBC) |
| Python 3.13+ | [python.org/downloads](https://www.python.org/downloads/) — tick **Add Python to PATH** |
| ODBC Driver 18 for SQL Server | [Microsoft download](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) |
| SQL Server access | Server `shahenhp` (or your server name/IP) |
| Business database | `nsds2626` (existing VB6 data — usually already on SQL Server) |
| Auth database | `NSDS2626_AUTH` (created by setup scripts if missing) |
| Network | App PC must reach SQL Server on TCP port **1433** |

**Do not copy these from the old PC** (recreate on the new PC):

- `venv/` — Python virtual environment (rebuilt by install)
- `.env` — contains secrets; copy manually and edit, or regenerate with `install\install.bat`
- `logs/`, `data/` — runtime files (optional; not required to run)

---

## Method 1 — Clone from GitHub (recommended backup)

GitHub URL: **https://github.com/u4kamran/ERP_SQL_SC**

### On the new computer

```powershell
# 1. Install Git from https://git-scm.com/download/win (if not installed)

# 2. Clone the backup
cd D:\CursorProject
git clone https://github.com/u4kamran/ERP_SQL_SC.git ahsteellab-nsds2626
cd ahsteellab-nsds2626

# 3. Follow "Quick install" below (Part A + Part B)
```

### Keep GitHub backup up to date (on your working PC)

```powershell
cd D:\CursorProject\ahsteellab-nsds2626
git add -A
git status
git commit -m "Backup: describe what changed"
git push origin main
```

Run this after important changes so the online copy stays current.

---

## Method 2 — Copy folder from USB / old PC

1. Copy the whole folder `ahsteellab-nsds2626` to the new PC (e.g. `D:\AHSteelLab\`).
2. **Exclude** `venv\` (large; will be recreated).
3. Copy `.env` separately if you still have it (or create a new one — see below).
4. Follow **Quick install** below.

---

## Quick install (both methods)

### Part A — Database (one time, on SQL Server machine)

If `NSDS2626_AUTH` already exists on SQL Server (normal after first setup), **skip Part A**.

**Option 1 — SQL Server Management Studio (easiest)**

On the database server, run these files **in order**:

```
sql\01_create_database.sql
sql\02_create_schema.sql
sql\03_create_tables.sql
sql\04_create_indexes.sql
sql\05_seed_data.sql
sql\07_seed_gl_ledger_permissions.sql
sql\08_seed_sms_email_scheduler_permissions.sql
```

**Option 2 — Batch script (from any PC with `sqlcmd` + network to SQL Server)**

```bat
install\setup-database.bat
```

Confirm both databases exist:

- `nsds2626` — business data (VB6)
- `NSDS2626_AUTH` — web login / permissions

---

### Part B — Application (on the app PC)

1. Install **Python 3.13+** and **ODBC Driver 18**.
2. Open Command Prompt in the project folder.
3. Run:

```bat
install\install.bat
```

This will:

- Create `.env` from `install\env.shahenhp` (if missing)
- Create `venv` and install `requirements.txt`
- Test SQL Server connections
- Seed admin user

4. Start the app:

```bat
install\start.bat
```

Or double-click **`START-APP.bat`** / **`START-WEBSITE.bat`** (production + Cloudflare).

5. Open browser: **http://localhost:8000/login**

| Field | Default |
|---|---|
| Username | `admin` |
| Password | `ChangeMe@2026!` |

Change the password on first login.

---

## Production / Cloudflare (optional)

If the site was online at `https://app.ahsteellab.com`:

1. Copy or recreate `.env` from `.env.production.example`.
2. Run `INSTALL.bat` or follow `docs\CLOUDFLARE_DEPLOY.md`.
3. Run `deploy\setup-cloudflare.ps1` once (tunnel + DNS).
4. Use `START-WEBSITE.bat` or `INSTALL-SERVICES.bat` (run as Administrator) for auto-start.

---

## Restore database from backup (.bak)

If you use **SYNC-DATABASE.bat** or **SYNC-LAN-DATABASE.bat**, restore SQL backups on the new SQL Server first, then point `.env` at the restored server and database names.

See `.env.example` section `SYNC_*` for remote backup share settings.

---

## Changing database names

Yes — you can change database names. How easy it depends on **which** database.

### Business database (`BUSINESS_DB_NAME`)

**Easy — change only `.env`:**

```env
BUSINESS_DB_NAME=your_new_business_db
BUSINESS_DB_SERVER=your_sql_server
```

The application reads this at startup. No code changes needed.

Restart the app after editing `.env`.

### Auth database (`DB_NAME`)

**Mostly easy — change `.env`:**

```env
DB_NAME=YOUR_NEW_AUTH_DB
DB_SERVER=your_sql_server
```

**If you are creating a brand-new auth database** (not restoring an existing one), the SQL scripts under `sql\` currently use the name `NSDS2626_AUTH`. Either:

1. **Recommended:** Keep auth DB name `NSDS2626_AUTH` (simplest), or  
2. **Rename in scripts:** Find/replace `NSDS2626_AUTH` with your new name in:
   - `sql\01_create_database.sql`
   - `sql\02_create_schema.sql` through `sql\08_*.sql`
   - `sql\99_rollback.sql` (if rolling back)

Then run Part A setup again on SQL Server.

**If you only restore an existing `.bak`** with a different name, set `DB_NAME` in `.env` to match the restored database name — no script edits needed.

### SQL Server instance (`DB_SERVER`)

Edit `.env`:

```env
DB_SERVER=shahenhp
# or IP:
DB_SERVER=192.168.1.50
```

If business DB is on a different server:

```env
BUSINESS_DB_SERVER=192.168.1.51
```

### Summary

| Setting | File | Code change needed? |
|---|---|---|
| Auth DB name | `.env` → `DB_NAME` | Only if creating DB from `sql\` scripts with a new name |
| Business DB name | `.env` → `BUSINESS_DB_NAME` | No |
| SQL Server host | `.env` → `DB_SERVER` / `BUSINESS_DB_SERVER` | No |
| SQL login/password | `.env` → `DB_USER`, `DB_PASSWORD` | No |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Cannot connect to SQL Server | Check `ping` to server; TCP/IP enabled; firewall port 1433; correct `DB_SERVER` / password in `.env` |
| `NSDS2626_AUTH` missing | Run Part A (SQL scripts) on database server |
| `ODBC Driver 18` not found | Install Microsoft ODBC Driver 18 for SQL Server |
| Item master empty | Verify `BUSINESS_DB_NAME=nsds2626` and business DB has data on SQL Server |
| Port 8000 in use | Change `PORT=` in `.env` or stop other app using 8000 |
| App not reachable on LAN | Allow port 8000 in Windows Firewall on app PC; use `http://app-pc-ip:8000` |

Test database connection manually:

```bat
install\test-db-connection.bat
```

---

## Checklist — full disaster recovery

- [ ] SQL Server running with `nsds2626` data (restore from backup if needed)
- [ ] Auth DB `NSDS2626_AUTH` exists (run `sql\` scripts or restore `.bak`)
- [ ] Project cloned from GitHub or copied from backup (without `venv`)
- [ ] `.env` created with correct `DB_SERVER`, `DB_NAME`, `BUSINESS_DB_NAME`, passwords
- [ ] `install\install.bat` completed successfully
- [ ] `install\start.bat` — login page loads
- [ ] Admin password changed from default
- [ ] (Optional) Cloudflare tunnel and services reinstalled

---

## Related docs

- [README-NSDS2626.md](../README-NSDS2626.md) — site overview
- [install/SETUP-SHAHENHP.txt](../install/SETUP-SHAHENHP.txt) — two-machine setup
- [GITHUB_BACKUP.md](GITHUB_BACKUP.md) — backup and push procedure
- [CLOUDFLARE_DEPLOY.md](CLOUDFLARE_DEPLOY.md) — public website deployment
