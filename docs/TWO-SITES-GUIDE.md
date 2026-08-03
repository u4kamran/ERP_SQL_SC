# Two Sites — Shafique Center + Al Haram Steel Lab

Run the **same ERP application** as two independent sites. Each site has its own database, domain, Cloudflare tunnel, and `.env` file.

```
                    Cloudflare (ahsteellab.com)
                              |
            +-----------------+-----------------+
            |                                   |
   erp.ahsteellab.com                 arp.ahsteellab.com
            |                                   |
     Tunnel: ahsteellab-erp              Tunnel: ahsteellab-arp
            |                                   |
   PC / Folder: ERP site                 PC / Folder: ARP site
   DB: shahenhp / nsds2626              DB: shahenhp / nahsl2627
   Port: 8000                           Port: 8001
```

| | Shafique Center | Al Haram Steel Lab |
|---|---|---|
| **Site code** | `erp` | `arp` |
| **Public URL** | https://erp.ahsteellab.com | https://arp.ahsteellab.com |
| **Business DB** | `nsds2626` | `nahsl2627` |
| **Auth DB** | `NSDS2626_AUTH` | `NAHSL2627_AUTH` |
| **SQL Server** | `shahenhp` | `shahenhp` (same server) |
| **Tunnel name** | `ahsteellab-erp` | `ahsteellab-arp` |

No router port forwarding. Each site runs its own app + `cloudflared` tunnel.

---

## This machine — same SQL Server, two folders

Both sites run on **this PC** and connect to the **same SQL Server** (`shahenhp`). Only the **database names** differ.

| | Shafique Center | Al Haram Steel Lab |
|---|---|---|
| Folder | `ahsteellab-nsds2626` (this repo) | `ahsteellab-arp` (clone) |
| Port | 8000 | 8001 |
| Business DB | `nsds2626` | `nahsl2627` |
| Auth DB | `NSDS2626_AUTH` | `NAHSL2627_AUTH` |
| SQL Server | `shahenhp` | `shahenhp` |

### Folder 1 — Shafique Center (ERP)

```bat
cd D:\CursorProject\ahsteellab-nsds2626
INSTALL-ERP.bat
SETUP-ERP.bat
START-ERP.bat
```

Login: https://erp.ahsteellab.com/login

### Folder 2 — Al Haram Steel Lab (ARP)

```bat
CLONE-ARP-SITE.bat
cd D:\CursorProject\ahsteellab-arp
INSTALL-ARP.bat
SETUP-ARP-DATABASE.bat
SETUP-ARP.bat
START-ARP.bat
```

Login: https://arp.ahsteellab.com/login

Both can run at the same time — ERP on port **8000**, ARP on port **8001**.

### Keep reports identical on both sites

ERP (`ahsteellab-nsds2626`) is the **main copy** for new reports and features. After changes here:

```bat
SYNC-CODE-TO-ARP.bat
```

Or use `START-ALL.bat` — it syncs code to ARP automatically before starting both sites.

ARP keeps its own `.env`, database (`nahsl2627`), and Cloudflare tunnel config. Only **application code** is copied.

---

## Alternative: Two separate PCs

---

## Step-by-step (each site)

### 1. Install Python packages + create `.env`

| Site | Command |
|---|---|
| Shafique Center | `INSTALL-ERP.bat` |
| Al Haram Steel Lab | `INSTALL-ARP.bat` |

This creates `venv`, installs packages, and generates `.env` with random security keys.

**Edit `.env`** and set `DB_PASSWORD` (and verify `DB_SERVER` if your SQL Server name differs).

### 2. One-time Cloudflare setup

| Site | Command |
|---|---|
| Shafique Center | `SETUP-ERP.bat` |
| Al Haram Steel Lab | `SETUP-ARP.bat` |

Browser opens for Cloudflare login. Select the `ahsteellab.com` zone. DNS is created automatically.

### 3. Start the site

| Site | Command |
|---|---|
| Shafique Center | `START-ERP.bat` |
| Al Haram Steel Lab | `START-ARP.bat` |

Keep the window open. To stop: `STOP-APP.bat`.

### 4. Check status

| Site | Command |
|---|---|
| Shafique Center | `CHECK-ERP.bat` |
| Al Haram Steel Lab | `CHECK-ARP.bat` |

### 5. Always-on (optional, run as Administrator)

```powershell
# On ERP PC:
.\deploy\install-site-services.ps1 -Site erp

# On ARP PC:
.\deploy\install-site-services.ps1 -Site arp
```

---

## Database setup

Each site needs **two databases** on SQL Server:

| Site | Auth database | Business database |
|---|---|---|
| ERP | `NSDS2626_AUTH` | `nsds2626` |
| ARP | `NAHSL2627_AUTH` | `nahsl2627` |

If auth databases do not exist yet, create them:

| Site | Command |
|---|---|
| ERP | `install\setup-database.bat` |
| ARP | `SETUP-ARP-DATABASE.bat` |

This creates `NAHSL2627_AUTH` on `shahenhp` with tables, roles, and default admin user.

Default login after seed: **admin** / **ChangeMe@2026!**

---

## Same PC — both sites (this machine)

Both sites use the **same SQL Server** (`shahenhp`) with different databases. Each site is in its own folder.

1. **ERP folder** (`ahsteellab-nsds2626`) — port 8000, database `nsds2626`
2. **ARP folder** (`ahsteellab-arp`) — port 8001, database `nahsl2627`

Run `START-ERP.bat` and `START-ARP.bat` from their respective folders. Both can run together.

`STOP-APP.bat` stops cloudflared for both — restart each site with its own `START-*.bat` if needed.

---

## Site configuration files

All site settings live in `deploy\sites\`:

- `deploy\sites\erp.json` — Shafique Center
- `deploy\sites\arp.json` — Al Haram Steel Lab

Environment templates:

- `install\env.erp` — production `.env` for ERP
- `install\env.arp` — production `.env` for ARP

Regenerate `.env` manually:

```bat
venv\Scripts\python.exe install\generate_env.py --site erp --force
venv\Scripts\python.exe install\generate_env.py --site arp --force
```

---

## Important rules

1. Run `SETUP-ERP.bat` / `SETUP-ARP.bat` **once per PC** (not once total).
2. Each site needs its own `SECRET_KEY` and `CSRF_SECRET_KEY` (auto-generated by install).
3. Do **not** put both hostnames in one `config.yml` unless both apps run on the same PC on different ports.
4. `STOP-APP.bat` stops cloudflared — if both sites run on one PC, stopping one stops the tunnel for both. Use separate PCs when possible.

---

## Quick reference

| Action | ERP (Shafique) | ARP (Al Haram) |
|---|---|---|
| Sync code to ARP | `SYNC-CODE-TO-ARP.bat` | (receives copy from ERP) |
| Install | `INSTALL-ERP.bat` | `INSTALL-ARP.bat` |
| Cloudflare setup | `SETUP-ERP.bat` | `SETUP-ARP.bat` |
| Start | `START-ERP.bat` | `START-ARP.bat` |
| Check | `CHECK-ERP.bat` | `CHECK-ARP.bat` |
| URL | https://erp.ahsteellab.com | https://arp.ahsteellab.com |
| Database | `nsds2626` | `nahsl2627` |
