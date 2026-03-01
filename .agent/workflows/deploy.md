---
description: Projeyi baştan sona (Frontend veya Backend) Google Cloud'a yayımlama (Deploy) yönergesi
---
Bu workflow, "Benim Masalım" projesinin Backend ve/veya Frontend kısımlarını canlıya (Production) almak için gerekli adımları içermektedir.

**Nasıl Kullanılır:**
Kullanıcı chat üzerine `/deploy` veya `/yayinla` yazdığında bu adımlar izlenir.

---

// turbo
1. **Kullanıcıdan iki soru sor:**
   - a) **Kapsam:** Sadece Backend mi, Sadece Frontend mi, yoksa Full Deploy (ikisi birden) mi?
   - b) **Yöntem:** Docker (GCP Cloud Build + Cloud Run) mi, yoksa Git (push → CI/CD) mi?

---

// turbo
2. **Docker Deploy Yöntemi (GCP Cloud Build + Cloud Run):**

   **Backend Docker Deploy:**
   ```powershell
   # 1. Docker image build (GCP Cloud Build)
   gcloud builds submit --tag europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest --timeout=20m . 
   # Cwd: c:\Users\yusuf\OneDrive\Belgeler\BenimMasalim\backend

   # 2. Cloud Run deploy
   gcloud run deploy benimmasalim-backend --image=europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest --region=europe-west1 --platform=managed --allow-unauthenticated --memory=2Gi --cpu=2 --min-instances=1 --max-instances=100 --timeout=300

   # 3. Worker deploy (aynı image)
   gcloud run deploy benimmasalim-worker --image=europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/backend:latest --region=europe-west1 --platform=managed
   ```

   **Frontend Docker Deploy:**
   ```powershell
   # 1. Docker image build (GCP Cloud Build)
   gcloud builds submit --tag europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend:latest --timeout=20m .
   # Cwd: c:\Users\yusuf\OneDrive\Belgeler\BenimMasalim\frontend

   # 2. Cloud Run deploy
   gcloud run deploy benimmasalim-frontend --image=europe-west1-docker.pkg.dev/gen-lang-client-0784096400/benimmasalim/frontend:latest --region=europe-west1 --platform=managed --allow-unauthenticated
   ```

   **Full Docker Deploy:**
   - Backend ve Frontend build'lerini **paralel** başlat (iki ayrı `gcloud builds submit`).
   - Her biri bitince ayrı ayrı `gcloud run deploy` yap.
   - Backend bitince worker'ı da deploy et.

---

// turbo
3. **Git Deploy Yöntemi (Push → CI/CD):**
   ```powershell
   # 1. Tüm değişiklikleri stage'le
   git add -A

   # 2. Commit (pre-commit hook sorun çıkarırsa --no-verify ekle)
   git commit --no-verify -m "feat: açıklayıcı commit mesajı"

   # 3. Push
   git push origin main
   ```
   - Push sonrası Vercel/CI otomatik deploy alır.
   - Bu yöntem sadece frontend'i etkiler. Backend için Docker yöntemi kullanılmalıdır.

---

// turbo
4. **Alembic Migration Kontrolü (Backend deploy öncesi):**
   - `git diff --name-only HEAD -- backend/alembic/versions/` ile yeni migration var mı kontrol et.
   - Yeni migration varsa, `cloud-sql-proxy` tünelinin açık olduğundan emin ol.
   - Migration çalıştır: `cd backend && alembic upgrade head`

---

// turbo
5. **Deploy Sonrası Doğrulama:**
   - Health check: `Invoke-WebRequest -Uri "https://benimmasalim-frontend-554846094227.europe-west1.run.app" -UseBasicParsing | Select-Object StatusCode`
   - Backend health: `Invoke-WebRequest -Uri "https://benimmasalim-backend-554846094227.europe-west1.run.app/api/v1/health" -UseBasicParsing | Select-Object StatusCode`
   - Hata varsa logları kontrol et: `gcloud run services logs read benimmasalim-frontend --region=europe-west1 --limit=20`
   - Kullanıcıya sonuçları tablo formatında bildir (servis adı, revision, durum, URL).
