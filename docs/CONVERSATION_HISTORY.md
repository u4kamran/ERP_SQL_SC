# Conversation History — GitHub Backup & Disaster Recovery

**Project:** AH Steel Lab (NSDS2626)  
**Folder:** `D:\CursorProject\ahsteellab-nsds2626`  
**GitHub:** https://github.com/u4kamran/ERP_SQL_SC  
**Date:** July 30–31, 2026  

This file records what was discussed and implemented in Cursor chat, so you can read the full history anytime without searching old chats.

---

## Session 1 — Original Request

**You asked for:**

1. Create a backup of this programme on GitHub
2. Create a procedure to install/use this code on another computer (disaster recovery — copy/paste and run)
3. Explain if database names can be changed easily

---

## What Was Done (Session 1)

### 1. GitHub backup created

- Git repository was initialized but had **no commits**
- Remote was already set: `erpsqlsc` → `https://github.com/u4kamran/ERP_SQL_SC.git`
- **First commit** created: 207 files (app, SQL, install scripts, docs)
- **Pushed to GitHub** on branch `main`

**What is backed up on GitHub:**
- Application source (`app/`, `scripts/`, `sql/`, etc.)
- Install scripts (`install/`, `INSTALL.bat`, `START-APP.bat`, etc.)
- Documentation (`docs/`, `README.md`)
- Example config (`.env.example`, `.env.production.example`)

**What is NOT backed up (by design — stays on your PC only):**
| Path | Reason |
|---|---|
| `.env` | Passwords and secret keys |
| `venv/` | Recreated by `install\install.bat` |
| `logs/` | Runtime logs |
| `data/` | Scheduler/sync state |
| `deploy/cloudflared/config.yml` | Tunnel credentials |

### 2. Disaster recovery documentation

Two guides were created:

| File | Purpose |
|---|---|
| `docs/DISASTER_RECOVERY.md` | Full install on another PC; DB name changes; troubleshooting |
| `docs/GITHUB_BACKUP.md` | How to push/pull backup on GitHub |

`README-NSDS2626.md` was updated with links to these docs.

### 3. `.gitignore` updated

Added exclusions for temp/duplicate files:
- `_tmp_*.py`
- `install_/`

---

## Disaster Recovery — Quick Reference

### Method A — Clone from GitHub (recommended)

```powershell
cd D:\CursorProject
git clone https://github.com/u4kamran/ERP_SQL_SC.git ahsteellab-nsds2626
cd ahsteellab-nsds2626
```

### Method B — Copy folder from USB / old PC

