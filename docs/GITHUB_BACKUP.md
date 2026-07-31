# GitHub Backup — AH Steel Lab (NSDS2626)

This project is backed up on GitHub so you can recover the full source code after any disaster.

| Item | Value |
|---|---|
| Repository | [github.com/u4kamran/ERP_SQL_SC](https://github.com/u4kamran/ERP_SQL_SC) |
| Clone URL | `https://github.com/u4kamran/ERP_SQL_SC.git` |
| Default branch | `main` |

---

## What is backed up

- Application source (`app/`, `scripts/`, `sql/`, etc.)
- Install scripts (`install/`, `INSTALL.bat`, `START-APP.bat`, …)
- Documentation (`docs/`, `README.md`)
- Example config (`.env.example`, `.env.production.example`)

## What is NOT backed up (by design)

These stay on your PC only — never commit them:

| Path | Reason |
|---|---|
| `.env` | Passwords and secret keys |
| `venv/` | Recreated by `install\install.bat` |
| `logs/` | Runtime logs |
| `data/` | Scheduler/sync state |
| `deploy/cloudflared/config.yml` | Tunnel credentials |

---

## First-time push (already done on initial setup)

If you need to push from a fresh clone:

```powershell
cd D:\CursorProject\ahsteellab-nsds2626
git remote add origin https://github.com/u4kamran/ERP_SQL_SC.git
git branch -M main
git push -u origin main
```

Git will ask for GitHub login (browser or personal access token).

---

## Daily backup — save changes to GitHub

**Easy way:** Double-click **`BACKUP-TO-GITHUB.bat`** in the project folder.  
It shows changed files, asks for a message, then commits and pushes to GitHub.

**Manual way** (PowerShell):

```powershell
cd D:\CursorProject\ahsteellab-nsds2626

git status
git add -A
git commit -m "Brief description of what you changed"
git push erpsqlsc main
```

**Tip:** Back up at least once per week, or after every important change.

---

## Restore on a new PC from GitHub

```powershell
cd D:\CursorProject
git clone https://github.com/u4kamran/ERP_SQL_SC.git ahsteellab-nsds2626
cd ahsteellab-nsds2626
```

Then follow **[DISASTER_RECOVERY.md](DISASTER_RECOVERY.md)** — Part A (database) and Part B (`install\install.bat`).

---

## Create your own private backup repo (optional)

If you prefer a separate private repository:

1. On GitHub: **New repository** → name e.g. `ahsteellab-nsds2626-backup` → **Private**.
2. On your PC:

```powershell
cd D:\CursorProject\ahsteellab-nsds2626
git remote add backup https://github.com/YOUR_USERNAME/ahsteellab-nsds2626-backup.git
git push -u backup main
```

You can push to both `origin` and `backup` whenever you run `git push`.

---

## GitHub Personal Access Token (if password login fails)

GitHub no longer accepts account passwords for `git push`. Use a token:

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens**
2. Generate token with `repo` scope
3. When Git asks for password, paste the token

---

## Related

- [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) — full install and DB name changes
