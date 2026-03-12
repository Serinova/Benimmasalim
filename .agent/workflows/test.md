---
description: Backend ve frontend için test, build ve type-check komutlarını sıralı çalıştırma
---
// turbo-all

# /test Workflow

Test ve doğrulama workflow'u. Kod değişikliği sonrası çalıştır.

## Adımlar

1. Frontend TypeScript kontrolü:
```powershell
cd frontend && npm run type-check
```

2. Frontend production build:
```powershell
cd frontend && npm run build
```

3. Frontend lint kontrolü:
```powershell
cd frontend && npm run lint
```

4. Backend pytest testleri:
```powershell
cd backend && python -m pytest tests/ -v --tb=short
```

5. Sonuçları özetle:
   - Hepsi geçtiyse ✅ "Tüm testler başarılı" mesajı ver
   - Biri başarısızsa ❌ Hata detaylarını raporla
