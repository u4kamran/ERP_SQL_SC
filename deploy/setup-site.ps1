#Requires -Version 5.1
<#
.SYNOPSIS
    One-time setup for a site: cloudflared tunnel + .env from site profile.

.PARAMETER Site
    Site code: erp (Shafique Center) or arp (Al Haram Steel Lab)

.EXAMPLE
    .\deploy\setup-site.ps1 -Site erp
    .\deploy\setup-site.ps1 -Site arp
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("erp", "arp")]
    [string]$Site,

    [switch]$SkipEnv
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DeployDir = Join-Path $ProjectRoot "deploy"
$CloudflaredDir = Join-Path $DeployDir "cloudflared"
$BinDir = Join-Path $CloudflaredDir "bin"
$ConfigFile = Join-Path $CloudflaredDir "config.yml"
$CloudflaredExe = Join-Path $BinDir "cloudflared.exe"
$SiteConfigPath = Join-Path $DeployDir "sites\$Site.json"

if (-not (Test-Path $SiteConfigPath)) {
    throw "Site config not found: $SiteConfigPath"
}

$cfg = Get-Content $SiteConfigPath -Raw | ConvertFrom-Json
$TunnelName = $cfg.tunnelName
$Hostname = $cfg.hostname
$Port = [int]$cfg.port

function Write-Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Cloudflared {
    if (Test-Path $CloudflaredExe) {
        Write-Host "cloudflared found: $CloudflaredExe"
        return
    }

    Write-Step "Downloading cloudflared for Windows amd64"
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $CloudflaredExe -UseBasicParsing
    Write-Host "Downloaded cloudflared to $CloudflaredExe"
}

function Get-TunnelId {
    param([string]$Name)
    try {
        $json = & $CloudflaredExe tunnel list -o json 2>$null | ConvertFrom-Json
        foreach ($t in $json) {
            if ($t.name -eq $Name) { return $t.id }
        }
    } catch {
        $output = & $CloudflaredExe tunnel list 2>&1 | Out-String
        foreach ($line in ($output -split "`n")) {
            if ($line -match "([0-9a-f-]{36}).*$Name") {
                return $Matches[1]
            }
        }
    }
    return $null
}

Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup: $($cfg.displayName)" -ForegroundColor Green
Write-Host "  URL:    https://$Hostname" -ForegroundColor Green
Write-Host "  DB:     $($cfg.businessDbName)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Ensure-Cloudflared

Write-Step "Log in to Cloudflare (browser will open)"
Write-Host "Select the ahsteellab.com zone when prompted."
& $CloudflaredExe tunnel login
if ($LASTEXITCODE -ne 0) {
    throw "cloudflared tunnel login failed"
}

Write-Step "Create tunnel '$TunnelName' (skip if it already exists)"
$tunnelId = Get-TunnelId -Name $TunnelName
if (-not $tunnelId) {
    $createOutput = & $CloudflaredExe tunnel create $TunnelName 2>&1 | Out-String
    Write-Host $createOutput
    $tunnelId = Get-TunnelId -Name $TunnelName
}
if (-not $tunnelId) {
    throw "Could not determine tunnel ID for '$TunnelName'"
}
Write-Host "Tunnel ID: $tunnelId"

Write-Step "Route DNS: $Hostname -> $TunnelName"
& $CloudflaredExe tunnel route dns $TunnelName $Hostname
if ($LASTEXITCODE -ne 0) {
    Write-Host "DNS route may already exist - continuing." -ForegroundColor Yellow
}

$credentialsFile = Join-Path $env:USERPROFILE ".cloudflared\$tunnelId.json"
if (-not (Test-Path $credentialsFile)) {
    throw "Credentials file not found: $credentialsFile"
}

Write-Step "Writing $ConfigFile (port $Port)"
$template = Get-Content (Join-Path $CloudflaredDir "config.yml.template") -Raw
$config = $template `
    -replace '\{\{TUNNEL_ID\}\}', $tunnelId `
    -replace '\{\{CREDENTIALS_FILE\}\}', ($credentialsFile -replace '\\', '/') `
    -replace '\{\{HOSTNAME\}\}', $Hostname `
    -replace '\{\{PORT\}\}', "$Port"
Set-Content -Path $ConfigFile -Value $config -Encoding UTF8

if (-not $SkipEnv) {
    Write-Step "Creating .env for site '$Site'"
    $PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
    $EnvFile = Join-Path $ProjectRoot ".env"
    if (-not (Test-Path $PythonExe)) {
        Write-Host "venv not found - run INSTALL-ERP.bat or INSTALL-ARP.bat first." -ForegroundColor Yellow
        Write-Host "Then run: python install\generate_env.py --site $Site --force"
    } elseif (Test-Path $EnvFile) {
        Write-Host ".env already exists - not overwritten."
        Write-Host "Verify DB_SERVER=shaheenhp and DB_PASSWORD in .env"
    } else {
        & $PythonExe (Join-Path $ProjectRoot "install\generate_env.py") --site $Site --force
        Write-Host ""
        Write-Host "IMPORTANT: Edit .env and set DB_PASSWORD" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Setup complete for $($cfg.displayName)!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit .env - set DB_PASSWORD (and verify DB_SERVER if needed)"
Write-Host "  2. Start site:  START-$($Site.ToUpper()).bat"
Write-Host "  3. Always-on:   powershell -File deploy\install-site-services.ps1 -Site $Site"
Write-Host "  4. Open:        https://$Hostname/login"
Write-Host ""
