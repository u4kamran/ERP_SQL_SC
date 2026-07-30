# Deploy AH Steel Lab Online with Cloudflare Tunnel

This guide publishes the app at **https://app.ahsteellab.com** while keeping SQL Server on your local Windows machine (`SHAHEENHPLT\SQLEXPRESS`).

The existing **https://ahsteellab.com** (Al Haram Reports) site is unchanged.

---

## Architecture

```
Browser  -->  Cloudflare (HTTPS)  -->  cloudflared tunnel  -->  FastAPI :8000  -->  SQL Server
              app.ahsteellab.com         (this PC)              (127.0.0.1)
```

No router port forwarding required. Cloudflare provides free SSL.

---

## Prerequisites

- Windows PC with SQL Server running (`SHAHEENHPLT\SQLEXPRESS`)
- Domain **ahsteellab.com** on Cloudflare (orange cloud / proxied)
- Python venv installed (`pip install -r requirements.txt`)
- Auth database seeded (`sql/01`–`05`, `python -m scripts.seed_database`)

---

## Step 1 — One-time Cloudflare setup

Open **PowerShell** in the project folder:

```powershell
cd D:\CursorProject\ahsteellab-auth
.\deploy\setup-cloudflare.ps1
```

This script will:

1. Download `cloudflared` to `deploy/cloudflared/bin/`
2. Open browser to log in to Cloudflare — select **ahsteellab.com**
3. Create tunnel `ahsteellab-app`
4. Add DNS: `app.ahsteellab.com` → tunnel
5. Write `deploy/cloudflared/config.yml`

---

## Step 2 — Configure production `.env`

If `.env` was not created automatically:

```powershell
copy .env.production.example .env
```

Edit `.env` and set:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `BASE_URL` | `https://app.ahsteellab.com` |
| `FRONTEND_URL` | `https://app.ahsteellab.com` |
| `HOST` | `127.0.0.1` |
| `SECURE_COOKIES` | `true` |
| `CORS_ORIGINS` | `https://app.ahsteellab.com` |
| `SECRET_KEY` | 64+ random characters |
| `CSRF_SECRET_KEY` | 32+ random characters |
| `DB_PASSWORD` | your SQL Server password |

Generate secrets in PowerShell:

```powershell
[Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## Step 3 — Start (manual test)

```powershell
.\deploy\start-production.ps1
```

Two windows open: FastAPI app + Cloudflare tunnel.

Open: **https://app.ahsteellab.com/login**

Default admin: `admin` / `ChangeMe@2026!`

FIN_ITEM admin: **https://app.ahsteellab.com/admin/fin-items**

---

## Step 4 — Always-on (Windows services)

Run **PowerShell as Administrator**:

```powershell
.\deploy\install-services.ps1
```

This installs:

- **cloudflared** as a Windows service (tunnel)
- **AHSteelLab-App** scheduled task (FastAPI at startup)

---

## URLs

| Page | URL |
|---|---|
| Login | https://app.ahsteellab.com/login |
| Dashboard | https://app.ahsteellab.com/dashboard |
| FIN_ITEM CRUD | https://app.ahsteellab.com/admin/fin-items |
| API docs | https://app.ahsteellab.com/api/docs |
| Health | https://app.ahsteellab.com/health |
| Reports (unchanged) | https://ahsteellab.com |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| 502 Bad Gateway | App not running — check `python run.py` or scheduled task |
| 404 on admin pages | Restart app after code updates |
| Login works locally but not online | Check `BASE_URL`, `SECURE_COOKIES=true`, re-login |
| 403 on FIN_ITEM | Run `python -m scripts.seed_inventory_permissions`, re-login |
| Tunnel not connecting | `Get-Service cloudflared` — restart service |
| DNS not resolving | Cloudflare dashboard → DNS → `app` CNAME to tunnel |

### Check tunnel status

```powershell
.\deploy\cloudflared\bin\cloudflared.exe tunnel info ahsteellab-app
```

### View logs

- App: `logs/app.log`
- Tunnel: Windows Event Viewer → Application → cloudflared

---

## Security notes

- FastAPI binds to `127.0.0.1` only — not exposed directly to the internet
- Change default admin password after first login
- Keep `.env` secret — never commit to git
- SQL Server stays on local machine; only the web app is tunneled

---

## Rollback

Stop services:

```powershell
Stop-ScheduledTask -TaskName AHSteelLab-App
.\deploy\cloudflared\bin\cloudflared.exe service uninstall
```

Remove DNS record `app.ahsteellab.com` in Cloudflare dashboard if needed.
