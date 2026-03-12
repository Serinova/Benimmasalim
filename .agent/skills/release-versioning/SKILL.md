---
name: Release & Versioning
description: >
  Versiyon takibi, release, changelog ve deployment geçmişi için ZORUNLU beceri.
  "versiyon", "release", "changelog", "ne deploy ettik" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 📦 Release & Versioning Skill

Deploy geçmişi, revision takibi ve rollback süreçlerini yönetir.

## ⚡ Tetikleyiciler

- "Hangi versiyon canlıda?", "ne zaman deploy ettik?"
- "Rollback yap", "önceki versiyona dön"
- "Changelog oluştur"

---

## 🔍 Aktif Revision Kontrolü

```powershell
# Backend — aktif revision
gcloud run services describe benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(status.latestReadyRevisionName)"

# Worker — aktif revision
gcloud run services describe benimmasalim-worker --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(status.latestReadyRevisionName)"

# Frontend — aktif revision
gcloud run services describe benimmasalim-frontend --region=europe-west1 --project=gen-lang-client-0784096400 --format="value(status.latestReadyRevisionName)"

# Tüm revision'lar (son 5)
gcloud run revisions list --service=benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --limit=5 --format="table(name, status.conditions[0].status, metadata.creationTimestamp)"
```

---

## 🔄 Rollback Prosedürü

```powershell
# 1. Mevcut revision'ları listele
gcloud run revisions list --service=benimmasalim-backend --region=europe-west1 --project=gen-lang-client-0784096400 --limit=5

# 2. Önceki revision'a traffic yönlendir
gcloud run services update-traffic benimmasalim-backend --to-revisions=REVISION_ADI=100 --region=europe-west1 --project=gen-lang-client-0784096400

# 3. Health check
Invoke-WebRequest -Uri "https://benimmasalim-backend-554846094227.europe-west1.run.app/health" -UseBasicParsing | Select-Object StatusCode, Content
```

---

## 📋 Deploy Öncesi Checklist

1. ✅ `npm run build` başarılı mı? (frontend)
2. ✅ `pytest` testleri geçiyor mu? (backend)
3. ✅ Alembic `heads` tek mi?
4. ✅ `.env` değişikliği var mı? → GCP Secret Manager'a da ekle
5. ✅ Breaking change var mı? → Migration önce, deploy sonra

---

## 📝 Changelog Oluşturma

```powershell
# Son deploy'dan bu yana commit'ler
git log --oneline --since="2 days ago"

# Belirli dosya değişiklikleri
git log --oneline --name-only --since="1 week ago" -- backend/
git log --oneline --name-only --since="1 week ago" -- frontend/
```

---

## 📊 Deploy Geçmişi

```powershell
# Son deploy tarihleri (Cloud Build)
gcloud builds list --project=gen-lang-client-0784096400 --limit=10 --format="table(id, status, createTime, source.repoSource.branchName)"
```

---

## 🏗️ Servis Bilgileri

| Servis | Cloud Run Adı | Docker Registry |
|--------|--------------|-----------------|
| Backend | `benimmasalim-backend` | `europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend` |
| Worker | `benimmasalim-worker` | Aynı image (farklı entrypoint) |
| Frontend | `benimmasalim-frontend` | `europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend` |
