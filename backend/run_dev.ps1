# Backend geliştirme sunucusu - Frontend proxy (127.0.0.1:8000) bu porta bağlanır.
# Proje kökünden: .\backend\run_dev.ps1   veya  cd backend; .\run_dev.ps1
# Veritabanı: Docker'da postgres (port 5432). Backend her zaman .env dosyasındaki DATABASE_URL kullanır.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot

# Sistem/shell DATABASE_URL'ini kaldır — sadece proje .env kullanılsın (başka proje DB'sine bağlanmayı önler)
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
# Backend config: app/config.py proje kökü .env + backend/.env yükler; DATABASE_URL oradan gelir.

# Postgres hazır olana kadar bekle (Docker bazen geç ayağa kalkar — bazen bağlanıyor bazen bağlanmıyor sorununu önler)
$maxWait = 30
$waited = 0
Write-Host "Postgres kontrol ediliyor (127.0.0.1:5432)..." -ForegroundColor Gray
while ($waited -lt $maxWait) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 5432)
        $tcp.Close()
        Write-Host "Postgres hazir (${waited}s)." -ForegroundColor Green
        break
    } catch {
        $waited += 2
        if ($waited -lt $maxWait) { Start-Sleep -Seconds 2 }
    }
}
if ($waited -ge $maxWait) {
    Write-Warning "Postgres 30 sn icinde yanit vermedi. 'docker compose up -d' ile postgres'i baslattiniz mi? Yine de backend baslatiliyor."
}

Write-Host "Backend baslatiliyor: http://0.0.0.0:8000 (health: http://localhost:8000/health)" -ForegroundColor Cyan
# uv run ile calistir (pyproject.toml + uv.lock); python yoksa: winget install Python.Python.3.12 veya uv kur: pip install uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
