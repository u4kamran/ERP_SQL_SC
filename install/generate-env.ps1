#Requires -Version 5.1
<#
.SYNOPSIS
    Create .env from install/env.shahenhp with random secrets.
#>

param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$template = Join-Path $PSScriptRoot "env.shahenhp"
$target = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $template)) {
    throw "Template not found: $template"
}

if ((Test-Path $target) -and -not $Force) {
    Write-Host '.env already exists - keeping your current file.' -ForegroundColor Yellow
    exit 0
}

$secretKey = [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
$csrfKey = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))

$content = Get-Content -Path $template -Raw -Encoding UTF8
$content = $content.Replace('__GENERATE_SECRET_KEY__', $secretKey)
$content = $content.Replace('__GENERATE_CSRF_KEY__', $csrfKey)

[System.IO.File]::WriteAllText($target, $content)
Write-Host 'Created .env from install\env.shahenhp' -ForegroundColor Green
