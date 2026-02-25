# BenimMasalim - Backend + Frontend Docker build ve Google Artifact Registry'ye push
# Gereksinim: gcloud CLI, Docker (Cloud Build kullanmıyorsanız)
#
# Yontem 1 - Cloud Build (Google sunucuda build, otomatik push):
#   .\scripts\build-push-google.ps1 -UseCloudBuild
#
# Yontem 2 - Yerel Docker build + push:
#   .\scripts\build-push-google.ps1
#   (Once: gcloud auth configure-docker europe-west1-docker.pkg.dev)

param(
    [switch]$UseCloudBuild,
    [string]$ProjectId = "",
    [string]$Region = "europe-west1",
    [string]$Repo = "benimmasalim",
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"
# Script scripts/build-push-google.ps1 -> proje kökü bir üst dizin
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path $Root)) { $Root = (Get-Location).Path }

if ($UseCloudBuild) {
    Write-Host "Cloud Build ile build + push (Google sunucuda)..." -ForegroundColor Cyan
    $cmd = "gcloud", "builds", "submit", "--config", "cloudbuild.yaml", "--substitutions", "_REGION=$Region,_REPO=$Repo,_TAG=$Tag", $Root
    if ($ProjectId) { $cmd += @("--project", $ProjectId) }
    & $cmd[0] $cmd[1..($cmd.Length-1)]
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Bitti. Image'lar Artifact Registry'de." -ForegroundColor Green
    exit 0
}

# Yerel Docker build + push
$Registry = "${Region}-docker.pkg.dev"
$FullRepo = "${Registry}/${ProjectId}/${Repo}"
if (-not $ProjectId) {
    $ProjectId = (gcloud config get-value project 2>$null)
    if (-not $ProjectId) { Write-Error "ProjectId gerekli. -ProjectId XXX veya gcloud config set project XXX" }
    $FullRepo = "${Registry}/${ProjectId}/${Repo}"
}

Write-Host "Docker ile yerel build + push (registry: $FullRepo)..." -ForegroundColor Cyan
Write-Host "Docker login: gcloud auth configure-docker $Registry" -ForegroundColor Yellow

# Backend
Push-Location (Join-Path $Root "backend")
docker build -t "${FullRepo}/backend:${Tag}" .
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
docker push "${FullRepo}/backend:${Tag}"
$be = $LASTEXITCODE
Pop-Location
if ($be -ne 0) { exit $be }

# Frontend
Push-Location (Join-Path $Root "frontend")
docker build --target runner -t "${FullRepo}/frontend:${Tag}" .
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
docker push "${FullRepo}/frontend:${Tag}"
$fe = $LASTEXITCODE
Pop-Location
if ($fe -ne 0) { exit $fe }

Write-Host "Bitti. backend:${Tag} ve frontend:${Tag} push edildi." -ForegroundColor Green
