#Requires -RunAsAdministrator
#Requires -Version 5.1
<#
.SYNOPSIS
    Install AH Steel Lab app and Cloudflare Tunnel as Windows services (always-on).

.DESCRIPTION
    Run PowerShell as Administrator from project root:
        .\deploy\install-services.ps1

    Requires cloudflared setup completed (setup-cloudflare.ps1).
    Uses Windows Task Scheduler for the Python app and cloudflared's built-in service for the tunnel.
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CloudflaredExe = Join-Path $ProjectRoot "deploy\cloudflared\bin\cloudflared.exe"
$ConfigFile = Join-Path $ProjectRoot "deploy\cloudflared\config.yml"
$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$RunScript = Join-Path $ProjectRoot "run.py"
$StartScript = Join-Path $ProjectRoot "deploy\start-app-service.ps1"
$AppTaskName = "AHSteelLab-ERP-App"
$TunnelServiceName = "Cloudflared-AHSteelLab-ERP"

if (-not (Test-Path $ConfigFile)) {
    throw "Run deploy\setup-cloudflare.ps1 first."
}

# Wrapper script for scheduled task (Task Scheduler needs a single script path)
@"
Set-Location '$ProjectRoot'
`$env:APP_ENV = 'production'
& '$PythonExe' '$RunScript'
"@ | Set-Content -Path $StartScript -Encoding UTF8

Write-Host "Installing Cloudflare Tunnel Windows service..." -ForegroundColor Cyan
& $CloudflaredExe service uninstall 2>$null
& $CloudflaredExe service install --config $ConfigFile
if ($LASTEXITCODE -ne 0) {
    throw "cloudflared service install failed"
}
Write-Host "Tunnel service installed (runs as Cloudflared-AHSteelLab or cloudflared)." -ForegroundColor Green

Write-Host "Installing app scheduled task (runs at startup)..." -ForegroundColor Cyan
$existing = Get-ScheduledTask -TaskName $AppTaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $AppTaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $AppTaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "AH Steel Lab FastAPI application" | Out-Null

Start-ScheduledTask -TaskName $AppTaskName
Write-Host "App task '$AppTaskName' registered and started." -ForegroundColor Green

Write-Host ""
Write-Host "Services installed. Site should be live at https://erp.ahsteellab.com" -ForegroundColor Green
Write-Host ""
Write-Host "Manage:"
Write-Host "  App task:    Get-ScheduledTask -TaskName $AppTaskName"
Write-Host "  Tunnel:      Get-Service cloudflared"
Write-Host "  Stop tunnel: & '$CloudflaredExe' service uninstall"
