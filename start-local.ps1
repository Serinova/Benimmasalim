# ============================================================================
# BenimMasalım — Lokal Geliştirme Başlatıcı
# ============================================================================
# Kullanım: .\start-local.ps1 [-SkipProxy] [-BackendOnly] [-FrontendOnly]
#
# Ne yapar:
#   1. Cloud SQL Proxy başlatır (production DB'ye tünel)
#   2. Redis kontrol eder
#   3. Backend (FastAPI) başlatır
#   4. Frontend (Next.js) başlatır
# ============================================================================

param(
    [switch]$SkipProxy,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

$PROJECT_ID = "gen-lang-client-0784096400"
$REGION = "europe-west1"
$INSTANCE = "${PROJECT_ID}:${REGION}:benimmasalim-db"
$PROXY_PORT = 5433

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BenimMasalim - Lokal Gelistirme" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 0. Onkosullar ──────────────────────────────────────────────────────────

# .env.local kontrol
if (-not (Test-Path ".env.local")) {
    Write-Host "HATA: .env.local dosyasi bulunamadi!" -ForegroundColor Red
    Write-Host "  .env.local dosyasini olusturun ve DATABASE_URL'deki sifrenizi girin." -ForegroundColor Yellow
    exit 1
}

# DATABASE_URL'de placeholder kontrol
$envContent = Get-Content ".env.local" -Raw
if ($envContent -match "YOUR_DB_PASSWORD_HERE") {
    Write-Host "HATA: .env.local'de DATABASE_URL sifresi girilmemis!" -ForegroundColor Red
    Write-Host "  DATABASE_URL satirindaki YOUR_DB_PASSWORD_HERE'i gercek sifre ile degistirin." -ForegroundColor Yellow
    exit 1
}

# ── 1. Cloud SQL Proxy ─────────────────────────────────────────────────────

if (-not $SkipProxy) {
    Write-Host "[1/4] Cloud SQL Proxy kontrol ediliyor..." -ForegroundColor Yellow

    # gcloud auth kontrol
    $authList = gcloud auth list --format="value(account)" 2>$null
    if (-not $authList) {
        Write-Host "  gcloud hesabi bulunamadi. Login yapiliyor..." -ForegroundColor Yellow
        gcloud auth login
        gcloud auth application-default login
    } else {
        Write-Host "  gcloud hesap: $($authList.Split("`n")[0])" -ForegroundColor Green
    }

    # Proxy zaten calisiyor mu?
    $proxyRunning = Get-Process -Name "cloud-sql-proxy", "cloud_sql_proxy" -ErrorAction SilentlyContinue
    if ($proxyRunning) {
        Write-Host "  Cloud SQL Proxy zaten calisiyor (PID: $($proxyRunning.Id -join ', '))" -ForegroundColor Green
    } else {
        # Proxy binary kontrol
        $proxyPath = $null
        if (Test-Path ".\cloud-sql-proxy.exe") {
            $proxyPath = ".\cloud-sql-proxy.exe"
        } elseif (Get-Command "cloud-sql-proxy" -ErrorAction SilentlyContinue) {
            $proxyPath = "cloud-sql-proxy"
        } elseif (Get-Command "cloud_sql_proxy" -ErrorAction SilentlyContinue) {
            $proxyPath = "cloud_sql_proxy"
        }

        if (-not $proxyPath) {
            Write-Host "  Cloud SQL Proxy bulunamadi! Indiriliyor..." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "  Otomatik indirme:" -ForegroundColor Cyan
            # Windows AMD64 binary indir
            $proxyUrl = "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.3/cloud-sql-proxy.x64.exe"
            try {
                Invoke-WebRequest -Uri $proxyUrl -OutFile "cloud-sql-proxy.exe" -UseBasicParsing
                $proxyPath = ".\cloud-sql-proxy.exe"
                Write-Host "  Cloud SQL Proxy indirildi!" -ForegroundColor Green
            } catch {
                Write-Host "  Indirme basarisiz. Manuel indirin:" -ForegroundColor Red
                Write-Host "  https://cloud.google.com/sql/docs/mysql/sql-proxy#install" -ForegroundColor Yellow
                exit 1
            }
        }

        Write-Host "  Cloud SQL Proxy baslatiliyor (port $PROXY_PORT)..." -ForegroundColor Yellow
        Start-Process -FilePath $proxyPath -ArgumentList "$INSTANCE --port=$PROXY_PORT --auto-iam-authn" -WindowStyle Minimized
        Start-Sleep -Seconds 3

        # Baglanti testi
        $proxyCheck = Get-Process -Name "cloud-sql-proxy", "cloud_sql_proxy" -ErrorAction SilentlyContinue
        if ($proxyCheck) {
            Write-Host "  Cloud SQL Proxy calisiyor (port $PROXY_PORT)" -ForegroundColor Green
        } else {
            Write-Host "  Cloud SQL Proxy baslatilamadi!" -ForegroundColor Red
            Write-Host "  Manuel baslatmayi deneyin:" -ForegroundColor Yellow
            Write-Host "    $proxyPath $INSTANCE --port=$PROXY_PORT" -ForegroundColor White
            exit 1
        }
    }
} else {
    Write-Host "[1/4] Cloud SQL Proxy atlandi (-SkipProxy)" -ForegroundColor DarkGray
}

# ── 2. Redis ───────────────────────────────────────────────────────────────

Write-Host "[2/4] Redis kontrol ediliyor..." -ForegroundColor Yellow
try {
    $redisCheck = redis-cli ping 2>$null
    if ($redisCheck -eq "PONG") {
        Write-Host "  Redis calisiyor" -ForegroundColor Green
    } else {
        throw "Redis yanit vermedi"
    }
} catch {
    Write-Host "  Redis bulunamadi veya calismiyior." -ForegroundColor Yellow
    Write-Host "  Rate limiting ve arq worker Redis gerektirir." -ForegroundColor Yellow
    Write-Host "  Redis olmadan backend calisir ama bazi ozellikler devre disi kalir." -ForegroundColor Yellow
    Write-Host "  Redis baslatmak icin: docker run -d -p 6379:6379 redis:7-alpine" -ForegroundColor DarkGray
}

# ── 3. Backend ─────────────────────────────────────────────────────────────

if (-not $FrontendOnly) {
    Write-Host "[3/4] Backend baslatiliyor (port 8000)..." -ForegroundColor Yellow

    # Python venv kontrol
    $venvPath = "backend\.venv"
    if (Test-Path "$venvPath\Scripts\activate.ps1") {
        Write-Host "  Python venv bulundu" -ForegroundColor Green
    } else {
        Write-Host "  UYARI: backend\.venv bulunamadi" -ForegroundColor Yellow
        Write-Host "  Olusturmak icin: cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor DarkGray
    }

    # Backend'i yeni terminal'de baslat
    $backendCmd = @"
cd "$PSScriptRoot\backend"
if (Test-Path '.venv\Scripts\activate.ps1') { & '.venv\Scripts\activate.ps1' }
`$env:ENV_FILE = "$PSScriptRoot\.env.local"
Write-Host 'Backend baslatiliyor...' -ForegroundColor Cyan
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
    Write-Host "  Backend terminali acildi" -ForegroundColor Green
} else {
    Write-Host "[3/4] Backend atlandi (-FrontendOnly)" -ForegroundColor DarkGray
}

# ── 4. Frontend ────────────────────────────────────────────────────────────

if (-not $BackendOnly) {
    Write-Host "[4/4] Frontend baslatiliyor (port 3000)..." -ForegroundColor Yellow

    $frontendCmd = @"
cd "$PSScriptRoot\frontend"
Write-Host 'Frontend baslatiliyor...' -ForegroundColor Cyan
npm run dev
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd
    Write-Host "  Frontend terminali acildi" -ForegroundColor Green
} else {
    Write-Host "[4/4] Frontend atlandi (-BackendOnly)" -ForegroundColor DarkGray
}

# ── Ozet ───────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Lokal gelistirme ortami hazir!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  DB Proxy: 127.0.0.1:$PROXY_PORT -> Cloud SQL" -ForegroundColor White
Write-Host ""
Write-Host "  Durdurmak icin: acilan terminal pencerelerini kapatin" -ForegroundColor DarkGray
Write-Host "  Cloud SQL Proxy: Get-Process cloud-sql-proxy | Stop-Process" -ForegroundColor DarkGray
Write-Host ""
