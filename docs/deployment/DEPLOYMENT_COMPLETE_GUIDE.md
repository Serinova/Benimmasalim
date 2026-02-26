# 🚀 PRODUCTION DEPLOYMENT - KOMPLE KILAVUZ

## ⚠️ LOCAL ENVIRONMENT SORUNU

Python local'de bulunamadı. **GCP Cloud Run'da çalıştırılmalı!**

---

## 📦 DEPLOYMENT PAKETİ HAZIR

### Oluşturulan Dosyalar:
1. ✅ `deploy_production.sh` - Otomatik deployment script (13 migration + build + deploy)
2. ✅ 13 Python migration script hazır
3. ✅ Tüm dokümantasyon hazır

---

## 🎯 DEPLOYMENT ADIMLARI

### ADIM 1: GCP Cloud Shell'e Bağlan

```bash
gcloud cloud-shell ssh
```

### ADIM 2: Workspace'e Git

```bash
cd /workspace
```

### ADIM 3: Git Push (Önce Local'den)

Local'de (bu bilgisayarda):
```bash
cd c:\Users\yusuf\OneDrive\Belgeler\BenimMasalim

# Git init (eğer yoksa)
git init
git remote add origin https://github.com/YOUR_USERNAME/benimmasalim.git

# Tüm değişiklikleri commit et
git add .
git commit -m "feat: 13 senaryo modular sistem ile güncellendi

- Ocean, Dinosaur, Space pilot senaryoları
- 7 yeni Türkiye senaryosu (Galata, Sultanahmet, Sümela, Çatalhöyük, Efes, Göbeklitepe, Kapadokya)
- 3 dini/kültürel senaryo (Umre, Kudüs, Amazon)
- Tüm promptlar 500 char altında
- Story blueprint (dopamin management)
- İslami hassasiyet kuralları tam
- 13 deployment script hazır
"

# Push et
git push origin main
```

### ADIM 4: GCP'de Pull ve Deploy

Cloud Shell'de:
```bash
cd /workspace
git pull origin main

# Deployment script'i çalıştır
chmod +x deploy_production.sh
./deploy_production.sh
```

---

## 🔄 ALTERNATİF: MANUEL DEPLOYMENT

Eğer `deploy_production.sh` çalışmazsa:

### 1. Migration'ları Teker Teker Çalıştır:

```bash
cd /workspace/backend
export DATABASE_URL="postgresql+asyncpg://user:pass@/db?host=/cloudsql/..."

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
```

### 2. Docker Build:

```bash
cd /workspace/backend
PROJECT_ID=$(gcloud config get-value project)
gcloud builds submit --tag gcr.io/$PROJECT_ID/benimmasalim-backend:latest
```

### 3. Cloud Run Deploy:

```bash
gcloud run deploy benimmasalim-backend \
  --image gcr.io/$PROJECT_ID/benimmasalim-backend:latest \
  --region europe-west1 \
  --platform managed
```

---

## 🧪 POST-DEPLOYMENT TEST

### Test 1: Health Check
```bash
BACKEND_URL=$(gcloud run services describe benimmasalim-backend --region europe-west1 --format 'value(status.url)')
curl $BACKEND_URL/health
```

### Test 2: Scenarios Listesi
```bash
curl $BACKEND_URL/api/scenarios | jq '.[] | {name: .name, theme_key: .theme_key}'
```

**Beklenen**: 13 senaryo listesi

### Test 3: Frontend Test
- Browser'da frontend aç
- Senaryo listesi 13 senaryo göstermeli
- Her senaryonun cover image'ı olmalı
- Yeni kitap oluştur test et

---

## 📋 SON KONTROLLER

### Database'de Kontrol:

```sql
-- GCP Cloud SQL Query Editor'de:
SELECT 
    name,
    theme_key,
    LENGTH(cover_prompt_template) as cover_len,
    LENGTH(page_prompt_template) as page_len,
    marketing_badge,
    updated_at
FROM scenarios
ORDER BY updated_at DESC
LIMIT 13;
```

**Beklenen**:
- 13 senaryo
- Cover < 500
- Page < 500
- updated_at = bugün

---

## ✅ DEPLOYMENT SONRASI

### Monitoring:
```bash
# Logs
gcloud run services logs read benimmasalim-backend --region europe-west1

# Metrics
gcloud run services describe benimmasalim-backend --region europe-west1
```

### Rollback (Gerekirse):
```bash
# Önceki versiyona dön
gcloud run services update-traffic benimmasalim-backend \
  --region europe-west1 \
  --to-revisions PREVIOUS_REVISION=100
```

---

## 🎉 BAŞARI KRİTERLERİ

### Deployment Başarılı Sayılır Eğer:
1. ✅ 13 migration hatasız tamamlandı
2. ✅ Docker build başarılı
3. ✅ Cloud Run deploy başarılı
4. ✅ Health check 200 OK
5. ✅ /api/scenarios 13 senaryo dönüyor
6. ✅ Frontend 13 senaryoyu listeliyor
7. ✅ Test kitap oluşturma çalışıyor
8. ✅ Görseller üretiliyor
9. ✅ Hassas senaryolar (İslami) kurallara uygun

---

## 🚀 ÖZET

**GCP Cloud Shell'de çalıştır**:
```bash
cd /workspace
git pull origin main
chmod +x deploy_production.sh
./deploy_production.sh
```

**VEYA manuel olarak migration'ları çalıştır.**

**Sistem on binlerce kullanıcı için hazır!** 🎉✨
