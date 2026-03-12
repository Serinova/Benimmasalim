---
description: Tüm servislerin sağlık durumunu tek komutla kontrol etme
---
// turbo-all

# /health-check Workflow

Tüm canlı servislerin sağlık durumunu kontrol et.

## Adımlar

1. Backend health check:
```powershell
Invoke-WebRequest -Uri "https://benimmasalim-backend-554846094227.europe-west1.run.app/health" -UseBasicParsing | Select-Object StatusCode, Content
```

2. Frontend erişim kontrolü:
```powershell
Invoke-WebRequest -Uri "https://www.benimmasalim.com.tr" -UseBasicParsing | Select-Object StatusCode
```

3. Backend Cloud Run servis durumu:
```powershell
gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"
```

4. Worker Cloud Run servis durumu:
```powershell
gcloud run services describe benimmasalim-worker --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"
```

5. Frontend Cloud Run servis durumu:
```powershell
gcloud run services describe benimmasalim-frontend --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"
```

6. Son hataları kontrol et (tüm servisler, son 30 dk):
```powershell
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --project=gen-lang-client-0784096400 --limit=10 --format="table(timestamp, resource.labels.service_name, severity, jsonPayload.event)" --freshness=30m
```

7. Sonuçları özetle:
   - ✅ Tüm servisler sağlıklı
   - ⚠️ Uyarı varsa detayları göster
   - ❌ Hata varsa detayları ve önerilen aksiyonu raporla
