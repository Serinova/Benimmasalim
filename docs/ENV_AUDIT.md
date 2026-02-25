# ENV Dosyaları Analizi

## Mevcut ENV Dosyaları

| Dosya | Kullanım | DATABASE_URL |
|-------|----------|--------------|
| `.env` (proje kökü) | Backend + Docker env_file | `postgres:postgres@localhost:5432/benimmasalim` ✅ |
| `backend/.env` | Backend config (cwd'ye göre) | `postgres:postgres@localhost:5432/benimmasalim` ✅ |
| `frontend/.env.local` | Next.js (varsa) | - |
| `.env.example` | Şablon | postgres ✅ |

## Config Yükleme Sırası (backend)

`app/config.py`: `env_file=[proje_kökü/.env, ".env"]`. Cwd=backend ise ".env" = backend/.env.

1. Proje kökü `.env` yüklenir.
2. `backend/.env` (aynı key’ler override) yüklenir.
3. **Sistem ortam değişkenleri** en yüksek öncelik.

**run_dev.ps1:** Başlamadan önce sistem `DATABASE_URL` silinir (sadece .env kullanılır). Postgres (127.0.0.1:5432) hazır olana kadar en fazla 30 sn beklenir.

## "herosteps" Hatası Kaynağı

HeroSteps başka bir proje (Google Cloud'da çalışıyor). Lokal HeroSteps container/network kaldırıldı.

`herosteps` hatası: Sistem veya shell ortamında `DATABASE_URL=...herosteps...` tanımlıysa .env override edilir.

**Kontrol:**
```powershell
[Environment]::GetEnvironmentVariable("DATABASE_URL", "User")
[Environment]::GetEnvironmentVariable("DATABASE_URL", "Machine")
$env:DATABASE_URL
```

**Çözüm:** `run_dev.ps1` her çalıştırmada sistem DATABASE_URL’i kaldırır. Elle: `Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue`

## Docker vs Yerel

| Ortam | DATABASE_URL |
|-------|----------------------|
| **Docker (backend container)** | compose `environment:` → `postgres:postgres@postgres:5432/benimmasalim` |
| **Yerel (run_dev.ps1)** | .env dosyaları (sistem DATABASE_URL script ile temizlenir) → `localhost:5432` (Docker postgres map’li) |

## Öneri

Backend’i **her zaman** `.\backend\run_dev.ps1` ile başlatın; aynı proje .env ve Postgres bekleme kullanılır. Tek DB: Docker’daki postgres (port 5432).
