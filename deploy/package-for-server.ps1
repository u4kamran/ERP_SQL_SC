#Requires -Version 5.1
<#
.SYNOPSIS
    Create unzip-and-run ZIP for server deployment.

.DESCRIPTION
    Run from project root:
        .\deploy\package-for-server.ps1

    Output: AHSteelLab-UNZIP-AND-RUN.zip
#>

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DeployDir = Join-Path $ProjectRoot "deploy"
$OutputZip = Join-Path $ProjectRoot "AHSteelLab-UNZIP-AND-RUN.zip"
$StagingDir = Join-Path $DeployDir "_package_staging"

$ExcludeDirNames = @(
    "venv", ".venv", "env", "__pycache__", ".pytest_cache",
    "htmlcov", ".git", ".idea", ".vscode", "logs", "_package_staging", "bin"
)
$ExcludeFileNames = @(
    ".env", ".env.local", ".env.production", "app.log", "secrets.txt"
)
$ExcludeFilePatterns = @("*.pyc", "*.pyo", "*.log", "AHSteelLab-*.zip")

function Should-ExcludePath {
    param([string]$FullPath, [string]$Root)

    $relative = $FullPath.Substring($Root.Length).TrimStart('\', '/')
    $parts = $relative -split '[\\/]'

    foreach ($part in $parts) {
        if ($ExcludeDirNames -contains $part) { return $true }
    }

    $fileName = Split-Path $FullPath -Leaf
    if ($ExcludeFileNames -contains $fileName) { return $true }

    foreach ($pattern in $ExcludeFilePatterns) {
        if ($fileName -like $pattern) { return $true }
    }

    if ($relative -eq "deploy\cloudflared\config.yml") { return $true }
    if ($relative -eq "deploy/start-app-service.ps1") { return $true }

    return $false
}

function Copy-ProjectFiles {
    param([string]$Source, [string]$Destination, [string]$Root)

    Get-ChildItem -Path $Source -Force | ForEach-Object {
        if (Should-ExcludePath -FullPath $_.FullName -Root $Root) {
            return
        }

        $target = Join-Path $Destination $_.Name
        if ($_.PSIsContainer) {
            New-Item -ItemType Directory -Force -Path $target | Out-Null
            Copy-ProjectFiles -Source $_.FullName -Destination $target -Root $Root
        } else {
            Copy-Item -Path $_.FullName -Destination $target -Force
        }
    }
}

Write-Host "Creating unzip-and-run package..." -ForegroundColor Cyan

if (Test-Path $StagingDir) {
    Remove-Item -Path $StagingDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null

Copy-ProjectFiles -Source $ProjectRoot -Destination $StagingDir -Root $ProjectRoot

if (Test-Path $OutputZip) {
    Remove-Item -Path $OutputZip -Force
}

Compress-Archive -Path (Join-Path $StagingDir "*") -DestinationPath $OutputZip -CompressionLevel Optimal
Remove-Item -Path $StagingDir -Recurse -Force

$sizeMb = [math]::Round((Get-Item $OutputZip).Length / 1MB, 2)
Write-Host ""
Write-Host "Created: $OutputZip ($sizeMb MB)" -ForegroundColor Green
Write-Host ""
Write-Host "On server PC:" -ForegroundColor Yellow
Write-Host "  1. Unzip"
Write-Host "  2. Double-click INSTALL.bat"
Write-Host "  3. Double-click START-WEBSITE.bat"
Write-Host "  4. Open https://app.ahsteellab.com/login"
