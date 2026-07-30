#Requires -Version 5.1
<#
.SYNOPSIS
    Start AH Steel Lab app and Cloudflare Tunnel for production.

.DESCRIPTION
    Run from project root:
        .\deploy\start-production.ps1

    Starts FastAPI on 127.0.0.1:8000 and cloudflared tunnel in separate windows.
    For always-on hosting, use install-services.ps1 instead.
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CloudflaredExe = Join-Path $ProjectRoot "deploy\cloudflared\bin\cloudflared.exe"
$ConfigFile = Join-Path $ProjectRoot "deploy\cloudflared\config.yml"
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$RunScript = Join-Path $ProjectRoot "run.py"
$EnvFile = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $EnvFile)) {
    throw ".env not found. Run deploy\setup-cloudflare.ps1 first or copy .env.production.example to .env"
}

if (-not (Test-Path $ConfigFile)) {
    throw "Cloudflare config not found: $ConfigFile`nRun deploy\setup-cloudflare.ps1 first."
}

if (-not (Test-Path $PythonExe)) {
    throw "Python venv not found. Run: python -m venv venv && pip install -r requirements.txt"
}

if (-not (Test-Path $CloudflaredExe)) {
    throw "cloudflared not found. Run deploy\setup-cloudflare.ps1 first."
}

Write-Host "Starting AH Steel Lab (production)..." -ForegroundColor Cyan
Write-Host "  App:     http://127.0.0.1:8000"
Write-Host "  Public:  https://erp.ahsteellab.com"
Write-Host ""

# Start FastAPI in a new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot'; `$env:APP_ENV='production'; & '$PythonExe' '$RunScript'"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Cloudflare Tunnel in a new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "& '$CloudflaredExe' tunnel --config '$ConfigFile' run"
) -WindowStyle Normal

Write-Host "Started app and tunnel in separate windows." -ForegroundColor Green
Write-Host "Open https://erp.ahsteellab.com/login in your browser."
