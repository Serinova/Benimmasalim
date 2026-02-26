# 🚀 SUNUCUDA BOYAMA KİTABI AKTİVASYONU - HIZLI KILAVUZ

## ⚡ HIZLI BAŞLANGIÇ (2 DAKİKA)

### 1. Google Cloud Shell Aç

**Link**: https://console.cloud.google.com/?cloudshell=true

Veya:
1. https://console.cloud.google.com/ 
2. Sağ üstten "Activate Cloud Shell" butonuna tıkla

---

### 2. Projeyi Hazırla

```bash
# Eğer proje yoksa klonla
git clone YOUR_REPO_URL benimmasalim
cd benimmasalim

# VEYA mevcut proje varsa
cd benimmasalim
git pull  # Son güncellemeleri al
```

---

### 3. Deployment Script'ini Çalıştır

```bash
# Script'i çalıştırılabilir yap
chmod +x deploy_coloring_activation.sh

# Çalıştır
./deploy_coloring_activation.sh
```

**Tahmini Süre**: 2-3 dakika

---

## 📋 SCRIPT NE YAPIYOR?

```
1. ✅ GCP Project ayarla (gen-lang-client-0784096400)
2. ✅ Database migration çalıştır (alembic upgrade head)
3. ✅ Boyama kitabı seed et (python -m scripts.seed_coloring_book)
4. ✅ Verification (database'de veri var mı kontrol)
5. ✅ Backend restart (Cloud Run'da yeni revision)
6. ✅ API test (curl ile endpoint kontrol)
7. ✅ Rapor göster
```

---

## ✅ BEKLENEN ÇIKTI

```bash
╔════════════════════════════════════════════════╗
║  SUNUCUDA BOYAMA KİTABI AKTİVASYONU          ║
╚════════════════════════════════════════════════╝

📌 Project: gen-lang-client-0784096400

📊 Database Migration...
✅ Migration tamamlandı!

🎨 Boyama Kitabı Seed...
✓ Coloring book product created successfully!
  Name: Boyama Kitabı
  Base Price: 200.00 TL
  Discounted Price: 150.00 TL
✅ Seed tamamlandı!

🔍 Verification...
✅ Coloring book product FOUND!
   Name: Boyama Kitabı
   Discounted: 150.0 TL
   Thresholds: 80/200
   Active: True

🔄 Backend Restart...
✅ Backend restarting...

🧪 API Test...
Backend URL: https://benimmasalim-backend-xxx.run.app
Testing: GET /api/v1/coloring-books/active
{
  "name": "Boyama Kitabı",
  "discounted_price": 150.0,
  "active": true
}

╔════════════════════════════════════════════════╗
║        ✅ DEPLOYMENT TAMAMLANDI! ✅           ║
╚════════════════════════════════════════════════╝
```

---

## 🧪 MANUEL TEST

### Backend API Test

```bash
# Backend URL al
BACKEND_URL=$(gcloud run services describe benimmasalim-backend \
  --region europe-west1 \
  --format 'value(status.url)')

# API test
curl $BACKEND_URL/api/v1/coloring-books/active | jq '.'
```

**Beklenen Response**:
```json
{
  "id": "...",
  "name": "Boyama Kitabı",
  "slug": "boyama-kitabi",
  "description": "...",
  "base_price": 200.0,
  "discounted_price": 150.0,
  "active": true
}
```

### Frontend Test

1. Frontend URL'i aç: `https://benimmasalim-frontend-xxx.run.app`
2. `/create` sayfasına git
3. Hikaye oluştur
4. Checkout adımına geç
5. **"🎨 Boyama Kitabını Ekle +150 TL"** checkbox'ını gör

---

## 🔧 SORUN GİDERME

### Problem 1: Migration Hatası

```bash
# DATABASE_URL set edilmemiş olabilir
export DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@/benimmasalim?host=/cloudsql/INSTANCE"

# Tekrar dene
cd backend
alembic upgrade head
```

### Problem 2: Seed Zaten Var

```bash
# Normal! "Already exists" mesajı göreceksiniz
✓ Coloring book product already exists
```

### Problem 3: API 404

```bash
# Backend restart gerekebilir
gcloud run services update benimmasalim-backend \
  --region europe-west1 \
  --update-env-vars "RESTART=$(date +%s)"

# 1-2 dakika bekle ve tekrar test et
```

