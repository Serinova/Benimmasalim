# E2E Docker verification: migrations, DB columns, optional order flow.
# Run from repo root: .\scripts\e2e_docker_verify.ps1
# Optional env: $E2E_CHILD_PHOTO_URL (public URL), $E2E_RUN_ORDER = "1" to run full order flow.

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path "$root\docker-compose.yml")) { $root = (Get-Location).Path }
Set-Location $root

Write-Host "=== 1) Docker Compose ===" -ForegroundColor Cyan
docker compose ps
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: docker compose up -d --build" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n=== 2) Migrations ===" -ForegroundColor Cyan
docker compose exec -T backend alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "`n=== 3) Verify story_previews columns ===" -ForegroundColor Cyan
$cols = docker compose exec -T postgres psql -U postgres -d benimmasalim -t -c "SELECT string_agg(column_name, ' ') FROM information_schema.columns WHERE table_name = 'story_previews' AND column_name IN ('prompt_debug_json', 'generation_manifest_json');"
if ($cols -notmatch "prompt_debug_json|generation_manifest_json") {
    Write-Host "Missing columns. Got: $cols" -ForegroundColor Red
    exit 1
}
Write-Host "OK: prompt_debug_json and generation_manifest_json exist" -ForegroundColor Green

Write-Host "`n=== 4) Health ===" -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "Backend health: $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Backend not reachable: $_" -ForegroundColor Yellow
}

if ($env:E2E_RUN_ORDER -eq "1" -and $env:E2E_CHILD_PHOTO_URL) {
    Write-Host "`n=== 5) E2E order flow (story -> submit -> confirm) ===" -ForegroundColor Cyan
    $photoUrl = $env:E2E_CHILD_PHOTO_URL
    $body = @{
        child_name = "Efe"
        child_age = 6
        child_gender = "erkek"
        child_photo_url = $photoUrl
        scenario_name = "Kapadokya"
        scenario_prompt = "Kapadokya macerasi"
        learning_outcomes = @("Eglenceli macera")
        visual_style = "2D childrens picture-book cartoon illustration"
        clothing_description = "kirmizi mont, mavi pantolon, beyaz spor ayakkabi"
        page_count = 2
    } | ConvertTo-Json -Depth 5

    $storyResp = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ai/test-story-structured" -Method POST -Body $body -ContentType "application/json; charset=utf-8"
    # V2: response has story.title / story.pages (not top-level)
    if ($storyResp.story) {
        $title = $storyResp.story.title
        $pages = $storyResp.story.pages
    } else {
        $title = $storyResp.title
        $pages = $storyResp.pages
    }
    if (-not $pages -or $pages.Count -lt 2) {
        Write-Host "Story did not return 2 pages. Response: $($storyResp | ConvertTo-Json -Depth 3 | Select-Object -First 500)" -ForegroundColor Red
        exit 1
    }
    Write-Host "Story title: $title ($($pages.Count) pages)" -ForegroundColor Green

    $submitBody = @{
        parent_name = "E2E Parent"
        parent_email = "e2e@example.com"
        child_name = "Efe"
        child_age = 6
        child_gender = "erkek"
        child_photo_url = $photoUrl
        clothing_description = "kirmizi mont, mavi pantolon, beyaz spor ayakkabi"
        story_title = $title
        story_pages = @(
            @{ page_number = 0; text = $pages[0].text; visual_prompt = $pages[0].visual_prompt },
            @{ page_number = 1; text = $pages[1].text; visual_prompt = $pages[1].visual_prompt }
        )
        visual_style = "2D childrens picture-book cartoon illustration"
        scenario_name = "Kapadokya"
    } | ConvertTo-Json -Depth 6

    $submitResp = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/orders/submit-preview-async" -Method POST -Body $submitBody -ContentType "application/json; charset=utf-8"
    $previewId = $submitResp.preview_id
    Write-Host "Preview ID: $previewId" -ForegroundColor Green

    $tokenRow = docker compose exec -T postgres psql -U postgres -d benimmasalim -t -A -c "SELECT confirmation_token FROM story_previews WHERE id = '$previewId'::uuid;"
    $token = ($tokenRow -replace "\s+", "").Trim()
    if (-not $token) {
        Write-Host "Could not get confirmation_token for $previewId" -ForegroundColor Red
        exit 1
    }
    Write-Host "Confirmation token: ${token.Substring(0, [Math]::Min(12, $token.Length))}..." -ForegroundColor Gray

    Write-Host "Waiting 45s for background image generation..." -ForegroundColor Yellow
    Start-Sleep -Seconds 45

    $confirmResp = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/orders/confirm/$token" -Method GET
    Write-Host "Confirm: $($confirmResp.message)" -ForegroundColor Green
    Write-Host "Preview ID for DB/log inspection: $previewId" -ForegroundColor Cyan
    Write-Host "Run: docker compose logs backend --tail=300 | grep -E 'PROMPT_DEBUG|reference_image_used'"
    Write-Host "DB: SELECT prompt_debug_json, generation_manifest_json FROM story_previews WHERE id = '$previewId'::uuid;"
} else {
    Write-Host "`nSkipping order flow. Set E2E_CHILD_PHOTO_URL and E2E_RUN_ORDER=1 to run." -ForegroundColor Gray
}

Write-Host "`nDone." -ForegroundColor Green
