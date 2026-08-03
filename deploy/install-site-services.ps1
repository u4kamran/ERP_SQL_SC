#Requires -RunAsAdministrator
#Requires -Version 5.1
<#
.SYNOPSIS
    Install app + Cloudflare tunnel as Windows services for a site profile.

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
$RunScript = Join-Path $ProjectRoot "run.py"
$StartScript = Join-Path $ProjectRoot "deploy\start-app-service-$Site.ps1"
$AppTaskName = $cfg.taskName
$Hostname = $cfg.hostname

if (-not (Test-Path $ConfigFile)) {
    throw "Run SETUP-$($Site.ToUpper()).bat first."
}

@"
Set-Location '$ProjectRoot'
`$env:APP_ENV = 'production'
& '$PythonExe' '$RunScript'
"@ | Set-Content -Path $StartScript -Encoding UTF8

Write-Host "Installing Cloudflare Tunnel service for $($cfg.displayName)..." -ForegroundColor Cyan
& $CloudflaredExe service uninstall 2>$null
& $CloudflaredExe service install --config $ConfigFile
if ($LASTEXITCODE -ne 0) {
    throw "cloudflared service install failed"
}
Write-Host "Tunnel service installed." -ForegroundColor Green

Write-Host "Installing app scheduled task '$AppTaskName'..." -ForegroundColor Cyan
$existing = Get-ScheduledTask -TaskName $AppTaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $AppTaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $AppTaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "$($cfg.displayName) FastAPI application" | Out-Null

Start-ScheduledTask -TaskName $AppTaskName
Write-Host "App task registered and started." -ForegroundColor Green

Write-Host ""
Write-Host "Services installed for $($cfg.displayName)." -ForegroundColor Green
Write-Host "Site: https://$Hostname"
Write-Host ""
