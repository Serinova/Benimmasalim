# 🚀 BOYAMA KİTABI AKTİVASYONU - 3 YÖNTEM

## ⚡ YÖNTEM 1: HTTP İsteği (EN KOLAY - 10 SANİYE)

**Backend zaten çalışıyorsa bu yöntemi kullanın!**

### Browser'dan:

Backend URL'inizi bulun ve tarayıcıda açın:

```
https://YOUR-BACKEND.run.app/admin/seed/coloring-book
```

**VEYA**

### Terminal'den:

```bash
# Backend URL'i alın
BACKEND_URL=$(gcloud run services describe benimmasalim-backend \
  --region europe-west1 \
  --format 'value(status.url)')

# POST isteği gönderin
curl -X POST "$BACKEND_URL/admin/seed/coloring-book"
```

### Beklenen Response:

**İlk çalıştırmada**:
```json
{
  "status": "created",
  "message": "Boyama kitabı başarıyla oluşturuldu!",
  "data": {
    "id": "...",
    "name": "Boyama Kitabı",
    "base_price": 200.0,
    "discounted_price": 150.0,
    "active": true
  }
}
```

**Zaten varsa**:
```json
{
  "status": "already_exists",
  "message": "Boyama kitabı zaten mevcut",
  "data": {
    "discounted_price": 150.0
  }
}
```

✅ **Bu kadar! Artık frontend'de görünecek!**

---

## 🔧 YÖNTEM 2: Google Cloud Shell (SCRIPT)

### Adım 1: Cloud Shell Aç

https://console.cloud.google.com/?cloudshell=true

### Adım 2: Project Ayarla

```bash
gcloud config set project gen-lang-client-0784096400
```

### Adım 3: Seed Script Çalıştır

```bash
# Python script oluştur
cat > /tmp/seed_coloring.py << 'PYTHON_SCRIPT'
import asyncio
import sys
from decimal import Decimal

# Backend path ekle
sys.path.insert(0, '/workspace/benimmasalim/backend')

async def seed():
    from sqlalchemy import select
    from app.core.database import async_session_factory
    from app.models.coloring_book import ColoringBookProduct
    
    async with async_session_factory() as db:
        # Kontrol et
        result = await db.execute(
            select(ColoringBookProduct).where(ColoringBookProduct.active == True)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Boyama kitabı zaten var!")
            print(f"   Fiyat: {existing.discounted_price} TL")
            return
        
        # Yeni oluştur
        config = ColoringBookProduct(
            name="Boyama Kitabı",
            slug="boyama-kitabi",
            description="Hikayenizdeki görsellerin boyama kitabı versiyonu.",
            base_price=Decimal("200.00"),
            discounted_price=Decimal("150.00"),
            line_art_method="canny",
            edge_threshold_low=80,
            edge_threshold_high=200,
            active=True,
        )
        
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
        print("✅ Boyama kitabı oluşturuldu!")
        print(f"   Fiyat: {config.discounted_price} TL")

asyncio.run(seed())
PYTHON_SCRIPT

# Çalıştır
cd /workspace/benimmasalim/backend
python /tmp/seed_coloring.py
```

---

## 🐳 YÖNTEM 3: Cloud Run Job

```bash
# Job oluştur
gcloud run jobs create coloring-book-seed \
  --image gcr.io/gen-lang-client-0784096400/benimmasalim-backend:latest \
  --region europe-west1 \
  --set-cloudsql-instances gen-lang-client-0784096400:europe-west1:benimmasalim-db \
  --set-env-vars "APP_ENV=production" \
  --command "python,-m,scripts.seed_coloring_book"

# Job'ı çalıştır
gcloud run jobs execute coloring-book-seed --region europe-west1
```

---

## ✅ DOĞRULAMA

### API Test:

```bash
curl https://YOUR-BACKEND.run.app/api/v1/coloring-books/active
```

**Beklenen**:
```json
{
  "name": "Boyama Kitabı",
  "discounted_price": 150.0,
  "active": true
}
```

### Frontend Test:

1. `/create` sayfasına git
2. Checkout adımına geç
3. **"🎨 Boyama Kitabını Ekle +150 TL"** checkbox'ını gör!

---

## 🎯 HANGİ YÖNTEMİ SEÇMELİ?

| Yöntem | Süre | Kolay | Ne Zaman |
|--------|------|-------|----------|
| **HTTP İsteği** | 10 sn | ⭐⭐⭐⭐⭐ | Backend çalışıyorsa |
| Cloud Shell | 2 dk | ⭐⭐⭐ | Backend erişimi varsa |
| Cloud Run Job | 5 dk | ⭐⭐ | Job oluşturma yetkisi varsa |

**ÖNERİ**: **Yöntem 1 (HTTP)** - En hızlı ve kolay!

---

## 📝 DEPLOYMENT SONRASI

### Code Deploy (Gelecek için)

Yeni admin endpoint'i deploy etmek için:

```bash
cd backend
gcloud builds submit --tag gcr.io/gen-lang-client-0784096400/benimmasalim-backend:latest
gcloud run deploy benimmasalim-backend --image gcr.io/.../benimmasalim-backend:latest --region europe-west1
```

**VEYA** Git push ile otomatik deploy.

---

## 🎉 ÖZET

**3 Seçenek**:

1. **HTTP POST**: `curl -X POST .../admin/seed/coloring-book` (10 sn)
2. **Cloud Shell**: Python script çalıştır (2 dk)
3. **Cloud Run Job**: Job oluştur ve çalıştır (5 dk)

**En Kolay**: HTTP isteği! ⚡

```bash
curl -X POST https://YOUR-BACKEND.run.app/admin/seed/coloring-book
```

**Sonuç**: Boyama kitabı checkout'ta görünür! 🎨
