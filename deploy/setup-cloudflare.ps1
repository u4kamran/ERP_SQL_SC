#Requires -Version 5.1
<#
.SYNOPSIS
    One-time setup: install cloudflared, create tunnel, route DNS for erp.ahsteellab.com

.DESCRIPTION
    Run from an elevated PowerShell in the project root:
        .\deploy\setup-cloudflare.ps1

    Steps performed:
    1. Download cloudflared (if missing)
    2. Log in to Cloudflare (browser opens)
    3. Create tunnel "ahsteellab-erp"
    4. Route DNS: erp.ahsteellab.com
    5. Write deploy/cloudflared/config.yml
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DeployDir = Join-Path $ProjectRoot "deploy"
$CloudflaredDir = Join-Path $DeployDir "cloudflared"
$BinDir = Join-Path $CloudflaredDir "bin"
$ConfigFile = Join-Path $CloudflaredDir "config.yml"
$TunnelName = "ahsteellab-erp"
$Hostname = "erp.ahsteellab.com"
$CloudflaredExe = Join-Path $BinDir "cloudflared.exe"

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
    Write-Host "DNS route may already exist — continuing." -ForegroundColor Yellow
}

$credentialsFile = Join-Path $env:USERPROFILE ".cloudflared\$tunnelId.json"
if (-not (Test-Path $credentialsFile)) {
    throw "Credentials file not found: $credentialsFile"
}

Write-Step "Writing $ConfigFile"
$template = Get-Content (Join-Path $CloudflaredDir "config.yml.template") -Raw
$config = $template `
    -replace '\{\{TUNNEL_ID\}\}', $tunnelId `
    -replace '\{\{CREDENTIALS_FILE\}\}', ($credentialsFile -replace '\\', '/') `
    -replace '\{\{HOSTNAME\}\}', $Hostname `
    -replace '\{\{PORT\}\}', '8000'
Set-Content -Path $ConfigFile -Value $config -Encoding UTF8

Write-Step "Production environment file"
$prodExample = Join-Path $ProjectRoot ".env.production.example"
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item $prodExample $envFile
    Write-Host "Created .env from .env.production.example"
    Write-Host "IMPORTANT: Edit .env and set SECRET_KEY, CSRF_SECRET_KEY, DB_PASSWORD" -ForegroundColor Yellow
} else {
    Write-Host ".env already exists — not overwritten."
    Write-Host "Compare with .env.production.example and update BASE_URL, APP_ENV, etc."
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit .env for production (SECRET_KEY, passwords, BASE_URL)"
Write-Host "  2. Start app + tunnel:  .\deploy\start-production.ps1"
Write-Host "  3. Install as Windows services:  .\deploy\install-services.ps1"
Write-Host "  4. Open: https://$Hostname/login"
Write-Host ""
