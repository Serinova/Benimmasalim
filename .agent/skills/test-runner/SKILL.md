---
name: Test Runner
description: >
  Kod değişikliklerinden sonra otomatik test ve doğrulama yapmak için ZORUNLU beceri.
  "test et", "build kontrol", "bu doğru mu", "pytest", "npm run build" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🧪 Test Runner Skill

Benim Masalım projesinde kod değişikliği sonrası sistematik test ve doğrulama adımlarını tanımlar.

## ⚡ Tetikleyiciler

- Kullanıcı "test et", "build kontrol", "doğrula" dediğinde
- Herhangi bir dosya değişikliği sonrası (otomatik kontrol)
- `/test` komutu verildiğinde

---

## 🔍 Hangi Dosya Değişti → Hangi Test Çalışır?

| Değişen Dosya/Klasör | Çalıştırılacak Test |
|----------------------|---------------------|
| `backend/app/**/*.py` | `pytest` (backend root'tan) |
| `backend/app/services/pdf_service.py` | `pytest` + `npm run build` |
| `backend/app/services/ai/*.py` | `pytest` + Gemini log kontrolü |
| `backend/alembic/versions/*.py` | `alembic heads` kontrolü + `alembic upgrade head --sql` |
| `frontend/src/**/*.tsx` | `npm run build` + `npm run type-check` |
| `frontend/src/**/*.ts` | `npm run build` + `npm run type-check` |
| `frontend/src/**/*.css` | `npm run build` |
| `frontend/package.json` | `npm install` + `npm run build` |
| `Dockerfile` | `docker build` dry-run |
| `.env*` | Health check endpoint kontrolü |

---

## 📋 Test Komutları Referansı

### Backend (Python / FastAPI)

```powershell
# Tüm testler
cd backend
python -m pytest tests/ -v --tb=short

# Belirli bir test dosyası
python -m pytest tests/test_orders.py -v

# Belirli bir test fonksiyonu
python -m pytest tests/test_orders.py::test_create_order -v

# Async testler (pytest-asyncio)
python -m pytest tests/ -v --asyncio-mode=auto

# Coverage raporu
python -m pytest tests/ --cov=app --cov-report=term-missing
```

**Önemli Fixture'lar (conftest.py):**
- `test_engine` — Test DB: `postgresql+asyncpg://postgres:postgres@localhost:5432/test_benimmasalim`
- `db_session` — Her test sonrası rollback yapan async session
- `client` — `httpx.AsyncClient` ile FastAPI test istemcisi
- `sample_user_data` — `{email, password, full_name}`
- `sample_order_data` — `{child_name, child_age, child_gender}`

### Frontend (Next.js / TypeScript)

```powershell
# TypeScript type kontrolü (en önemli!)
cd frontend
npm run type-check

# Production build (lint + compile + optimize)
npm run build

# ESLint kontrolü
npm run lint

# Jest birim testleri
npm run test

# Playwright E2E testleri
npm run test:e2e

# Prettier format kontrolü
npm run format:check
```

### Docker Build Doğrulama

```powershell
# Backend Docker build (dry-run)
cd backend
docker build --no-cache -t test-backend .

# Frontend Docker build (dry-run)
cd frontend
docker build --no-cache -t test-frontend .
```

---

## 🎯 Değişiklik Sonrası Kontrol Checklist'i

### Küçük Değişiklik (tek dosya, basit fix)
1. ✅ `npm run type-check` veya `pytest` (ilgili tarafa göre)
2. ✅ `npm run build` veya `pytest` başarılı mı?

### Orta Değişiklik (birden fazla dosya, yeni özellik)
1. ✅ Backend: `pytest tests/ -v`
2. ✅ Frontend: `npm run build && npm run type-check`
3. ✅ Değişen dosyaların import'ları doğru mu?

### Büyük Değişiklik (mimari, migration, yeni servis)
1. ✅ Backend: `pytest tests/ -v --tb=long`
2. ✅ Frontend: `npm run build && npm run type-check && npm run lint`
3. ✅ Alembic: `alembic heads` (tek head olmalı!)
4. ✅ Docker: `docker build --no-cache .` (her iki servis)
5. ✅ Health check: `Invoke-WebRequest -Uri "http://localhost:8000/health"`

---

## ⚠️ Sık Karşılaşılan Test Hataları

| Hata | Çözüm |
|------|--------|
| `ModuleNotFoundError` | `cd backend && pip install -e .` veya `npm install` |
| `asyncpg.InvalidCatalogNameError` | Test DB oluştur: `createdb test_benimmasalim` |
| `Type error: ... is not assignable` | `npm run type-check` çıktısında satır numarasına bak |
| `Build optimization failed` | `rm -rf frontend/.next && npm run build` |
| `Multiple heads` (Alembic) | `alembic merge heads -m "merge"` |
| `CSRF token mismatch` | Test client'ta `app.dependency_overrides` kontrol et |
