#Requires -Version 5.1
<#
.SYNOPSIS
    Start app + Cloudflare tunnel for a site profile.

.PARAMETER Site
    Site code: erp or arp
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("erp", "arp")]
    [string]$Site
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SiteConfigPath = Join-Path $ProjectRoot "deploy\sites\$Site.json"
$cfg = Get-Content $SiteConfigPath -Raw | ConvertFrom-Json

$CloudflaredExe = Join-Path $ProjectRoot "deploy\cloudflared\bin\cloudflared.exe"
$ConfigFile = Join-Path $ProjectRoot "deploy\cloudflared\config.yml"
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$WatchdogScript = Join-Path $ProjectRoot "scripts\app_watchdog.py"
$EnvFile = Join-Path $ProjectRoot ".env"
$Port = [int]$cfg.port
$Hostname = $cfg.hostname

if (-not (Test-Path $EnvFile)) {
    throw ".env not found. Run SETUP-$($Site.ToUpper()).bat first."
}

if (-not (Test-Path $ConfigFile)) {
    throw "Cloudflare config not found. Run SETUP-$($Site.ToUpper()).bat first."
}

function Test-CloudflareConfig {
    param([string]$Path, [string]$ExpectedHostname, [int]$ExpectedPort)
    $content = Get-Content $Path -Raw
    if ($content -notmatch [regex]::Escape($ExpectedHostname)) {
        throw @"
Cloudflare config.yml is for the wrong site (missing $ExpectedHostname).
Run SETUP-$($Site.ToUpper()).bat in this project folder to regenerate it.
"@
    }
    if ($content -notmatch "127\.0\.0\.1:$ExpectedPort") {
        throw @"
Cloudflare config.yml points to the wrong port (expected 127.0.0.1:$ExpectedPort).
Run SETUP-$($Site.ToUpper()).bat in this project folder to regenerate it.
"@
    }
}

Test-CloudflareConfig -Path $ConfigFile -ExpectedHostname $Hostname -ExpectedPort $Port

if (-not (Test-Path $PythonExe)) {
    throw "Python venv not found. Run INSTALL-$($Site.ToUpper()).bat first."
}

if (-not (Test-Path $CloudflaredExe)) {
    throw "cloudflared not found. Run SETUP-$($Site.ToUpper()).bat first."
}

Write-Host ""
Write-Host "Starting $($cfg.displayName)..." -ForegroundColor Cyan
Write-Host "  Local:   http://127.0.0.1:$Port/health"
Write-Host "  Public:  https://$Hostname"
Write-Host ""

Start-Process cmd -ArgumentList @(
    "/c", "cd /d `"$ProjectRoot`" && `"$PythonExe`" `"$WatchdogScript`""
) -WindowStyle Minimized

Start-Sleep -Seconds 5

# Start tunnel for this site only (match this site's config path in command line)
$configNorm = $ConfigFile.Replace('\', '/')
$existingTunnel = Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $cmd = $_.CommandLine
        ($cmd -like "*$ConfigFile*") -or ($cmd -like "*$configNorm*")
    }
if (-not $existingTunnel) {
    Start-Process cmd -ArgumentList @(
        "/c", "cd /d `"$ProjectRoot`" && `"$CloudflaredExe`" tunnel --config `"$ConfigFile`" run"
    ) -WindowStyle Minimized
} else {
    Write-Host "Cloudflare tunnel already running for this site." -ForegroundColor Yellow
}

Write-Host "Started app watchdog and Cloudflare tunnel." -ForegroundColor Green
Write-Host "Open: https://$Hostname/login"
Write-Host "To stop: STOP-APP.bat"
Write-Host ""