### Problem 4: Checkbox Görünmüyor

**Browser Console'da kontrol**:
```javascript
// F12 > Console
console.log("Coloring book price:", coloringBookPrice);
// Beklenen: 150

// Eğer 0 ise:
// 1. Backend'den fetch hatası olabilir
// 2. Network tab'da request kontrol et
// 3. API response 200 OK mı?
```

---

## 📊 DATABASE KONTROL

```bash
# Cloud SQL'e bağlan
gcloud sql connect benimmasalim-db --user=postgres

# Database'de kontrol
SELECT 
    name,
    base_price,
    discounted_price,
    edge_threshold_low,
    edge_threshold_high,
    active
FROM coloring_book_products;
```

**Beklenen**:
```
name           | base_price | discounted_price | edge_threshold_low | edge_threshold_high | active
Boyama Kitabı | 200.00     | 150.00          | 80                 | 200                 | t
```

---

## 🎯 BAŞARI KRİTERLERİ

### ✅ Backend
- [ ] Database'de `coloring_book_products` verisi var
- [ ] API endpoint `/coloring-books/active` 200 döndürüyor
- [ ] Response'da `discounted_price: 150.0` var

### ✅ Frontend
- [ ] `/create` sayfası açılıyor
- [ ] Console'da coloring book fetch hatası yok
- [ ] Checkout adımında checkbox görünüyor
- [ ] Checkbox işaretlenince toplam +150 TL artıyor

### ✅ End-to-End
- [ ] Sipariş verilebiliyor
- [ ] `has_coloring_book: true` backend'e gidiyor
- [ ] İyzico ödeme tutarı doğru (base + coloring)
- [ ] Order create ediliyor

---

## 📝 MANUEL SEED (Alternatif)

Eğer script çalışmazsa:

```bash
cd benimmasalim/backend

# Direkt seed çalıştır
python -m scripts.seed_coloring_book
```

**Çıktı**:
```
═══════════════════════════════════════════
Seeding Coloring Book Product Configuration
═══════════════════════════════════════════
✓ Coloring book product created successfully!
  ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Name: Boyama Kitabı
  Base Price: 200.00 TL
  Discounted Price: 150.00 TL
  Line-art Method: canny
  Edge Thresholds: 80/200
═══════════════════════════════════════════
Done!
```

---

## 🚀 DEPLOYMENT SONRASI

### Hemen Test Et

```bash
# 1. API test
curl https://benimmasalim-backend-xxx.run.app/api/v1/coloring-books/active

# 2. Frontend aç
open https://benimmasalim-frontend-xxx.run.app/create

# 3. Hikaye oluştur ve checkout'a git
```

### Monitoring

```bash
# Backend logs
gcloud run services logs read benimmasalim-backend \
  --region europe-west1 \
  --limit 50

# Coloring book API calls kontrol
gcloud run services logs read benimmasalim-backend \
  --region europe-west1 \
  --filter 'resource.labels.service_name="benimmasalim-backend" AND textPayload=~"coloring"'
```

---

## 📞 DESTEK

### Logs Kontrol

```bash
# Backend logs
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=benimmasalim-backend" \
  --limit 20 \
  --format json

# Hata varsa
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=benimmasalim-backend \
  AND severity>=ERROR" \
  --limit 20
```

### Database Debug

```bash
# SQL proxy başlat
cloud_sql_proxy -instances=gen-lang-client-0784096400:europe-west1:benimmasalim-db=tcp:5432

# Başka terminal'de
psql -h localhost -U postgres benimmasalim

# Query
SELECT * FROM coloring_book_products;
```

---

## 🎉 ÖZET

**1 Komut ile Aktif**:
```bash
./deploy_coloring_activation.sh
```

**Süre**: 2-3 dakika

**Sonuç**:
- ✅ Database seed edildi
- ✅ Backend restart oldu
- ✅ API çalışıyor
- ✅ Frontend'de görünür

**Test**:
```bash
curl https://YOUR-BACKEND.run.app/api/v1/coloring-books/active
# Expected: {"discounted_price": 150.0}
```

🎨 **BOYAMA KİTABI ARTIK SUNUCUDA AKTİF!**
