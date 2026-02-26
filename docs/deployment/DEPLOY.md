# BenimMasalim — Deploy & Sunucu Bilgileri

> Son güncelleme: 2026-02-13

---

## 1. Genel Mimari

```
Kullanıcı (tarayıcı)
    │
    ▼
GCP Global HTTPS Load Balancer  (IP: 35.190.26.191)
    │
    ├── benimmasalim.com.tr      → Cloud Run: benimmasalim-frontend
    └── /api/*  (proxy)          → Cloud Run: benimmasalim-backend
                                        │
                                        ├── Cloud SQL (PostgreSQL 15)
                                        ├── Cloud Storage (4 bucket)
                                        ├── Google Gemini API
                                        └── Secret Manager (9 secret)
```

---

## 2. GCP Proje Bilgileri

| Bilgi             | Değer                                  |
|-------------------|----------------------------------------|
| **Proje ID**      | `gen-lang-client-0784096400`           |
| **Bölge**         | `europe-west1` (Belçika)               |
| **Domain**        | `benimmasalim.com.tr`                  |
| **Statik IP**     | `35.190.26.191`                        |

---

## 3. Cloud Run Servisleri

### 3.1 Backend (`benimmasalim-backend`)

| Parametre            | Değer                                                            |
|----------------------|------------------------------------------------------------------|
| **Image**            | `europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest` |
| **URL (internal)**   | `https://benimmasalim-backend-554846094227.europe-west1.run.app` |
| **Aktif Revision**   | `benimmasalim-backend-00054-wbc`                                 |
| **CPU**              | 2 vCPU                                                          |
| **Memory**           | 4 GiB                                                           |
| **Timeout**          | 600 saniye                                                      |
| **Max Instances**    | 5                                                                |
| **Concurrency**      | 80                                                               |
| **CPU Throttling**   | Kapalı (her zaman CPU ayrılmış)                                 |
| **Startup CPU Boost**| Açık                                                            |
| **Cloud SQL**        | `gen-lang-client-0784096400:europe-west1:benimmasalim-db`        |
| **Framework**        | Python 3.11 + FastAPI + SQLAlchemy 2.x (async) + Alembic        |
| **Port**             | 8000                                                             |

#### Backend Ortam Değişkenleri

| Değişken                            | Değer / Kaynak                       |
|-------------------------------------|--------------------------------------|
| `APP_ENV`                           | `production`                         |
| `DEBUG`                             | `false`                              |
| `JWT_ALGORITHM`                     | `HS256`                              |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`   | `1440`                               |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS`     | `7`                                  |
| `BEHIND_PROXY`                      | `true`                               |
| `DB_POOL_SIZE`                      | `10`                                 |
| `DB_MAX_OVERFLOW`                   | `5`                                  |
| `GCP_PROJECT_ID`                    | `gen-lang-client-0784096400`         |
| `STORAGE_DRIVER`                    | `gcs`                                |
| `SMTP_HOST`                         | `smtp.gmail.com`                     |
| `SMTP_PORT`                         | `587`                                |
| `SMTP_USER`                         | `benimmasalim.34@gmail.com`          |
| `SMTP_FROM_NAME`                    | `Benim Masalim`                      |
| `LOG_LEVEL`                         | `INFO`                               |
| `FRONTEND_URL`                      | `https://benimmasalim.com.tr`        |
| `KVKK_RETENTION_DAYS`              | `30`                                 |
| `AUTO_DELETE_ENABLED`               | `true`                               |
| `SECRET_KEY`                        | Secret Manager                       |
| `JWT_SECRET_KEY`                    | Secret Manager                       |
| `WEBHOOK_SECRET`                    | Secret Manager                       |
| `DATABASE_URL`                      | Secret Manager                       |
| `GEMINI_API_KEY`                    | Secret Manager                       |
| `SMTP_PASSWORD`                     | Secret Manager                       |

### 3.2 Worker (`benimmasalim-worker`)

| Parametre            | Değer                                                              |
|----------------------|--------------------------------------------------------------------|
| **Image**            | `europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest` |
| **URL (internal)**   | `https://benimmasalim-worker-554846094227.europe-west1.run.app`    |
| **Command**          | `python -m app.workers.run_worker`                                 |
| **CPU**              | 2 vCPU                                                            |
| **Memory**           | 4 GiB                                                             |
| **Timeout**          | 1800 saniye (30 dk)                                               |
| **Min Instances**    | 2                                                                  |
| **Max Instances**    | 5                                                                  |
| **Concurrency**      | 1 (her instance tek health-check)                                  |
| **Framework**        | Arq (async Redis job queue) + health HTTP server                   |
| **Port**             | 8080 (health check only)                                           |
| **Görev**            | Redis kuyruğundan iş alarak görsel üretimi yapar                   |

