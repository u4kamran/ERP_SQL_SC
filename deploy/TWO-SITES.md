# Two sites: erp.ahsteellab.com + arp.ahsteellab.com

Two **separate** deployments, two **separate** PCs (recommended), two **separate** Cloudflare tunnels.

```
                    Cloudflare (ahsteellab.com)
                              |
            +-----------------+-----------------+
            |                                   |
   erp.ahsteellab.com                 arp.ahsteellab.com
            |                                   |
     Tunnel: ahsteellab-erp              Tunnel: ahsteellab-arp
            |                                   |
   Shafique Center                      Al Haram Steel Lab
   DB: shahenhp / nsds2626              DB: shahenhp / nahsl2627
```

See full guide: **docs/TWO-SITES-GUIDE.md**

---

## Site 1 — erp.ahsteellab.com (Shafique Center)

**Folder:** `ahsteellab-nsds2626` (this repo)  
**Database:** `shahenhp` / `nsds2626` + `NSDS2626_AUTH`

```bat
INSTALL-ERP.bat
SETUP-ERP.bat
START-ERP.bat
```

Login: https://erp.ahsteellab.com/login

---

## Site 2 — arp.ahsteellab.com (Al Haram Steel Lab)

**Folder:** `ahsteellab-arp` (clone this repo to a second folder on **same PC**)  
**Database:** `shahenhp` / `nahsl2627` + `NAHSL2627_AUTH` (same SQL Server as ERP)

```bat
git clone https://github.com/u4kamran/ERP_SQL_SC.git ahsteellab-arp
cd ahsteellab-arp
INSTALL-ARP.bat
SETUP-ARP-DATABASE.bat
SETUP-ARP.bat
START-ARP.bat
```

Login: https://arp.ahsteellab.com/login

---

## Cloudflare DNS (automatic)

`SETUP-ERP.bat` / `SETUP-ARP.bat` on each PC creates:

| Site | Tunnel name | Hostname |
|---|---|---|
| ERP | `ahsteellab-erp` | `erp.ahsteellab.com` |
| ARP | `ahsteellab-arp` | `arp.ahsteellab.com` |

Both use local ports **8000** (ERP) and **8001** (ARP) on the same PC — no conflict.

---

## Production .env checklist

### erp.ahsteellab.com (Shafique Center)
```env
APP_NAME=Shafique Departmental Store
BASE_URL=https://erp.ahsteellab.com
PORT=8000
BUSINESS_DB_NAME=nsds2626
DB_NAME=NSDS2626_AUTH
DB_SERVER=shahenhp
BUSINESS_DB_SERVER=shahenhp
```

### arp.ahsteellab.com (Al Haram Steel Lab)
```env
APP_NAME=Al Haram Steel Lab
BASE_URL=https://arp.ahsteellab.com
PORT=8001
BUSINESS_DB_NAME=nahsl2627
DB_NAME=NAHSL2627_AUTH
DB_SERVER=shahenhp
BUSINESS_DB_SERVER=shahenhp
```

---

## Important

- Run setup **once per PC** (not once total).
- Each site needs its own `SECRET_KEY` and `CSRF_SECRET_KEY`.
- Do **not** put both hostnames in one `config.yml` unless both apps run on the **same** PC on different ports.
