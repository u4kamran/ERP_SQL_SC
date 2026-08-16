#Requires -Version 5.1
<#
.SYNOPSIS
    Restart ERP only after several failed health checks, and never during startup.
    Does not touch ARP (port 8001).
#>

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SiteConfigPath = Join-Path $ProjectRoot "deploy\sites\erp.json"
$cfg = Get-Content $SiteConfigPath -Raw | ConvertFrom-Json
$Port = [int]$cfg.port
$AppTask = [string]$cfg.taskName
$HealthUrl = "http://127.0.0.1:$Port/health"
$StateFile = Join-Path $ProjectRoot "data\erp-health-state.json"
$FailNeed = 3
$GraceSeconds = 90

function Read-State {
    if (-not (Test-Path $StateFile)) {
        return [pscustomobject]@{ fails = 0; lastRestart = 0 }
    }
    try {
        return Get-Content $StateFile -Raw | ConvertFrom-Json
    } catch {
        return [pscustomobject]@{ fails = 0; lastRestart = 0 }
    }
}

function Write-State($state) {
    $dir = Split-Path $StateFile
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    ($state | ConvertTo-Json) | Set-Content -Path $StateFile -Encoding UTF8
}

function Test-ErpHealth {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 8
        return ($response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Stop-HungErp {
    $existing = Get-ScheduledTask -TaskName $AppTask -ErrorAction SilentlyContinue
    if ($existing) {
        Stop-ScheduledTask -TaskName $AppTask -ErrorAction SilentlyContinue
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and (
                ($_.CommandLine -like "*start-app-service-erp.ps1*") -or
                (($_.CommandLine -like "*ahsteellab-nsds2626*") -and ($_.CommandLine -like "*run.py*"))
            )
        } |
        ForEach-Object { cmd /c "taskkill /PID $($_.ProcessId) /T /F >nul 2>&1" }
    $listen = netstat -ano | Select-String ":$Port" | Select-String "LISTENING"
    foreach ($line in $listen) {
        $procId = ($line.ToString() -split "\s+")[-1]
        if ($procId -match "^\d+$") {
            cmd /c "taskkill /PID $procId /T /F >nul 2>&1"
        }
    }
    Start-Sleep -Seconds 3
}

$state = Read-State
$now = [DateTimeOffset]::Now.ToUnixTimeSeconds()
if ($state.lastRestart -and (($now - [int]$state.lastRestart) -lt $GraceSeconds)) {
    exit 0
}

if (Test-ErpHealth) {
    $state.fails = 0
    Write-State $state
    exit 0
}

$state.fails = ([int]$state.fails) + 1
if ($state.fails -lt $FailNeed) {
    Write-State $state
    Write-Host "$(Get-Date -Format 'HH:mm:ss') ERP health miss $($state.fails)/$FailNeed — not restarting yet"
    exit 0
}

Write-Host "$(Get-Date -Format 'HH:mm:ss') ERP health failed $FailNeed times — force restarting $AppTask"
Stop-HungErp
$state.fails = 0
$state.lastRestart = [DateTimeOffset]::Now.ToUnixTimeSeconds()
Write-State $state

$existing = Get-ScheduledTask -TaskName $AppTask -ErrorAction SilentlyContinue
if ($existing) {
    Start-ScheduledTask -TaskName $AppTask
} else {
    $python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
    $run = Join-Path $ProjectRoot "run.py"
    Start-Process -FilePath $python -ArgumentList "`"$run`"" -WorkingDirectory $ProjectRoot -WindowStyle Minimized
}

Start-Sleep -Seconds 12
if (Test-ErpHealth) {
    Write-Host "ERP health restored"
    exit 0
}
Write-Host "ERP still unhealthy after restart"
exit 1
