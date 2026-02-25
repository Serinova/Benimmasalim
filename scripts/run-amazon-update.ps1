# Run Amazon Scenario Update via Admin API
# Usage: .\scripts\run-amazon-update.ps1

$backend_url = "https://benimmasalim-backend-554846094227.europe-west1.run.app"
$endpoint = "$backend_url/api/v1/admin/scenarios/scripts/update-amazon"

Write-Host "=== Amazon Scenario Update ===" -ForegroundColor Green
Write-Host "Endpoint: $endpoint"
Write-Host ""

# You need to provide admin JWT token
# Get it from your admin login in the browser (Developer Tools > Application > Local Storage)
Write-Host "Please provide your admin JWT token:" -ForegroundColor Yellow
$token = Read-Host "Token"

if (-not $token) {
    Write-Host "Error: Token required" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Calling endpoint..." -ForegroundColor Cyan

try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri $endpoint -Method Post -Headers $headers
    
    Write-Host ""
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Green
    Write-Host ($response | ConvertTo-Json -Depth 10)
}
catch {
    Write-Host ""
    Write-Host "Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body:" -ForegroundColor Red
        Write-Host $responseBody
    }
    exit 1
}
