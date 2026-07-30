# Two sites: app.ahsteellab.com + erp.ahsteellab.com

Two **separate** deployments, two **separate** PCs, two **separate** Cloudflare tunnels.

```
                    Cloudflare (ahsteellab.com)
                              |
            +-----------------+-----------------+
            |                                   |
   app.ahsteellab.com                 erp.ahsteellab.com
            |                                   |
     Tunnel: ahsteellab-app              Tunnel: ahsteellab-erp
            |                                   |
   PC 1: ahsteellab-auth                 PC 2: ahsteellab-nsds2626
   DB: SHAHEENHPLT / NAHSL2627           DB: shahenhp / nsds2626
```

No router port forwarding. Each PC runs its own app + cloudflared.

---

## Site 1 — app.ahsteellab.com (original)

**Folder:** `ahsteellab-auth`  
**PC:** Your original/dev machine  
**Database:** `SHAHEENHPLT\SQLEXPRESS` / `NAHSL2627`

```powershell
cd D:\CursorProject\ahsteellab-auth
copy .env.production.example .env
# Edit .env: BASE_URL=https://app.ahsteellab.com, DB settings, secrets

.\deploy\setup-cloudflare.ps1
.\deploy\start-production.ps1
```

Always-on (Admin PowerShell):
```powershell
.\deploy\install-services.ps1
```

Login: https://app.ahsteellab.com/login

---

## Site 2 — erp.ahsteellab.com (NSDS2626)

**Folder:** `ahsteellab-nsds2626`  
**PC:** New app machine  
**Database:** `shahenhp` / `nsds2626` (remote SQL)

```powershell
cd D:\CursorProject\ahsteellab-nsds2626
copy .env.production.example .env
# Edit .env: BASE_URL=https://erp.ahsteellab.com
# Set DB_SERVER to working value (e.g. shahenhp\SQLEXPRESS)
python install\generate_env.py --force
install\set-db-server.bat

.\deploy\setup-cloudflare.ps1
.\deploy\start-production.ps1
```

Always-on (Admin PowerShell):
```powershell
.\deploy\install-services.ps1
```

Login: https://erp.ahsteellab.com/login  
Item Master: https://erp.ahsteellab.com/admin/fin-item-classic

---

## Cloudflare DNS (automatic)

`setup-cloudflare.ps1` on each PC creates:

| PC | Tunnel name | Hostname |
|---|---|---|
| PC 1 | `ahsteellab-app` | `app.ahsteellab.com` |
| PC 2 | `ahsteellab-erp` | `erp.ahsteellab.com` |

Both use local port **8000** on their own PC — no conflict.

---

## Production .env checklist

### app.ahsteellab.com
```env
BASE_URL=https://app.ahsteellab.com
FRONTEND_URL=https://app.ahsteellab.com
CORS_ORIGINS=https://app.ahsteellab.com
HOST=127.0.0.1
SECURE_COOKIES=true
APP_ENV=production
DEBUG=false
```

### erp.ahsteellab.com
```env
BASE_URL=https://erp.ahsteellab.com
FRONTEND_URL=https://erp.ahsteellab.com
CORS_ORIGINS=https://erp.ahsteellab.com
HOST=127.0.0.1
SECURE_COOKIES=true
APP_ENV=production
DEBUG=false
```

---

## Important

- Run `setup-cloudflare.ps1` **once per PC** (not once total).
- Do **not** put both hostnames in one `config.yml` unless both apps run on the **same** PC on different ports.
- Each site needs its own `SECRET_KEY` and `CSRF_SECRET_KEY` in `.env`.