1. Copy whole folder (do **not** copy `venv\`)
2. Copy `.env` separately if you have it

### Then on the new PC

**Part A — Database (one time, if auth DB missing):**
- Run `sql\01` through `sql\05` in SSMS on SQL Server, **or**
- Run `install\setup-database.bat`

**Part B — Application:**
```bat
install\install.bat
install\start.bat
```

**Login:** http://localhost:8000/login  
**Username:** `admin`  
**Password:** `ChangeMe@2026!`

Full details: `docs\DISASTER_RECOVERY.md`

---

## Changing Database Names

**Yes — mostly easy via `.env` only:**

```env
DB_SERVER=shahenhp
DB_NAME=NSDS2626_AUTH
BUSINESS_DB_NAME=nsds2626
BUSINESS_DB_SERVER=shahenhp
DB_USER=sa
DB_PASSWORD=your_password
```

| Setting | File | Code change needed? |
|---|---|---|
| Auth DB name | `.env` → `DB_NAME` | Only if creating new DB from `sql\` scripts with a different name |
| Business DB name | `.env` → `BUSINESS_DB_NAME` | No |
| SQL Server host | `.env` → `DB_SERVER` / `BUSINESS_DB_SERVER` | No |
| SQL login/password | `.env` → `DB_USER`, `DB_PASSWORD` | No |

**Exception:** If you create a **new** auth database from `sql\` scripts with a different name, find/replace `NSDS2626_AUTH` in all `sql\*.sql` files first.

---

## Session 2 — Git Tutorial Request

**You asked:**
- Can we create git from main / can we change it now?
- Teach me everything that was done

### Git vs GitHub (simple explanation)

| Term | Meaning |
|---|---|
| **Git** | Version control on your PC — saves snapshots |
| **GitHub** | Online backup of those snapshots |
| **Commit** | One saved snapshot with a message |
| **Push** | Upload commits PC → GitHub |
| **Clone** | Download from GitHub → new PC |
| **Branch** | Separate line of work; yours is `main` |

### Your current Git setup

```
Branch:     main
Remote:     erpsqlsc  →  https://github.com/u4kamran/ERP_SQL_SC.git
Commits:    1 initial commit (a89411e)
```

**Note:** Remote is named `erpsqlsc` (not `origin`). Use:
```powershell
git push erpsqlsc main
```

### Daily workflow (manual commands)

```powershell
cd D:\CursorProject\ahsteellab-nsds2626
git status
git add -A
git commit -m "Describe what you changed"
git push erpsqlsc main
```

### Creating a branch from main (optional, safer for big changes)

```powershell
git checkout -b my-new-feature
# make changes...
git add -A
git commit -m "Added new feature"
git push erpsqlsc my-new-feature

# When ready, merge back:
git checkout main
git merge my-new-feature
git push erpsqlsc main
```

### Git commands cheat sheet

| Command | What it does |
|---|---|
| `git status` | Show changed files |
| `git add -A` | Stage all changes |
| `git commit -m "message"` | Save snapshot locally |
| `git push erpsqlsc main` | Upload to GitHub |
| `git pull erpsqlsc main` | Download latest from GitHub |
| `git log --oneline` | Show commit history |
| `git diff` | Show what changed in files |

---

## Session 3 — BACKUP-TO-GITHUB.bat

**You said:** yes (to creating a one-click backup script)

### File created: `BACKUP-TO-GITHUB.bat`

**How to use:**
1. Double-click `BACKUP-TO-GITHUB.bat`
2. See list of changed files
3. Enter a short commit message (or press Enter for auto date/time message)
4. Script commits and pushes to GitHub automatically

**If push fails:** GitHub needs a Personal Access Token (not account password):
1. GitHub → Settings → Developer settings → Personal access tokens
2. Create token with `repo` scope
3. Paste token when Git asks for password

`docs/GITHUB_BACKUP.md` and `README-NSDS2626.md` were updated to mention this batch file.

---

## Architecture Reminder

```
┌─────────────────────────────────────────────────────────┐
│  YOUR PC                                                │
│  D:\CursorProject\ahsteellab-nsds2626                   │
│                                                         │
│  Edit code → BACKUP-TO-GITHUB.bat (or git push)         │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│  GITHUB                                                 │
│  https://github.com/u4kamran/ERP_SQL_SC                 │
│  (code only — no passwords)                             │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼  disaster / new PC
┌─────────────────────────────────────────────────────────┐
│  NEW PC                                                 │
│  git clone → install\install.bat → install\start.bat    │
└─────────────────────────────────────────────────────────┘
```

### Databases

| Database | Name | Purpose |
|---|---|---|
| Business | `nsds2626` | VB6 legacy data (items, GL, etc.) |
| Auth | `NSDS2626_AUTH` | Web login, users, permissions |
| SQL Server | `shahenhp` | Database machine |

---

## Important Files

| File | Purpose |
|---|---|
| `BACKUP-TO-GITHUB.bat` | One-click backup to GitHub |
| `install\install.bat` | Install app on new PC |
| `install\start.bat` | Start the app |
| `install\setup-database.bat` | Create auth DB on SQL Server |
| `START-WEBSITE.bat` | Production + Cloudflare |
| `.env` | Real passwords (PC only) |
| `.env.example` | Template for settings |
| `docs/DISASTER_RECOVERY.md` | Full disaster recovery guide |
| `docs/GITHUB_BACKUP.md` | GitHub backup guide |
| `docs/CONVERSATION_HISTORY.md` | This file |

---

## Pending Items (as of last session)

These files were modified locally but may not yet be on GitHub — run `BACKUP-TO-GITHUB.bat` to upload:

- `.env.lan.example`
- `SETUP-MACHINE2-SHARE.bat`
- `SYNC-LAN-DATABASE.bat`
- `scripts/run_lan_db_sync.py`
- `BACKUP-TO-GITHUB.bat` (new)
- `docs/CONVERSATION_HISTORY.md` (this file)
- `docs/GITHUB_BACKUP.md` (updated)
- `README-NSDS2626.md` (updated)

Suggested commit message: `Added backup script and conversation history docs`

---

## How to Keep This File Updated

After future Cursor chats about this project, you can ask:

> "Add today's conversation to docs/CONVERSATION_HISTORY.md"

Or append a new section yourself with date and what was discussed.

---

*Last updated: July 31, 2026*
