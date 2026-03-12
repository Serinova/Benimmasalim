---
name: Performance Monitor
description: >
  Cloud Run performans sorunları, cold start, memory, timeout analizi için ZORUNLU beceri.
  "yavaş", "performans", "memory", "timeout", "cold start" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 📊 Performance Monitor Skill

Cloud Run servislerinin performans analizi ve optimizasyonu rehberi.

## ⚡ Tetikleyiciler

- "Site yavaş", "cold start", "timeout"
- "Memory hatası", "OOM", "CPU yüksek"
- "İstek süresi uzun", "gecikme var"

---

## 🔍 Hızlı Durum Kontrolü

```powershell
# Backend — request latency (son 1 saat)
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND jsonPayload.duration_ms>0" --project=gen-lang-client-0784096400 --limit=20 --freshness=1h --format="table(timestamp, jsonPayload.method, jsonPayload.path, jsonPayload.duration_ms, jsonPayload.status_code)"

# Worker — task süreleri
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND jsonPayload.event:\"TASK_COMPLETED\"" --project=gen-lang-client-0784096400 --limit=10 --freshness=2h --format="table(timestamp, jsonPayload.task_name, jsonPayload.duration_seconds)"

# Instance sayısı (aktif)
gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(spec.template.spec.containerConcurrency, spec.template.metadata.annotations['autoscaling.knative.dev/maxScale'], spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"
```

---

## 🧊 Cold Start Analizi

```powershell
# Cold start logları
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND textPayload:\"Started\"" --project=gen-lang-client-0784096400 --limit=10 --freshness=6h --format="table(timestamp, textPayload)"

# Container startup süreleri
gcloud run revisions describe $(gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(status.latestReadyRevisionName)") --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(status.conditions)"
```

**Cold start azaltma yöntemleri:**
- `minScale=1` ayarla (en az 1 instance her zaman çalışsın)
- Docker image boyutunu küçült
- Startup'ta lazy loading kullan

---

## 💾 Memory Analizi

```powershell
# Memory limit aşımları (OOMKilled)
gcloud logging read "resource.labels.service_name=benimmasalim-worker AND textPayload:\"OOM\\" OR textPayload:\"memory\"" --project=gen-lang-client-0784096400 --limit=10 --freshness=24h

# Mevcut memory limiti
gcloud run services describe benimmasalim-worker --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(spec.template.spec.containers[0].resources.limits.memory)"
```

**Memory sorunlarında:**
- PDF üretimi yoğun memory kullanır → `gc.collect()` her 3 sayfada
- PIL Image'ları kapatılmalı → `img.close()` + `buffer.close()`
- Worker memory limitini artır: `--memory=2Gi`

---

## ⏱️ Timeout Analizi

```powershell
# Timeout logları
gcloud logging read "resource.labels.service_name=benimmasalim-backend AND (jsonPayload.error:\"timeout\" OR jsonPayload.error:\"TimeoutError\")" --project=gen-lang-client-0784096400 --limit=10 --freshness=2h

# Mevcut timeout ayarı
gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(spec.template.spec.timeoutSeconds)"
```

**Timeout limitleri:**
| Servis | Default | Önerilen |
|--------|---------|----------|
| Backend API | 300s | 300s |
| Worker | 900s (15dk) | 900s-1800s |
| Gemini API çağrısı | 180s | 180s |

---

## 📈 "Neden Yavaş?" Karar Ağacı

```
Site yavaş
  │
  ├── Frontend yavaş mı? → Chrome DevTools Network tab
  │     ├── TTFB yüksek → Backend cold start?
  │     ├── Bundle büyük → next build analizi
  │     └── API çağrıları yavaş → Backend latency kontrol
  │
  ├── Backend yavaş mı? → gcloud logging (duration_ms)
  │     ├── DB query yavaş → EXPLAIN ANALYZE
  │     ├── Gemini API yavaş → rate_limit logları
  │     └── Cold start → minScale=1 ayarla
  │
  └── Worker yavaş mı? → task duration logları
        ├── Gemini rate limit → Key rotation + backoff
        ├── Memory yetersiz → OOM logları kontrol
        └── Image processing → PIL pipeline profiling
```

---

## 🛠️ Optimizasyon Komutları

```powershell
# Min instance'ı 1'e çek (cold start engellemek)
gcloud run services update benimmasalim-backend --min-instances=1 --region=europe-west1 --project=gen-lang-client-0784096400

# CPU boost'u aç (cold start hızlandırma)
gcloud run services update benimmasalim-backend --cpu-boost --region=europe-west1 --project=gen-lang-client-0784096400

# Worker memory'sini artır
gcloud run services update benimmasalim-worker --memory=2Gi --region=europe-west1 --project=gen-lang-client-0784096400
```
