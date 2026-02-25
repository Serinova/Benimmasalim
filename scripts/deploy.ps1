# BenimMasalim - Docker build & GCP Cloud Run deploy
# Kullanim: .\scripts\deploy.ps1   veya   .\scripts\deploy.ps1 -BuildOnly
# Gereksinim: gcloud CLI, Docker, proje icin gcloud auth login + docker configure-docker

$ErrorActionPreference = "Stop"
$ProjectId = "gen-lang-client-0784096400"
$Region = "europe-west1"
$Registry = "${Region}-docker.pkg.dev/${ProjectId}/benimmasalim"
$BackendImage = "${Registry}/backend:latest"
$FrontendImage = "${Registry}/frontend:latest"
# Frontend build-time: rewrite /health -> backend
$BackendInternalUrl = "https://benimmasalim-backend-554846094227.${Region}.run.app"

$Root = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $Root

Write-Host "=== BenimMasalim Build & Deploy ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId  Region: $Region`n"

# 1) Backend
Write-Host "[1/6] Building backend image..." -ForegroundColor Yellow
Set-Location "$Root\backend"
docker build -t $BackendImage .
if ($LASTEXITCODE -ne 0) { throw "Backend build failed." }

# 2) Frontend (production: client calls backend directly via NEXT_PUBLIC_API_URL)
Write-Host "[2/6] Building frontend image (runner)..." -ForegroundColor Yellow
Set-Location "$Root\frontend"
$ApiBaseUrl = "$BackendInternalUrl/api/v1"
docker build --target runner --build-arg BACKEND_INTERNAL_URL=$BackendInternalUrl --build-arg NEXT_PUBLIC_API_URL=$ApiBaseUrl -t $FrontendImage .
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }

Set-Location $Root

if ($args -contains "-BuildOnly") {
    Write-Host "`nBuildOnly: images built. Push and deploy skipped." -ForegroundColor Green
    exit 0
}

# 3) Docker auth Artifact Registry
Write-Host "[3/6] Configuring Docker for Artifact Registry..." -ForegroundColor Yellow
gcloud auth configure-docker "${Region}-docker.pkg.dev" --quiet
if ($LASTEXITCODE -ne 0) { throw "Docker configure failed." }

# 4) Push
Write-Host "[4/6] Pushing backend image..." -ForegroundColor Yellow
docker push $BackendImage
if ($LASTEXITCODE -ne 0) { throw "Backend push failed." }
Write-Host "[5/6] Pushing frontend image..." -ForegroundColor Yellow
docker push $FrontendImage
if ($LASTEXITCODE -ne 0) { throw "Frontend push failed." }

# 5) Deploy Cloud Run (frontend needs BACKEND_INTERNAL_URL for API proxy)
Write-Host "[6/6] Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run services update benimmasalim-backend --region=$Region --image=$BackendImage --project=$ProjectId --timeout=3600 --quiet
gcloud run services update benimmasalim-worker  --region=$Region --image=$BackendImage --project=$ProjectId --max-instances=10 --timeout=3600 --quiet
gcloud run services update benimmasalim-frontend --region=$Region --image=$FrontendImage --project=$ProjectId --set-env-vars "BACKEND_INTERNAL_URL=$BackendInternalUrl" --quiet

Write-Host "`nDeploy tamamlandi." -ForegroundColor Green
Write-Host "Backend:  https://benimmasalim-backend-554846094227.${Region}.run.app"
Write-Host "Frontend: https://benimmasalim-frontend-554846094227.${Region}.run.app"
Write-Host "`nSonraki adim: .\scripts\post-deploy.ps1  (migration + health check)"
