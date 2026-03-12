---
description: Alembic migration oluşturma ve uygulama workflow'u
---
// turbo-all

# /migration Workflow

Yeni Alembic migration oluştur, kontrol et ve uygula.

## Adımlar

// turbo
1. Mevcut head durumunu kontrol et:
```powershell
cd backend && python -m alembic heads
```

2. Birden fazla head varsa ÖNCE merge et:
```powershell
cd backend && python -m alembic merge heads -m "merge_heads"
```

3. Yeni migration oluştur (kullanıcıdan migration açıklamasını al):
```powershell
cd backend && python -m alembic revision --autogenerate -m "ACIKLAMA_BURAYA"
```

4. Oluşturulan migration dosyasını aç ve kontrol et:
   - `upgrade()` fonksiyonu doğru mu?
   - `downgrade()` fonksiyonu tüm değişiklikleri geri alıyor mu?
   - Gerekirse düzenle

// turbo
5. SQL çıktısını kontrol et (dry-run):
```powershell
cd backend && python -m alembic upgrade head --sql
```

6. Kullanıcıya migration'ı lokalde mi yoksa production'da mı uygulamak istediğini sor.

7a. **Lokal uygulama:**
```powershell
cd backend && python -m alembic upgrade head
```

7b. **Production uygulama:**
   - Cloud SQL Proxy başlatıldığından emin ol
   - DATABASE_URL'yi production'a ayarla
   - `python -m alembic upgrade head` çalıştır

// turbo
8. Sonucu doğrula:
```powershell
cd backend && python -m alembic current
```
