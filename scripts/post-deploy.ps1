# BenimMasalim - Deploy sonrasi adimlar: migration + health check
# Kullanim: .\scripts\post-deploy.ps1
# deploy.ps1 calistirdiktan sonra bu scripti calistirin.

$ErrorActionPreference = "Stop"
$ProjectId = "gen-lang-client-0784096400"
$Region = "europe-west1"
$BackendUrl = "https://benimmasalim-backend-554846094227.${Region}.run.app"
$FrontendUrl = "https://benimmasalim-frontend-554846094227.${Region}.run.app"

Write-Host "=== BenimMasalim Post-Deploy ===" -ForegroundColor Cyan

# 1) Sync migration job image with latest backend
$BackendImage = "${Region}-docker.pkg.dev/${ProjectId}/benimmasalim/backend:latest"
Write-Host "[1/3] Updating migration job image..." -ForegroundColor Yellow
gcloud run jobs update benimmasalim-migrate --region=$Region --project=$ProjectId --image=$BackendImage --quiet
if ($LASTEXITCODE -ne 0) { throw "Migration job image update failed." }

# 2) Migration
Write-Host "[2/3] Running DB migration (Cloud Run job)..." -ForegroundColor Yellow
gcloud run jobs execute benimmasalim-migrate --region=$Region --project=$ProjectId --wait
if ($LASTEXITCODE -ne 0) { throw "Migration job failed." }
Write-Host "Migration OK." -ForegroundColor Green

# 3) Health check
Write-Host "[3/3] Health check..." -ForegroundColor Yellow
$backend = (Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -Method Get).StatusCode
$frontend = (Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -Method Get).StatusCode
if ($backend -ne 200) { throw "Backend health failed: $backend" }
if ($frontend -ne 200) { throw "Frontend health failed: $frontend" }
Write-Host "Backend: $backend  Frontend: $frontend  OK." -ForegroundColor Green

Write-Host "`nPost-deploy tamamlandi." -ForegroundColor Green
