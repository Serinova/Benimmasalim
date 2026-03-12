---
description: Cloud Run servisini önceki revision'a geri alma (rollback) workflow'u
---
// turbo-all

# /rollback Workflow

Hatalı deploy sonrası önceki revision'a rollback yapma.

## Adımlar

1. Kullanıcıdan hangi servisi rollback edeceğini sor: `backend`, `worker`, veya `frontend`

// turbo
2. Mevcut revision'ları listele:
```powershell
gcloud run revisions list --service=benimmasalim-SERVIS --region=europe-west1 --project=gen-lang-client-0784096400 --limit=5 --format="table(name, status.conditions[0].status, metadata.creationTimestamp)"
```

3. Kullanıcıya hangi revision'a dönmek istediğini sor.

4. Traffic'i hedef revision'a yönlendir:
```powershell
gcloud run services update-traffic benimmasalim-SERVIS --to-revisions=HEDEF_REVISION=100 --region=europe-west1 --project=gen-lang-client-0784096400
```

// turbo
5. Health check ile doğrula:
```powershell
Invoke-WebRequest -Uri "https://benimmasalim-backend-554846094227.europe-west1.run.app/health" -UseBasicParsing | Select-Object StatusCode, Content
```

6. Sonucu kullanıcıya raporla.
