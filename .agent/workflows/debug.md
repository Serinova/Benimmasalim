---
description: Canlı ortamda (Production) hata teşhisi ve çözümü. Sunucuda problem olunca logları kontrol edip sorunu bulmak için kullanılır.
---
// turbo-all
Bu workflow, canlı sistemde bir problem bildirildiğinde sistematik olarak hata teşhisi yapmak için kullanılır.

**Nasıl Kullanılır:**
Kullanıcı `/debug` yazdığında veya "hata var", "sunucu problemi", "logları kontrol et" dediğinde bu adımlar izlenir.

---

**ÖNEMLİ:** Başlamadan önce mutlaka `.agent/skills/production-debugger/SKILL.md` dosyasını oku!

---

1. **Kullanıcıdan bilgi al:**
   - Hangi hizmette sorun var? (ödeme, hikaye üretimi, giriş yapma, sayfa açılmıyor vb.)
   - Ne zaman başladı?
   - Hata mesajı veya ekran görüntüsü var mı?

2. **Tüm servislerin durumlarını kontrol et:**
// turbo
```powershell
gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"
```

// turbo
```powershell
gcloud run services describe benimmasalim-worker --region=europe-west1 --project=gen-lang-client-0784096400 --format="table(status.conditions[0].status, status.conditions[0].type, status.latestReadyRevisionName)"
```

3. **Son hata loglarını oku (backend):**
// turbo
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-backend AND severity>=ERROR" --project=gen-lang-client-0784096400 --limit=20 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error, jsonPayload.path)" --freshness=1h
```

4. **Son hata loglarını oku (worker):**
// turbo
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benimmasalim-worker AND severity>=ERROR" --project=gen-lang-client-0784096400 --limit=20 --format="table(timestamp, severity, jsonPayload.event, jsonPayload.error)" --freshness=1h
```

5. **Gerekirse Sentry'den detay al:**
   - Tarayıcıda https://benimmasalim.sentry.io/issues/ aç
   - Son unresolved issue'ları kontrol et
   - Stack trace'i oku

6. **Health check yap:**
// turbo
```powershell
Invoke-WebRequest -Uri "https://benimmasalim-backend-554846094227.europe-west1.run.app/health" -UseBasicParsing | Select-Object StatusCode, Content
```

7. **Teşhis raporunu hazırla:**
   - Problem, kök neden, kanıt (log satırları), çözüm planı ve aciliyet seviyesi içeren rapor sun
   - Çözüm kodunu yaz, test et ve deploy et
