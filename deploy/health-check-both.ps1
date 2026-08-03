# Health check for ERP and ARP (local + public URLs).
$ErrorActionPreference = "SilentlyContinue"

function Test-Url($label, $url, $timeoutSec) {
    try {
        $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec $timeoutSec
        Write-Host "  $label" $r.Content
    } catch {
        Write-Host "  $label FAIL"
    }
}

Test-Url "ERP local :" "http://127.0.0.1:8000/health" 10
Test-Url "ARP local :" "http://127.0.0.1:8001/health" 10
Test-Url "ERP public:" "https://erp.ahsteellab.com/health" 15
Test-Url "ARP public:" "https://arp.ahsteellab.com/health" 15
