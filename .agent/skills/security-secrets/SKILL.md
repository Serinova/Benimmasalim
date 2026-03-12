---
name: Security & Secrets Manager
description: >
  API key, secret, env değişkeni ve credential yönetimi için ZORUNLU beceri.
  "API key", "secret", "env dosyası", "credential", "güvenlik" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🔐 Security & Secrets Manager Skill

Hassas bilgilerin güvenli yönetimi, saklanması ve rotasyonu için rehber.

## ⚡ Tetikleyiciler

- "API key ekle", "secret güncelle", "env değişkeni"
- ".env dosyası", "credential kayboldu"
- "Güvenlik kontrolü"

---

## 🗺️ Secret Haritası

### Lokal Geliştirme (`.env` dosyaları)

| Dosya | Nerede | Ne İçerir |
|-------|--------|-----------|
| `.env` | Proje root | Tüm ortam değişkenleri (master) |
| `.env.local` | Proje root | Lokal override'lar |
| `.env.example` | Proje root | Şablon (gerçek key YOK) |
| `frontend/.env.local` | Frontend root | `NEXT_PUBLIC_*` değişkenler |

### Production (GCP)

| Kaynak | Erişim |
|--------|--------|
| Cloud Run Environment Variables | GCP Console → Cloud Run → Edit & Deploy |
| Cloud Run YAML | `backend_service.yaml` (referans) |

---

## 🔑 Mevcut Secret'lar

| Secret | Lokal | Production | Kullanıldığı Yer |
|--------|-------|------------|-------------------|
| `SECRET_KEY` | `.env` | Cloud Run env | App-level signing (min 64 char prod) |
| `WEBHOOK_SECRET` | `.env` | Cloud Run env | Webhook imza doğrulama |
| `GEMINI_API_KEY` | `.env` | Cloud Run env | Gemini AI servisi |
| `GEMINI_API_KEYS_EXTRA` | `.env` | Cloud Run env | Rate limit key rotation |
| `DATABASE_URL` | `.env` | Cloud Run env | PostgreSQL bağlantısı |
| `REDIS_URL` | `.env` | Cloud Run env | Arq worker kuyruk |
| `IYZICO_API_KEY` | `.env` | Cloud Run env | Ödeme servisi |
| `IYZICO_SECRET_KEY` | `.env` | Cloud Run env | Ödeme servisi |
| `JWT_SECRET_KEY` | `.env` | Cloud Run env | Auth token imzalama (min 64 char prod) |
| `GCS_CREDENTIALS_JSON` | `.env` | Cloud Run env | GCS service account JSON |
| `SENTRY_DSN` | `.env` | Cloud Run env | Hata izleme |
| `FAL_API_KEY` | `.env` | Cloud Run env | Fal.ai görsel üretimi |
| `FAL_API_KEYS_EXTRA` | `.env` | Cloud Run env | Fal.ai key rotation |
| `ELEVENLABS_API_KEY` | `.env` | Cloud Run env | Sesli kitap |
| `REPLICATE_API_KEY` | `.env` | Cloud Run env | Real-ESRGAN upscaling |
| `SMTP_USER` | `.env` | Cloud Run env | Email gönderimi |
| `SMTP_PASSWORD` | `.env` | Cloud Run env | Email gönderimi |
| `NEXTAUTH_SECRET` | Frontend `.env.local` | Cloud Run env | Next-Auth |
| `GOOGLE_CLIENT_ID` | `.env` | Cloud Run env | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | `.env` | Cloud Run env | Google OAuth |

---

## ➕ Yeni Secret Ekleme Prosedürü

### 1. Lokale Ekle
```powershell
# .env dosyasına ekle
echo "NEW_SECRET=value" >> .env

# .env.example'a placeholder ekle (gerçek değer OLMADAN)
echo "NEW_SECRET=your-secret-here" >> .env.example
```

### 2. Koda Ekle
```python
# backend/app/config.py'ye ekle
class Settings(BaseSettings):
    new_secret: str = ""
    
    class Config:
        env_file = ".env"
```

### 3. Production'a Ekle
```powershell
# Cloud Run servisine env var olarak ekle
gcloud run services update benimmasalim-backend --set-env-vars="NEW_SECRET=value" --region=europe-west1 --project=gen-lang-client-0784096400

# Worker'a da aynısını ekle (aynı codebase)
gcloud run services update benimmasalim-worker --set-env-vars="NEW_SECRET=value" --region=europe-west1 --project=gen-lang-client-0784096400
```

---

## 🔄 API Key Rotasyonu

### Gemini API Key Rotation

```powershell
# 1. Yeni key'i extra'lara ekle
# .env → GEMINI_API_KEYS_EXTRA=eski_key1,eski_key2,YENI_KEY

# 2. Production'da güncelle
gcloud run services update benimmasalim-worker --set-env-vars="GEMINI_API_KEYS_EXTRA=key1,key2,key3" --region=europe-west1 --project=gen-lang-client-0784096400

# 3. Eski primary key'i dönüşüme al
# .env → GEMINI_API_KEY=yeni_primary_key
```

---

## 🛡️ Güvenlik Kontrol Listesi

1. ✅ `.gitignore` kontrol: `.env`, `.env.local`, `*.json` (credentials) listede mi?
2. ✅ `git log --all --full-history -- .env` → Hiç commit edilmiş mi?
3. ✅ Hardcoded secret grep: `grep -rn "sk-\|AIza\|iyzico" backend/app/ --include="*.py"`
4. ✅ `.env.example` güncel mi? (tüm key'ler placeholder ile)
5. ✅ JWT_SECRET_KEY en az 32 karakter mi?

---

## ⚠️ KESİNLİKLE YASAK

1. **Secret'ları kod içine hard-code ETME** → `settings.xxx` kullan
2. **`.env` dosyasını commit ETME** → `.gitignore`'da olmalı
3. **API key'leri log'a YAZMA** → Sadece suffix (son 4 karakter)
4. **GCP service account JSON'ı repo'ya EKLEME**
5. **Kullanıcıya secret değerini gösterirken TAM GÖSTERME** → mask'li göster
