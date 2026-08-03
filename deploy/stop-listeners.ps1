# Stop processes listening on ERP/ARP ports and local cloudflared tunnels.
$ErrorActionPreference = "SilentlyContinue"

foreach ($port in 8000, 8001) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Get-Process cloudflared -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2
