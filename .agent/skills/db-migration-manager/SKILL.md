---
name: Database Migration Manager
description: >
  Veritabanı migration (Alembic) işlemlerinde ZORUNLU beceri. "tablo ekle", "kolon ekle",
  "migration", "alembic", "veritabanı değişikliği" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🗄️ Database Migration Manager Skill

Alembic migration oluşturma, kontrol etme ve production'a uygulama sürecini yönetir.

## ⚡ Tetikleyiciler

- Kullanıcı "migration yap", "tablo ekle", "kolon ekle" dediğinde
- Veritabanı model değişikliği yapıldığında
- `/migration` komutu verildiğinde

---

## 📋 Migration Oluşturma Süreci

### Adım 1: Mevcut Durumu Kontrol Et

```powershell
cd backend

# Mevcut head'leri kontrol et (TEK head olmalı!)
python -m alembic heads

# Mevcut versiyon
python -m alembic current

# Migration geçmişi (son 5)
python -m alembic history -r -5:head
```

> ⚠️ **BİRDEN FAZLA HEAD VARSA** migration oluşturmadan önce merge yap:
> ```powershell
> python -m alembic merge heads -m "merge_heads"
> ```

### Adım 2: Migration Dosyası Oluştur

**Otomatik (autogenerate):**
```powershell
python -m alembic revision --autogenerate -m "açıklayıcı_isim"
```

**Manuel (boş şablon):**
```powershell
python -m alembic revision -m "açıklayıcı_isim"
```

### Adım 3: Migration Dosyasını Düzenle

**Dosya konumu:** `backend/alembic/versions/`

**Zorunlu kurallar:**
1. `upgrade()` ve `downgrade()` MUTLAKA yazılmalı
2. `downgrade()` tüm değişiklikleri geri alabilmeli
3. Veri migration'larında var olan kontrolü yapılmalı

### Adım 4: Lokalde Test Et

```powershell
# Dry-run (SQL çıktısı kontrol)
python -m alembic upgrade head --sql

# Gerçek uygulama (lokal DB)
python -m alembic upgrade head

# Geri alma testi
python -m alembic downgrade -1
python -m alembic upgrade head
```

### Adım 5: Production'a Uygulama

```powershell
# Cloud SQL Proxy başlat (ayrı terminalde)
.\cloud-sql-proxy.exe gen-lang-client-0784096400:europe-west1:benimmasalim-db --port=5433

# Migration uygula (proxy üzerinden)
$env:DATABASE_URL="postgresql+asyncpg://USER:PASS@localhost:5433/benimmasalim"
python -m alembic upgrade head
```

---

## 📝 Migration Dosyası Şablonları

### Kolon Ekleme

```python
"""açıklayıcı_isim

Revision ID: xxx
Revises: yyy
Create Date: ...
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('tablo_adi', sa.Column('yeni_kolon', sa.String(255), nullable=True))

def downgrade() -> None:
    op.drop_column('tablo_adi', 'yeni_kolon')
```

### Veri Güncelleme (Data Migration)

```python
def upgrade() -> None:
    conn = op.get_bind()
    # Var olan kontrolü
    result = conn.execute(sa.text("SELECT id FROM tablo WHERE kolon = 'deger'"))
    if result.fetchone():
        conn.execute(sa.text("UPDATE tablo SET kolon = 'yeni_deger' WHERE kolon = 'deger'"))
    else:
        conn.execute(sa.text("INSERT INTO tablo (kolon) VALUES ('deger')"))

def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM tablo WHERE kolon = 'deger'"))
```

### Tablo Oluşturma

```python
def upgrade() -> None:
    op.create_table(
        'yeni_tablo',
        sa.Column('id', sa.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('yeni_tablo')
```

---

## 📁 İsimlendirme Kuralları

**Format:** `NNN_kisa_aciklama.py`
- `NNN` = Sıra numarası (son migration'dan +1)
- Son migration: `133_update_dinosaur_skill_v1.py` → Sonraki: `134_...`
- Açıklama İngilizce ve snake_case

**Senaryo migration'ları için:** `NNN_update_[theme_key]_scenario.py`

---

## ⚠️ Yaygın Hatalar ve Çözümleri

| Hata | Çözüm |
|------|--------|
| `Multiple heads detected` | `alembic merge heads -m "merge_NNN"` |
| `Target database is not up to date` | `alembic upgrade head` çalıştır |
| `Can't locate revision` | `down_revision` değerini kontrol et |
| `Column already exists` | `IF NOT EXISTS` kontrolü ekle |
| `asyncpg error` | Cloud SQL Proxy bağlantısını kontrol et |

---

## 🔗 İlgili Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `backend/alembic.ini` | Alembic konfigürasyonu |
| `backend/alembic/env.py` | Async engine konfigürasyonu |
| `backend/alembic/versions/` | 150+ migration dosyası |
| `backend/app/models/` | SQLAlchemy model tanımları |
| `backend/app/core/database.py` | DB bağlantı ve `Base` sınıfı |
