# V3 Stabilizasyon + PDF/Prompt Fix — Uygulama Özeti

**Tarih:** 2026-02-17  
**Hedef:** V3 tek kaynak, PDF hatasız, “görsele yazı / encoding / sayfa karışması” kapatıldı.

---

## A) Yapılan Değişiklikler (Dosya / Fonksiyon)

| # | Dosya | Fonksiyon / Bölüm | Değişiklik | Gerekçe |
|---|--------|-------------------|------------|---------|
| 1 | `backend/app/services/pdf_service.py` | `_register_fonts()` | Font adı `"TurkishFont"` → `"DejaVuSans"`; proje-relative `backend/fonts/DejaVuSans.ttf` ilk sırada | TR karakter (ş,ğ,İ,ı) için tek isim; setFont("DejaVuSans") artık eşleşiyor |
| 2 | `backend/app/services/pdf_service.py` | `render_back_cover` içi `set_font()` | `"TurkishFont"` → `"DejaVuSans"` | Aynı font adı |
| 3 | `backend/app/services/pdf_service.py` | `_add_text_page()` | Font 14 için `DejaVuSans` + stringWidth için `_font` (DejaVuSans/Helvetica) | TR metin sayfası |
| 4 | `backend/app/services/pdf_service.py` | Yeni `_add_text_from_config()` | Config dict ile vektör metin overlay | Trial PDF’te URL ile gelen sayfalara metin |
| 5 | `backend/app/services/pdf_service.py` | `generate_book_pdf_from_preview()` | URL sayfalarında `add_image_from_url` sonrası `_add_text_from_config()`; `expected_story_pages` / `expected_total_pages` ile sayfa sayısı doğrulama; hata durumunda `ValueError` | Trial PDF’te metin + sayfa sayısı garantisi |
| 6 | `backend/app/config.py` | `Settings` | `book_pipeline_version: Literal["2","3"] = "3"` eklendi; `use_blueprint_pipeline` yorumu “deprecated” | Tek env ile V3 zorunlu |
| 7 | `backend/app/services/ai/gemini_service.py` | `generate_story_structured()` | `book_pipeline_version` ile use_v3; `requested_version="v2"` ve version=3 ise `AIServiceError`; V2 dönüşünde version=3 ise `AIServiceError` | V3 dışında çalışmayı engelleme |
| 8 | `backend/app/models/order_page.py` | `OrderPage` | `v3_composed`, `negative_prompt`, `pipeline_version` alanları | Ödeme sonrası üretimde skip_compose kullanımı |
| 9 | `backend/alembic/versions/049_add_order_page_v3_columns.py` | — | Yeni migration: order_pages’e v3_composed, negative_prompt, pipeline_version | Şema güncellemesi |
| 10 | `backend/app/tasks/generate_book.py` | `generate_full_book()` | `skip_compose=getattr(page,"v3_composed",False)`, `precomposed_negative=getattr(page,"negative_prompt","")`; BUILD_REPORT log + return’e `build_report` | V3 sayfaları tekrar compose edilmiyor; job raporu |
| 11 | `backend/app/api/v1/trials.py` | Trial create + PDF | `pdf_data`’ya `expected_story_pages`, `expected_total_pages`; QA’da no_text_instructions / no_text_suffix / page_count fail ise `HTTPException 422` | Manifest/sayfa sayısı + QA bloklama |
| 12 | `backend/app/services/pdf_service.py` | Cover branch | `if cover_image_url and add_image_from_url(...)` birleştirildi | Lint (merge if) |

---

## B) Çalıştırma Talimatı

### Ortam
- **BOOK_PIPELINE_VERSION:** `3` (default). V2 kullanmak için `2` verilir; prod’da `3` kalmalı.
- **Font:** TR karakterler için `DejaVuSans` kullanılır. Sistem fontu veya `backend/fonts/DejaVuSans.ttf` (proje içi) kullanılabilir. Font yoksa Helvetica’ya düşer (TR bozulur).

### Local
```bash
cd backend
# Migration (yeni order_pages kolonları)
alembic upgrade head

# .env’de (opsiyonel, zaten default 3)
BOOK_PIPELINE_VERSION=3

# API + worker
uvicorn app.main:app --reload
# Ayrı terminal: arq app.workers.image_worker.WorkerSettings
```

### Prod
- `BOOK_PIPELINE_VERSION=3` set edilmeli (veya default 3 kullanılır).
- Migration çalıştır: `alembic upgrade head`.
- `backend/fonts/DejaVuSans.ttf` varsa PDF TR karakterleri güvenilir; yoksa sunucu fontuna bağlı.

---

## C) Test Adımları

1. **Font:** Hikaye metninde “hazırlanmıştır, Kapadokya, Göreme” geçen bir kitap üret → PDF’te ş, ğ, İ, ı, ö, ü, ç doğru görünmeli.
2. **V3 zorunlu:** `BOOK_PIPELINE_VERSION=3` ile trial oluştur → yanıt sayfalarında `pipeline_version: "v3"` olmalı.
3. **Trial PDF metin:** Trial PDF indir → kapak hariç sayfalarda hikaye metni vektör overlay olarak görünmeli.
4. **Sayfa sayısı:** Beklenen sayfa sayısı dışında PDF üretilirse (expected_story_pages / expected_total_pages) `ValueError` ile job fail etmeli.
5. **QA bloklama:** Prompt’ta metin talimatı veya sayfa sayısı uyumsuzluğu ile trial create → 422 ve “QA_CHECK_FAIL” detayı dönmeli.
6. **Build report:** Ödeme sonrası kitap job’u bittiğinde log’da `BUILD_REPORT` (used_version, page_count, total_duration_seconds) görünmeli.

---

## D) V2 Kaldırma / Devre Dışı Notu

- **Silinen dosya yok.** V2 pipeline kodu (`_pass1_write_story`, `_pass2_format_story`, `_compose_visual_prompts`, `compose_visual_prompt` vb.) duruyor.
- **Devre dışı:** `book_pipeline_version=3` (default) ile:
  - `requested_version="v2"` geçilirse `AIServiceError` (V2 kullanılamaz).
  - Caller `requested_version` geçmezse otomatik V3 çalışır.
  - V2 path’e düşülürse (bug) `AIServiceError`: "BOOK_PIPELINE_VERSION=3 but V2 pipeline ran".
- **Tek kaynak:** Hikaye + prompt üretimi fiilen V3; görsel üretimde `v3_composed=True` olan sayfalar `skip_compose=True` ile Fal’a gidiyor.

---

## E) Branch Notu

Projede git repo yoktu; değişiklikler doğrudan yapıldı. İsterseniz:

```bash
git checkout -b fix/v3-stabilization
git add -A
git commit -m "V3 stabilization: font fix, BOOK_PIPELINE_VERSION=3, OrderPage V3 fields, trial PDF text overlay, manifest validation, QA blocking, build report"
```

---

## F) Özet

- **TR encoding:** PDF’te font adı `DejaVuSans` ile tutarlı; register ve kullanım aynı.
- **V3 tek kaynak:** `book_pipeline_version=3` (default), V2’ye dönüş hata ile engellendi.
- **Trial PDF:** URL’den gelen sayfalara vektör metin overlay eklendi; sayfa sayısı doğrulanıyor.
- **QA:** no_text_instructions, no_text_suffix, page_count fail’de trial create 422 dönüyor.
- **OrderPage:** v3_composed / negative_prompt / pipeline_version ile ödeme sonrası üretimde V3 prompt’lar tekrar compose edilmiyor.
- **Build report:** Kitap job sonunda log ve return’de `build_report` (version, page_count, duration, error) var.
