#Requires -Version 5.1
<#
.SYNOPSIS
    Always-on ERP helpers: install, uninstall, start, stop.

    Uses current Windows user scheduled tasks (not cloudflared service install),
    so ARP on this PC is not taken over.
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("install", "uninstall", "start", "stop", "status")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SiteConfigPath = Join-Path $ProjectRoot "deploy\sites\erp.json"
$cfg = Get-Content $SiteConfigPath -Raw | ConvertFrom-Json

$PythonExe = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$RunScript = Join-Path $ProjectRoot "run.py"
$CloudflaredExe = Join-Path $ProjectRoot "deploy\cloudflared\bin\cloudflared.exe"
$ConfigFile = Join-Path $ProjectRoot "deploy\cloudflared\config.yml"
$AppWrapper = Join-Path $ProjectRoot "deploy\start-app-service-erp.ps1"
$TunnelWrapper = Join-Path $ProjectRoot "deploy\start-tunnel-service-erp.ps1"
$HealthScript = Join-Path $ProjectRoot "deploy\erp-health-restart.ps1"

$AppTask = [string]$cfg.taskName
$TunnelTask = "AHSteelLab-ERP-Tunnel"
$HealthTask = "AHSteelLab-ERP-Health"
$Port = [int]$cfg.port

function Test-ErpConfig {
    if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
        throw ".env not found. Run SETUP-ERP.bat first."
    }
    if (-not (Test-Path $PythonExe)) {
        throw "venv Python not found. Run INSTALL-ERP.bat first."
    }
    if (-not (Test-Path $CloudflaredExe)) {
        throw "cloudflared.exe not found. Run SETUP-ERP.bat first."
    }
    if (-not (Test-Path $ConfigFile)) {
        throw "deploy\cloudflared\config.yml not found. Run SETUP-ERP.bat first."
    }
    $content = Get-Content $ConfigFile -Raw
    if ($content -notmatch [regex]::Escape([string]$cfg.hostname)) {
        throw "config.yml is not for $($cfg.hostname). Do not install ARP config as ERP."
    }
    if ($content -notmatch "127\.0\.0\.1:$Port") {
        throw "config.yml must point at 127.0.0.1:$Port."
    }
}

function Stop-ErpBatCopies {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -like "*ahsteellab-nsds2626*") } |
        ForEach-Object {
            Write-Host "Stopping Python PID $($_.ProcessId)"
            cmd /c "taskkill /PID $($_.ProcessId) /F >nul 2>&1"
        }

    Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and ($_.CommandLine -like "*ahsteellab-nsds2626*") } |
        ForEach-Object {
            Write-Host "Stopping ERP tunnel PID $($_.ProcessId)"
            cmd /c "taskkill /PID $($_.ProcessId) /F >nul 2>&1"
        }

    $listen = netstat -ano | Select-String ":$Port" | Select-String "LISTENING"
    foreach ($line in $listen) {
        $procId = ($line.ToString() -split "\s+")[-1]
        if ($procId -match "^\d+$") {
            Write-Host "Stopping listener PID $procId on port $Port"
            cmd /c "taskkill /PID $procId /F >nul 2>&1"
        }
    }
}

function Get-ErpTaskPrincipal {
    $account = "$env:USERDOMAIN\$env:USERNAME"
    New-ScheduledTaskPrincipal -UserId $account -LogonType Interactive -RunLevel Limited
}

function Get-LongRunningSettings {
    New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -MultipleInstances IgnoreNew
}

function Write-Wrappers {
    @"
Set-Location '$ProjectRoot'
`$env:APP_ENV = 'production'
& '$PythonExe' '$RunScript'
"@ | Set-Content -Path $AppWrapper -Encoding UTF8

    @"
Set-Location '$ProjectRoot'
& '$CloudflaredExe' tunnel --config '$ConfigFile' run
"@ | Set-Content -Path $TunnelWrapper -Encoding UTF8
}

function Register-ErpTask {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [string]$Description,
        $Trigger
    )
    $existing = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
    }
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    $principal = Get-ErpTaskPrincipal
    $settings = Get-LongRunningSettings
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $Trigger -Principal $principal -Settings $settings -Description $Description | Out-Null
}

function Install-ErpAlwaysOn {
    Test-ErpConfig
    Write-Host "Installing always-on ERP tasks for $($cfg.hostname)..." -ForegroundColor Cyan
    Write-Wrappers
    Stop-ErpBatCopies
    Start-Sleep -Seconds 2

    $boot = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    Register-ErpTask -Name $AppTask -ScriptPath $AppWrapper -Description "Shafique Center ERP (run.py)" -Trigger $boot
    Register-ErpTask -Name $TunnelTask -ScriptPath $TunnelWrapper -Description "Shafique Center Cloudflare tunnel (ERP config only)" -Trigger $boot

    $healthLogon = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    $healthRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 2) -RepetitionDuration (New-TimeSpan -Hours 23 -Minutes 50)
    $existingHealth = Get-ScheduledTask -TaskName $HealthTask -ErrorAction SilentlyContinue
    if ($existingHealth) {
        Unregister-ScheduledTask -TaskName $HealthTask -Confirm:$false
    }
    $healthAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$HealthScript`""
    $healthSettings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
        -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $HealthTask -Action $healthAction -Trigger @($healthLogon, $healthRepeat) -Principal (Get-ErpTaskPrincipal) -Settings $healthSettings -Description "Restart ERP if http://127.0.0.1:$Port/health fails" | Out-Null

    Start-ScheduledTask -TaskName $TunnelTask
    Start-Sleep -Seconds 3
    Start-ScheduledTask -TaskName $AppTask
    Disable-ScheduledTask -TaskName $HealthTask -ErrorAction SilentlyContinue | Out-Null

    Write-Host "Installed:" -ForegroundColor Green
    Write-Host "  $AppTask"
    Write-Host "  $TunnelTask"
    Write-Host "  $HealthTask (registered, disabled - does not kill a live ERP)"
    Write-Host "Do not run START-APP.bat or FIX-TUNNEL.bat while these tasks are on."
}

function Uninstall-ErpAlwaysOn {
    foreach ($name in @($HealthTask, $AppTask, $TunnelTask)) {
        $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
            Unregister-ScheduledTask -TaskName $name -Confirm:$false
            Write-Host "Removed task $name"
        }
    }
    Stop-ErpBatCopies
}

function Start-ErpAlwaysOn {
    Test-ErpConfig
    foreach ($name in @($TunnelTask, $AppTask)) {
        $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if (-not $existing) {
            throw "Task $name is not installed. Run INSTALL-ERP-SERVICES.bat first."
        }
        Start-ScheduledTask -TaskName $name
        Write-Host "Started $name"
    }
}

function Stop-ErpAlwaysOn {
    foreach ($name in @($HealthTask, $AppTask, $TunnelTask)) {
        $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($existing) {
            Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
            Write-Host "Stopped $name"
        }
    }
    Stop-ErpBatCopies
}

function Show-ErpStatus {
    foreach ($name in @($AppTask, $TunnelTask, $HealthTask)) {
        $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($t) {
            Write-Host ("{0}: {1}" -f $name, $t.State)
        } else {
            Write-Host ("{0}: not installed" -f $name)
        }
    }
}

switch ($Action) {
    "install" { Install-ErpAlwaysOn }
    "uninstall" { Uninstall-ErpAlwaysOn }
    "start" { Start-ErpAlwaysOn }
    "stop" { Stop-ErpAlwaysOn }
    "status" { Show-ErpStatus }
}