### 3.3 Frontend (`benimmasalim-frontend`)

| Parametre            | Değer                                                              |
|----------------------|--------------------------------------------------------------------|
| **Image**            | `europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend:latest` |
| **URL (internal)**   | `https://benimmasalim-frontend-554846094227.europe-west1.run.app`  |
| **Aktif Revision**   | `benimmasalim-frontend-00013-bjp`                                  |
| **CPU**              | 1 vCPU                                                            |
| **Memory**           | 1 GiB                                                             |
| **Timeout**          | 300 saniye                                                        |
| **Max Instances**    | 3                                                                  |
| **Framework**        | Next.js 14 (App Router) + React + Tailwind CSS                    |
| **Port**             | 3000                                                               |
| **Docker Target**    | `runner` (production build)                                        |

#### Frontend Ortam Değişkenleri

| Değişken                  | Değer                                                              |
|---------------------------|--------------------------------------------------------------------|
| `NODE_ENV`                | `production`                                                       |
| `NEXT_TELEMETRY_DISABLED` | `1`                                                                |
| `BACKEND_INTERNAL_URL`    | `https://benimmasalim-backend-554846094227.europe-west1.run.app`   |
| `NEXT_PUBLIC_API_URL`     | `https://benimmasalim-backend-554846094227.europe-west1.run.app/api/v1` |
| `NEXT_PUBLIC_SITE_URL`    | `https://benimmasalim.com.tr`                                      |

---

## 4. Veritabanı (Cloud SQL)

| Parametre          | Değer                                       |
|--------------------|---------------------------------------------|
| **Instance**       | `benimmasalim-db`                           |
| **Connection**     | `gen-lang-client-0784096400:europe-west1:benimmasalim-db` |
| **Motor**          | PostgreSQL 15                               |
| **Tier**           | `db-f1-micro` (1 shared vCPU, 0.6 GB RAM)  |
| **Disk**           | 10 GB SSD                                   |
| **Bölge**          | `europe-west1`                              |
| **Public IP**      | Açık (bağlantı Cloud SQL Proxy üzerinden)   |
| **Migration Tool** | Alembic                                     |

---

## 5. Cloud Storage Bucket'ları

| Bucket Adı                      | Kullanım            | Bölge          |
|---------------------------------|----------------------|----------------|
| `benimmasalim-raw-uploads`      | Kullanıcı fotoğrafları (ham) | EUROPE-WEST1 |
| `benimmasalim-generated-books`  | Oluşturulan PDF'ler | EUROPE-WEST1   |
| `benimmasalim-images`           | AI üretilen görseller | EUROPE-WEST1  |
| `benimmasalim-audio-files`      | Sesli kitap dosyaları | EUROPE-WEST1  |

---

## 6. Secret Manager

| Secret Adı            | Açıklama                           |
|------------------------|------------------------------------|
| `DATABASE_URL`         | PostgreSQL bağlantı URI            |
| `SECRET_KEY`           | Uygulama gizli anahtarı            |
| `JWT_SECRET_KEY`       | JWT token imzalama anahtarı        |
| `WEBHOOK_SECRET`       | Webhook doğrulama anahtarı         |
| `GEMINI_API_KEY`       | Google Gemini AI API anahtarı      |
| `SMTP_PASSWORD`        | Gmail SMTP şifresi                 |
| `FAL_API_KEY`          | Fal.ai API anahtarı (kullanılmıyor)|
| `ELEVENLABS_API_KEY`   | ElevenLabs ses klonlama anahtarı   |
| `REDIS_URL`            | Upstash Redis bağlantı URI (TLS, aktif) |

---

## 7. Load Balancer & SSL

| Bileşen                | Değer                              |
|------------------------|------------------------------------|
| **Statik IP**          | `35.190.26.191` (`benimmasalim-ip`)|
| **HTTPS Proxy**        | `benimmasalim-https-proxy`         |
| **HTTP Proxy**         | `benimmasalim-http-proxy` (→ HTTPS redirect) |
| **SSL Sertifikası 1**  | `benimmasalim-comtr-cert` — `benimmasalim.com.tr` (ACTIVE) |
| **SSL Sertifikası 2**  | `benimmasalim-www-cert-v2` — `www.benimmasalim.com.tr` (ACTIVE) |
| **Forwarding Rules**   | `benimmasalim-http-rule` + `benimmasalim-https-rule` |

