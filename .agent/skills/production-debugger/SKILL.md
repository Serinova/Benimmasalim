---
name: Production Debugger
description: Canlı sunucuda (Production) hata teşhisi ve çözümü için ZORUNLU beceri. Kullanıcı "logları kontrol et", "hata var", "sunucu problemi", "debug" veya `/debug` dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# Production Debugger (Prodüksiyon Hata Teşhis Becerisi)

Benim Masalım projesinin canlı ortamındaki hataları teşhis edip çözmek için uygulaman gereken sistematik adımlardır.

## ⚠️ Tetikleyiciler

Bu skill aşağıdaki durumlarda otomatik olarak aktifleşir:
- Kullanıcı "hata var", "çalışmıyor", "problem var", "logları kontrol et" dediğinde
- Kullanıcı `/debug` komutu verdiğinde
- Kullanıcı "sunucu crash", "500 hatası", "ödeme problemi" gibi canlı ortam sorunları bildirdiğinde

---

## 🔍 Teşhis Adımları (Sırayla Uygula)

### Adım 1: Problemin Kapsamını Belirle

Kullanıcıdan şu bilgileri al:
- **Hangi servis?** (frontend / backend / worker)
- **Ne zaman başladı?**
- **Hata mesajı var mı?** (ekran görüntüsü, console hatası vb.)
- **Tekrarlanabiliyor mu?**

### Adım 2: Cloud Run Servis Durumunu Kontrol Et

```powershell
# Backend durumu
gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"

# Worker durumu
gcloud run services describe benimmasalim-worker --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"

# Frontend durumu
gcloud run services describe benimmasalim-frontend --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"
```

### Adım 3: Son Logları Oku

```powershell
# Backend — son 50 log (hatalar öncelikli)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-backend AND severity>=ERROR" --project=gen-lang-client-0784096400 --limit=20 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error, jsonPayload.path)" --freshness=1h

# Worker — son hatalar
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-worker AND severity>=ERROR" --project=gen-lang-client-0784096400 --limit=20 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error)" --freshness=1h

# Frontend — son hatalar
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-frontend AND severity>=ERROR" --project=gen-lang-client-0784096400 --limit=20 --format="table(timestamp, severity, textPayload)" --freshness=1h
```

### Adım 4: Spesifik Log Filtreleri

Problemin türüne göre aşağıdaki filtreleri kullan:

#### Ödeme Problemleri:
```powershell
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND (jsonPayload.path:\"/payments\" OR jsonPayload.event:\"PAYMENT\" OR jsonPayload.event:\"iyzico\")" --project=gen-lang-client-0784096400 --limit=30 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error, jsonPayload.path)" --freshness=2h
```

#### Hikaye/Görsel Üretim Problemleri:
```powershell
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND (jsonPayload.event:\"ARQ_TASK\" OR jsonPayload.event:\"generate\")" --project=gen-lang-client-0784096400 --limit=30 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error, jsonPayload.trial_id, jsonPayload.order_id)" --freshness=2h
```

#### 5xx Hataları:
```powershell
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND jsonPayload.status_code>=500" --project=gen-lang-client-0784096400 --limit=20 --format="table(timestamp, jsonPayload.method, jsonPayload.path, jsonPayload.status_code, jsonPayload.error)" --freshness=2h
```

#### Auth/Login Problemleri:
```powershell
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND (jsonPayload.path:\"/auth\" OR jsonPayload.event:\"LOGIN\")" --project=gen-lang-client-0784096400 --limit=30 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error, jsonPayload.path)" --freshness=2h
```

#### Request ID ile Takip:
```powershell
# Belirli bir request_id ile tüm logları topla
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND jsonPayload.request_id=\"<REQUEST_ID>\"" --project=gen-lang-client-0784096400 --limit=50 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error)"
```

### Adım 5: Sentry Kontrol (Tarayıcı ile)

Eğer loglardan yeterli bilgi çıkmazsa:
1. Chrome'da `https://benimmasalim.sentry.io/issues/` aç
2. Son hataları (`Unresolved` filtresi) incele
3. Hata'nın stack trace'ini, breadcrumbs'ını ve context bilgisini oku

### Adım 6: Health Check

```powershell
# Backend health
Invoke-WebRequest -Uri "https://benimmasalim-backend-554846094227.europe-west1.run.app/health" -UseBasicParsing | Select-Object StatusCode, Content

# Frontend erişim
Invoke-WebRequest -Uri "https://www.benimmasalim.com.tr" -UseBasicParsing | Select-Object StatusCode
```

---

## 🛠️ Yaygın Problemler ve Çözümleri

### Problem: "Hikaye oluşturken hata oluştu"
1. Worker loglarını kontrol et → `ARQ_TASK_FAILED` event'lerini ara
2. Gemini API key rotasyonunu kontrol et
3. Redis bağlantısını kontrol et (Upstash idle timeout)

### Problem: "Ödeme başarısız"
1. Backend loglarında `/payments/callback` path'ini kontrol et
2. Iyzico callback hatalarını ara
3. Order state transition hatalarını kontrol et

### Problem: "Sayfa açılmıyor / 502"
1. Cloud Run servis durumunu kontrol et
2. Container crash loglarını ara
3. Memory limit aşımı kontrol et
4. Deploy sırasında hata olmuş olabilir → revision loglarını kontrol et

### Problem: "Görsel üretilmiyor / Preview gelmiyor"
1. Worker'ın çalıştığını doğrula
2. Redis kuyruk durumunu kontrol et
3. Fal.ai / Gemini API rate limit loglarını ara
4. Distributed semaphore doluluk durumunu kontrol et

---

## 📊 Teşhis Raporu Formatı

Teşhis tamamlandığında kullanıcıya şu formatta rapor sun:

```markdown
## 🔍 Teşhis Raporu

**Problem:** [Kısa açıklama]
**Etkilenen Servis:** backend / worker / frontend
**Kök Neden:** [Root cause analizi]
**Kanıt:** [Log satırları / Sentry hata referansı]

### Çözüm Planı
1. [Adım 1]
2. [Adım 2]
...

### Aciliyet
🔴 Kritik / 🟡 Önemli / 🟢 Düşük
```

---

## 🏗️ Altyapı Referansı

| Servis | Cloud Run Adı | Bölge |
|--------|--------------|-------|
| Backend API | `benimmasalim-backend` | europe-west1 |
| Arq Worker | `benimmasalim-worker` | europe-west1 |
| Frontend (Next.js) | `benimmasalim-frontend` | europe-west1 |

| Araç | URL / Erişim |
|------|-------------|
| Sentry | https://benimmasalim.sentry.io |
| Cloud Logging | Google Cloud Console → Logging |
| Cloud Monitoring | Google Cloud Console → Monitoring |
| GCP Project | `gen-lang-client-0784096400` |
