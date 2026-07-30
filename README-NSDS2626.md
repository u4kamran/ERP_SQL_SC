# AH Steel Lab — NSDS2626 Site (shahenhp)

**Separate deployment copy** for SQL Server `shahenhp` and business database `nsds2626`.

The original project remains at `d:\CursorProject\ahsteellab-auth` (NAHSL2627 / SHAHEENHPLT).

| Setting | Value |
|---|---|
| SQL Server | `shahenhp` |
| Business DB | `nsds2626` |
| Auth DB | `NSDS2626_AUTH` |
| SQL user | `sa` |

## Quick install on another PC

1. Copy this whole folder (`ahsteellab-nsds2626`) to the new computer (without `venv`)
2. Run `install\setup-database.bat` — creates `NSDS2626_AUTH` on shahenhp (one time)
3. Run `install\install.bat` — Python packages + admin user
4. Run `install\start.bat` — start app

Login: `http://localhost:8000/login`  
Username: `admin`  
Password: `ChangeMe@2026!`

Full steps: [install/SETUP-SHAHENHP.txt](install/SETUP-SHAHENHP.txt)

## GitHub backup & disaster recovery

| Doc | Purpose |
|---|---|
| [docs/GITHUB_BACKUP.md](docs/GITHUB_BACKUP.md) | Push/pull code backup on GitHub |
| [docs/DISASTER_RECOVERY.md](docs/DISASTER_RECOVERY.md) | Install on another PC; change DB names |

**Clone backup:** `git clone https://github.com/u4kamran/ERP_SQL_SC.git`

---
