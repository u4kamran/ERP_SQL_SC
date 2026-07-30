#Requires -Version 5.1
<#
.SYNOPSIS
    Generate random SECRET_KEY and CSRF_SECRET_KEY for production .env
#>

$key = [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Maximum 256 }))
$csrf = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))

Write-Host "Add these to your .env file:" -ForegroundColor Cyan
Write-Host ""
Write-Host "SECRET_KEY=$key"
Write-Host "CSRF_SECRET_KEY=$csrf"
Write-Host ""
