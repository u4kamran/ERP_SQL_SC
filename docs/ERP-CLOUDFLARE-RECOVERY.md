# ERP Cloudflare / Website Down — Recovery Procedure

**Site:** Shafique Departmental Store (`https://erp.ahsteellab.com`)  
**Folder:** `D:\CursorProject\ahsteellab-nsds2626`  
**Origin:** `http://127.0.0.1:8000`  
**Do not touch ARP** (`ahsteellab-arp`) unless that site is also down.

---

## Quick rule

Phone / browser Cloudflare errors (502, 522, 1033, timeout) almost always mean:

> **Origin ERP on this PC is down or hung** — not that Cloudflare itself is “broken.”

Fix the local ERP first. Cloudflare will recover when `/health` responds.

---

## Official start / stop (use ONLY these)

| Action | File |
|--------|------|
| **Start** | `START-ERP-SERVICES.bat` |
| **Stop** | `STOP-ERP-SERVICES.bat` |
| **Status** | PowerShell: `deploy\erp-always-on.ps1 -Action status` |

These control scheduled tasks:

1. `AHSteelLab-ERP-App` — Python API on port **8000**
2. `AHSteelLab-ERP-Tunnel` — Cloudflare tunnel for `erp.ahsteellab.com`

### Never run while services are on

- `START-APP.bat`
- `FIX-TUNNEL.bat`
- Extra `python run.py` windows

Duplicates freeze the API → Cloudflare 502 / phone timeouts.

---

## Procedure when the website shows a Cloudflare error

### Step 1 — Confirm the error

Note:

- Exact Cloudflare code (502 / 522 / 1033 / 524 / …)
- URL (home, login, API, mobile app)
- Time

### Step 2 — Check local origin (most important)

On the ERP PC, open PowerShell:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 10
```

| Result | Meaning |
|--------|---------|
| Fast JSON `"status":"healthy"` | Origin OK → go to Step 5 (tunnel / DNS) |
| Timeout / cannot connect | Origin down or hung → Step 3 |
| Connects but hangs forever | Hung process → Step 3 (hard restart) |

### Step 3 — Clean restart (normal)

1. Double-click **`STOP-ERP-SERVICES.bat`**
2. Wait **10 seconds**
3. Double-click **`START-ERP-SERVICES.bat`**
4. Wait **15–20 seconds**
5. Recheck local health (Step 2)
6. Recheck public:

```powershell
Invoke-WebRequest https://erp.ahsteellab.com/health -UseBasicParsing -TimeoutSec 20
```

Both should return `"healthy"`.

### Step 4 — Hard restart if still hanging

If local `/health` still times out even though tasks say “Running”:

```powershell
cd D:\CursorProject\ahsteellab-nsds2626

# Stop tasks
schtasks /End /TN "AHSteelLab-ERP-App"
schtasks /End /TN "AHSteelLab-ERP-Tunnel"

# Kill leftover ERP Python on this project only
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like "*ahsteellab-nsds2626*" } |
  ForEach-Object { taskkill /PID $_.ProcessId /F }

# Free port 8000 if something still holds it
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
  ForEach-Object { taskkill /PID $_.OwningProcess /F }

Start-Sleep -Seconds 3

# Start clean
schtasks /Run /TN "AHSteelLab-ERP-Tunnel"
Start-Sleep -Seconds 4
schtasks /Run /TN "AHSteelLab-ERP-App"
Start-Sleep -Seconds 15

Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 10
Invoke-WebRequest https://erp.ahsteellab.com/health -UseBasicParsing -TimeoutSec 20
```

Or simply: **Stop bat → wait → Start bat** after killing leftovers.

### Step 5 — If local is healthy but public still fails

1. Confirm tunnel task is **Running**:

```powershell
schtasks /Query /TN "AHSteelLab-ERP-Tunnel" /FO LIST
```

2. Confirm ERP `cloudflared` process uses **ERP** config (not ARP only):

```text
...\ahsteellab-nsds2626\deploy\cloudflared\config.yml
```

3. Restart tunnel only:

```powershell
schtasks /End /TN "AHSteelLab-ERP-Tunnel"
Start-Sleep -Seconds 2
schtasks /Run /TN "AHSteelLab-ERP-Tunnel"
```

4. Wait 15 seconds, retest `https://erp.ahsteellab.com/health`

5. Browser: hard refresh or private window (cache can show an old Cloudflare page).

### Step 6 — Still failing

Check:

- [ ] PC is online / SQL Server reachable (ERP needs DB)
- [ ] `.env` exists in `ahsteellab-nsds2626`
- [ ] `venv\Scripts\python.exe` exists
- [ ] `logs\app.log` last lines for Python crash
- [ ] You did **not** run `cloudflared service install` (machine-wide service steals tunnels)

Then restart once more with Step 3/4.

---

## Status checklist (copy/paste)

```powershell
cd D:\CursorProject\ahsteellab-nsds2626
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy\erp-always-on.ps1 -Action status

schtasks /Query /TN "AHSteelLab-ERP-App" /FO LIST
schtasks /Query /TN "AHSteelLab-ERP-Tunnel" /FO LIST

Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

Invoke-WebRequest http://127.0.0.1:8000/health -UseBasicParsing -TimeoutSec 10
Invoke-WebRequest https://erp.ahsteellab.com/health -UseBasicParsing -TimeoutSec 20
```

Expected:

- App + Tunnel = **Running**
- Port 8000 = **Listen**
- Both health URLs = **200** + `"healthy"`

---

## Decision guide

```text
Cloudflare error on erp.ahsteellab.com
        │
        ▼
Local /health OK?
   ┌────┴────┐
  YES       NO
   │         │
   ▼         ▼
Fix tunnel  STOP → START ERP services
 / cache    (hard kill if hung)
```

---

## After code changes (OTP, APIs, admin pages)

The running ERP process does **not** auto-reload.

1. `STOP-ERP-SERVICES.bat`
2. `START-ERP-SERVICES.bat`
3. Confirm `/health`

---

## Customer mobile app note

Expo app needs ERP public API healthy:

`EXPO_PUBLIC_API_BASE_URL=https://erp.ahsteellab.com/api/v1`

If the phone fails but `/health` is OK, the problem is usually app cache/network — not Cloudflare origin.

---

## One-line memory

**Cloudflare error → check `127.0.0.1:8000/health` → STOP-ERP-SERVICES → START-ERP-SERVICES → recheck public `/health`.**