---

## 8. Artifact Registry

| Parametre  | Değer                                                         |
|------------|---------------------------------------------------------------|
| **Repo**   | `europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim` |
| **Format** | Docker                                                         |
| **Bölge**  | `europe-west1`                                                 |

---

## 9. DNS Ayarları (benimmasalim.com.tr)

| Kayıt Tipi | Host  | Değer            |
|------------|-------|-------------------|
| A          | @     | `35.190.26.191`   |
| CNAME      | www   | `benimmasalim.com.tr.` |

---

## 10. Deploy Komutları

**Tek komutla (PowerShell):** Proje kökünden `.\scripts\deploy.ps1` — build + push + Cloud Run güncelleme. Sadece build için: `.\scripts\deploy.ps1 -BuildOnly`.

### Backend Deploy

```bash
# 1. Docker image build
cd backend
docker build -t europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest .

# 2. Push
docker push europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest

# 3. Deploy to Cloud Run
gcloud run services update benimmasalim-backend \
  --region=europe-west1 \
  --image=europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest
```

### Frontend Deploy

```bash
# 1. Docker image build (production target)
cd frontend
docker build --target runner \
  -t europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend:latest .

# 2. Push
docker push europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend:latest

# 3. Deploy to Cloud Run
gcloud run services update benimmasalim-frontend \
  --region=europe-west1 \
  --image=europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend:latest
```

### Veritabanı Migration

**Deploy sonrası (önerilen):** `.\scripts\post-deploy.ps1` — Cloud Run migration job + health check.

**Cloud Run job ile:**
```bash
gcloud run jobs execute benimmasalim-migrate --region=europe-west1 --project=gen-lang-client-0784096400 --wait
```

**Cloud SQL Proxy ile (lokal):**
```bash
cloud-sql-proxy gen-lang-client-0784096400:europe-west1:benimmasalim-db --port=5433
cd backend
DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head
```

### Deploy Sonrası Adımlar

1. **Migration:** `.\scripts\post-deploy.ps1` veya yukarıdaki `gcloud run jobs execute benimmasalim-migrate ...`
2. **Health check:** Backend `GET /health` → 200, Frontend `/` → 200
3. **Log kontrol:** Hata varsa `gcloud logging read ...` (bkz. §11)

---

## 11. Faydalı Komutlar

```bash
# Backend logları (son 5 dk)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-backend" \
  --limit=30 --freshness=5m --format=json

# Frontend logları
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-frontend" \
  --limit=30 --freshness=5m --format=json

# Sadece hataları göster
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-backend AND severity>=ERROR" \
  --limit=10 --freshness=30m --format=json

# Cloud Run revision listesi
gcloud run revisions list --service=benimmasalim-backend --region=europe-west1
gcloud run revisions list --service=benimmasalim-frontend --region=europe-west1

# Secret güncelle
echo -n "yeni-deger" | gcloud secrets versions add SECRET_ADI --data-file=-

# Cloud SQL'e bağlan
gcloud sql connect benimmasalim-db --user=postgres
```

---

## 12. Mimari Notlar

- **API Proxy**: Frontend, `/api/*` isteklerini `src/app/api/[...path]/route.ts` üzerinden 180s timeout ile backend'e proxy eder.
- **AI Hikaye Üretimi**: Google Gemini `gemini-2.0-flash` ile iki aşamalı (Pass 1: hikaye yazma, Pass 2: JSON formatlama) üretim. Her iki aşamada 429 rate limit retry mekanizması var.
- **AI Görsel Üretimi**: Google Gemini `gemini-2.5-flash-image` ile. Real-ESRGAN 4x upscale + LANCZOS resize ile baskı kalitesine ulaşılır.
- **PDF Üretimi**: `page_composer.py` ile Pillow tabanlı sayfa kompozisyonu + `pdf_service.py` ile PDF birleştirme.
- **E-posta**: Gmail SMTP üzerinden sipariş onay ve PDF teslim mailleri.
- **KVKK**: 30 gün sonra otomatik veri silme (`AUTO_DELETE_ENABLED=true`).
