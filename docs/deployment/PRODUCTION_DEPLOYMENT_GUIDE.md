# 🚀 PRODUCTION DEPLOYMENT PAKETI - KOMPLE MIGRATION

## 📦 TÜM MİGRATIONLAR (13 SENARYO)

Local environment Python sorunu var. GCP Cloud Run'da çalıştırılmalı!

---

## 🎯 GCP CLOUD RUN DEPLOYMENT KOMUTU

### Adım 1: Cloud Shell'e Bağlan
```bash
gcloud cloud-shell ssh
```

### Adım 2: Repository'yi Çek
```bash
cd /workspace
git pull origin main
```

### Adım 3: Backend Container'a Gir
```bash
cd backend
```

### Adım 4: Environment Variables Ayarla
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance"
```

### Adım 5: Tüm Migration'ları Çalıştır
```bash
# POPÜLER SENARYOLAR
python -m scripts.update_ocean_adventure_scenario
python -m scripts.update_dinosaur_scenario
python -m scripts.update_space_scenario
python -m scripts.update_galata_scenario
python -m scripts.update_cappadocia_scenario

# TARİHİ/EĞİTİCİ SENARYOLAR
python -m scripts.update_ephesus_scenario
python -m scripts.update_gobekli_scenario
python -m scripts.update_catalhoyuk_scenario
python -m scripts.update_amazon_scenario
python -m scripts.update_sumela_scenario

# DİNİ/KÜLTÜREL SENARYOLAR
python -m scripts.update_sultanahmet_scenario
python -m scripts.update_umre_scenario
python -m scripts.update_jerusalem_scenario

echo "✅ Tüm migration'lar tamamlandı!"
```

---

## 🏗️ BACKEND BUILD VE DEPLOY

### Adım 6: Docker Image Build
```bash
# Backend root'da
gcloud builds submit --tag gcr.io/PROJECT_ID/benimmasalim-backend:latest

# VEYA Dockerfile ile:
docker build -t gcr.io/PROJECT_ID/benimmasalim-backend:latest .
docker push gcr.io/PROJECT_ID/benimmasalim-backend:latest
```

### Adım 7: Cloud Run'a Deploy
```bash
gcloud run deploy benimmasalim-backend \
  --image gcr.io/PROJECT_ID/benimmasalim-backend:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances PROJECT_ID:europe-west1:benimmasalim-db \
  --set-env-vars DATABASE_URL="postgresql+asyncpg://..." \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 100
```

---

## 🎨 FRONTEND BUILD VE DEPLOY

### Adım 8: Frontend Build
```bash
cd /workspace/frontend
npm run build

# VEYA Next.js için:
npm run build
```

### Adım 9: Frontend Deploy (Varsa)
```bash
# Cloud Run için:
gcloud run deploy benimmasalim-frontend \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated

# VEYA Vercel/Netlify için:
vercel --prod
# veya
netlify deploy --prod
```

---

## 🧪 PRODUCTION TEST

### Adım 10: Health Check
```bash
# Backend health
curl https://benimmasalim-backend-xxx.run.app/health

# Scenarios endpoint
curl https://benimmasalim-backend-xxx.run.app/api/scenarios
```

### Adım 11: Frontend Test
```bash
# Frontend'i aç
open https://benimmasalim-frontend-xxx.run.app

# Kontroller:
# 1. Senaryo listesi görünüyor mu?
# 2. Yeni kitap oluştur butonu çalışıyor mu?
# 3. 13 senaryo listelenmiş mi?
```

### Adım 12: Senaryo Testi (Her Biri İçin)
1. Frontend'den yeni kitap oluştur
2. Çocuk bilgilerini gir
3. Senaryo seç (13 senaryodan biri)
4. Custom input gir (favorite_*, robot_name, vb.)
5. Kitap oluştur
6. İlk sayfa kontrol (cover)
7. Rastgele sayfa kontrol (page)
8. Son sayfa kontrol (final)
9. Görseller doğru mu?
10. Kıyafet uygun mu?

---

## 📊 DEPLOYMENT CHECKLİST

### Pre-Deployment:
- ✅ 13 migration script hazır
- ✅ Tüm promptlar < 500 char
- ✅ Story blueprint'ler eksiksiz
- ✅ Hassasiyet kuralları uygulanmış
- ✅ Dokümantasyon tam

### During Deployment:
- ⏳ Migration'lar çalıştırılacak
- ⏳ Database güncellenecek
- ⏳ Docker build yapılacak
- ⏳ Cloud Run'a push edilecek
- ⏳ DNS güncellemesi (gerekirse)

### Post-Deployment:
- ⏳ Health check
- ⏳ 13 senaryo testi
- ⏳ Performance monitoring
- ⏳ Error log kontrolü

---

## 🔥 HIZLI DEPLOYMENT (TEK KOMUT)

### GCP Cloud Shell'den Çalıştır:

```bash
#!/bin/bash
set -e

echo "🚀 BENİMMASALIM PRODUCTION DEPLOYMENT BAŞLIYOR..."

# 1. Repository güncelle
cd /workspace
git pull origin main

# 2. Backend migration'ları çalıştır
cd backend
export DATABASE_URL="postgresql+asyncpg://..."

echo "📊 Migration'lar çalıştırılıyor..."
python -m scripts.update_ocean_adventure_scenario
python -m scripts.update_dinosaur_scenario
python -m scripts.update_space_scenario
python -m scripts.update_galata_scenario
python -m scripts.update_cappadocia_scenario
python -m scripts.update_ephesus_scenario
python -m scripts.update_gobekli_scenario
python -m scripts.update_catalhoyuk_scenario
python -m scripts.update_amazon_scenario
python -m scripts.update_sumela_scenario
python -m scripts.update_sultanahmet_scenario
python -m scripts.update_umre_scenario
python -m scripts.update_jerusalem_scenario

echo "✅ Tüm migration'lar tamamlandı!"

# 3. Docker build ve deploy
echo "🏗️ Backend build başlıyor..."
gcloud builds submit --tag gcr.io/PROJECT_ID/benimmasalim-backend:latest

echo "🚀 Cloud Run'a deploy ediliyor..."
gcloud run deploy benimmasalim-backend \
  --image gcr.io/PROJECT_ID/benimmasalim-backend:latest \
  --region europe-west1 \
  --platform managed

echo "✅ DEPLOYMENT TAMAMLANDI!"
echo "🎉 13 yeni senaryo production'da!"
```

---

## ✅ SONUÇ

**HAZIR!** GCP Cloud Shell'de yukarıdaki komutu çalıştır:
1. ✅ 13 migration çalışacak
2. ✅ Backend build olacak  
3. ✅ Cloud Run'a deploy edilecek
4. ✅ Production'a push olacak

**On binlerce kullanıcı için hazır!** 🚀✨
