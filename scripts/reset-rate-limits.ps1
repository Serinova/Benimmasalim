# Rate limitleri sifirla (Redis'teki tum IP sayaclari). Admin token gerekir.
# Kullanim: .\scripts\reset-rate-limits.ps1
# Ortam: $env:ADMIN_TOKEN = "Bearer eyJ..."  veya  -Token "eyJ..."

param([string]$Token = $env:ADMIN_TOKEN)

$BackendUrl = "https://benimmasalim-backend-554846094227.europe-west1.run.app"
$Uri = "$BackendUrl/api/v1/admin/rate-limit/reset-all"

if (-not $Token) {
    Write-Host "ADMIN_TOKEN gerekli. Ornek: `$env:ADMIN_TOKEN='Bearer eyJ...'; .\scripts\reset-rate-limits.ps1" -ForegroundColor Red
    exit 1
}
if (-not $Token.StartsWith("Bearer ")) { $Token = "Bearer " + $Token }

try {
    $r = Invoke-RestMethod -Uri $Uri -Method Post -Headers @{ Authorization = $Token } -ContentType "application/json"
    Write-Host "Rate limitler sifirlandi." -ForegroundColor Green
    Write-Host ($r | ConvertTo-Json)
} catch {
    Write-Host "Hata: $_" -ForegroundColor Red
    exit 1
}
