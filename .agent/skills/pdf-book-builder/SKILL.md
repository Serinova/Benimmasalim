---
name: PDF & Book Builder
description: >
  PDF üretimi, kitap formatı, sayfa düzeni, boyama kitabı veya kapak sorunlarıyla ilgili
  ZORUNLU beceri. "PDF sorunu", "kitap formatı", "kapak", "boyama kitabı" dediğinde OKUNMALIDIR.
---
// turbo-all

# 📄 PDF & Book Builder Skill

Benim Masalım PDF pipeline'ını anlama, debug etme ve geliştirme rehberi.

## ⚡ Tetikleyiciler

- "PDF sorunu", "kapak bozuk", "sayfa düzeni hatalı"
- "boyama kitabı çalışmıyor", "QR kodu yok"
- "faded logo", "opacity sorunu", "font sorunu"

---

## 🗺️ PDF Pipeline Haritası

```
Sipariş Oluşturuldu
  │
  ├── Worker: generate_book (tasks/generate_book.py)
  │     │
  │     ├── Hikaye üretimi (GeminiService)
  │     ├── Görsel üretimi (Gemini Consistent Image)
  │     ├── Sayfa birleştirme (PageComposer)
  │     └── PDF oluşturma (PDFService)
  │
  └── Worker: generate_coloring_book (tasks/generate_coloring_book.py)
        │
        ├── Çizgi dönüştürme (image_processing.py → convert_to_line_art_ai)
        └── PDF oluşturma (PDFService, skip_text=True)
```

## 📁 Kritik Dosyalar

| Dosya | Satır | Rolü |
|-------|-------|------|
| `services/pdf_service.py` | ~1607 | Ana PDF üretici (ReportLab) |
| `services/admin_pdf_service.py` | - | Admin panel PDF raporu |
| `services/invoice_pdf_service.py` | - | Fatura PDF üretici |
| `services/page_composer.py` | - | Sayfa birleştirme (image + text overlay) |
| `tasks/generate_book.py` | - | Worker task: hikaye kitabı üretimi |
| `tasks/generate_coloring_book.py` | - | Worker task: boyama kitabı üretimi |
| `models/book_template.py` | - | PageTemplate, BackCoverConfig modelleri |

---

## 📐 Sayfa Yapısı

### Boyutlar (PageTemplate'den gelir)
- **Yatay A4**: 297mm × 210mm (standart kitap formatı)
- **Bleed (taşma)**: 3mm her yönde → Toplam: 303mm × 216mm
- **ReportLab birimleri**: mm × 2.834645 = points

### Sayfa Sırası (PDF)
1. **Kapak** (Cover) — `cover_image_url`
2. **Karşılama 1** (Dedication) — `dedication_image_base64` / `dedication_image_url`
3. **Karşılama 2** (Intro) — `intro_image_base64` / `intro_image_url`
4. **Hikaye sayfaları** — `story_pages[]` (text + image)
5. **QR bilgi sayfası** — `back_cover_config` (inner page)
6. **Görsel arka kapak** — `back_cover_image_url` (son sayfa)

---

## 🐛 "PDF Neden Bozuk?" Karar Ağacı

### Problem: Logo/Görsel soluk/şeffaf (faded)
1. **ReportLab Graphics State kontrolü** — `canvas.saveState()` / `canvas.restoreState()` doğru mu?
2. `setFillAlpha()` veya `setStrokeAlpha()` önceki elementlerden leak ediyor mu?
3. **Çözüm:** Logo çiziminden önce `c.saveState()` + `c.setFillAlpha(1.0)`, sonra `c.restoreState()`

### Problem: Metin görünmüyor / Türkçe karakter bozuk
1. Font kayıtlı mı? → `pdfmetrics.getRegisteredFontNames()` kontrol et
2. `DejaVuSans.ttf` dosyası var mı? → `backend/fonts/DejaVuSans.ttf`
3. **Fallback:** Helvetica (Türkçe karakterleri desteklemez!)

### Problem: Sayfa sayısı yanlış
1. `expected_total_pages` vs `total_pages` eşleşiyor mu?
2. `front_matter` sayfalar düzgün skip ediliyor mu?
3. `dedication_image` ve `intro_image` varsa sayfa sayısına ekleniyor mu?

### Problem: Görsel sayfayı doldurmuyoru
1. `preserveAspectRatio=False` olmalı (tam sayfa kaplama)
2. `drawImage(0, 0, width=page_width, height=page_height)` koordinatları doğru mu?
3. RGBA/P modlu görseller RGB'ye convert ediliyor mu?

### Problem: Boyama kitabı PDF üretilmiyor
1. Worker loglarında `generate_coloring_book` task'ını ara
2. `convert_to_line_art_ai` Gemini API hatası döndürüyor mu?
3. Retry logic çalışıyor mu? → `rate_limit_retry` decorator kontrolü

---

## 🎨 ReportLab Temel Kuralları

```python
# 1. Graphics State Management (KRİTİK!)
c.saveState()
c.setFillAlpha(1.0)       # Tam opak
c.drawImage(...)           # Görseli çiz
c.restoreState()           # Önceki state'e dön

# 2. Koordinat Sistemi
# (0,0) = SOL ALT KÖŞE (PDF standardı)
# y yukarı artar
c.drawImage(reader, x=0, y=0, width=w, height=h)

# 3. Ölçü Birimleri
from reportlab.lib.pagesizes import mm
page_width = 303 * mm    # mm → points dönüşümü

# 4. Font Kullanımı (Türkçe)
c.setFont("DejaVuSans", 14)  # Türkçe karakter desteği
# ASLA c.setFont("Helvetica", ...) kullanma (ş,ğ,İ,ı bozulur)

# 5. Memory Management
gc.collect()  # Her 3 sayfada bir
img.close()   # PIL Image'ları kapat
buffer.close()  # BytesIO buffer'ları kapat
```

---

## ⚠️ KESİNLİKLE YASAK

1. **Boyutları hard-code etme** — Daima `PageTemplate`'den al
2. **Helvetica fontunu Türkçe metin için kullanma** — `DejaVuSans` kullan
3. **Graphics state'i restore etmeden bırakma** — `saveState/restoreState` çifti
4. **PIL Image'ları kapatmadan bırakma** — Memory leak olur
5. **`preserveAspectRatio=True`** kullanma (sayfa tam kapanmalı)
