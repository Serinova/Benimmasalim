# Prompt Sistemi Yeniden Yazım Analizi

## 1. Mevcut Mimari Özeti

### 1.1 Prompt Engine (22 dosya — `backend/app/prompt_engine/`)

| Dosya | Sorumluluk |
|---|---|
| `constants.py` | Stil tanımları, negatif prompt'lar, template'lar, PuLID config |
| `story_prompt_composer.py` | PASS-1: Türkçe hikaye yazım prompt'u |
| `visual_prompt_composer.py` | V2 legacy: görsel prompt birleştirme |
| `visual_prompt_builder.py` | V3: gelişmiş görsel prompt oluşturma |
| `flux_prompt_builder.py` | Legacy Flux builder |
| `fal_request_builder.py` | FAL API payload oluşturma |
| `negative_prompt_builder.py` | Negatif prompt oluşturma |
| `prompt_sanitizer.py` | Prompt temizleme, TR→EN çeviri |
| `validators.py` | Prompt doğrulama |
| `character_bible.py` | Karakter tanımı yönetimi |
| `scene_director.py` | Kamera/çekim planı |
| `iconic_anchors.py` | Lokasyon çapa noktaları |
| `style_adapter.py` | Stil uyarlama |
| `blueprint_prompt.py` | V3 blueprint prompt |
| `page_prompt.py` | V3 sayfa prompt |
| `scenario_bible.py` | Senaryo bilgi bankası |
| `story_validators.py` | Hikaye doğrulama |
| `qa_checks.py` | Kalite kontrol |
| `visual_prompt_validator.py` | Görsel prompt doğrulama |
| `compliance.py` | Uyumluluk kontrolleri |
| `__init__.py` | 130+ export |
| `README.md` | Dokümantasyon |

### 1.2 DB Katmanı

| Dosya | Sorumluluk |
|---|---|
| `models/prompt_template.py` | PromptTemplate DB modeli |
| `services/prompt_template_service.py` | Cache + DB + fallback service |
| `api/v1/admin/prompts.py` | Admin CRUD API |

### 1.3 İlgili Migration'lar (8 adet)

- `014_add_prompt_templates.py`
- `015_seed_full_prompt_templates.py`
- `021_add_prompt_debug_json_to_story_preview.py`
- `023_prompt_system_v2.py`
- `024_sync_prompt_templates_to_constants.py`
- `031_visual_style_prompt_overrides.py`
- `040_fix_visual_style_prompt_modifiers.py`
- `baf6123b9d1f_add_cover_and_page_prompt_templates_to_.py`

---

## 2. Entegrasyon Noktaları (Silme Öncesi Harita)

### 2.1 Servisler

| Dosya | Import Edilen Semboller |
|---|---|
| `services/ai/gemini_service.py` | compose_story_prompt, compose_visual_prompt, enhance_all_pages, build_character_bible, build_cover_prompt, blueprint_prompt, page_prompt, scenario_bible, story_validators, style_adapter, visual_prompt_validator, qa_checks, constants (çok sayıda), prompt_template_service |
| `services/ai/fal_ai_service.py` | FluxPromptBuilder, PromptContext, compose_visual_prompt, truncate_safe_2d, constants (NEGATIVE_PROMPT, STYLE_PULID_CONFIGS vb.) |
| `services/ai/gemini_consistent_image.py` | compose_visual_prompt, constants |
| `services/ai/image_generator.py` | compose_visual_prompt |
| `services/ai/__init__.py` | FluxPromptBuilder, PromptContext |

### 2.2 API Endpoint'leri

| Dosya | Import Edilen Semboller |
|---|---|
| `api/v1/ai.py` | personalize_style_prompt, compose_visual_prompt, constants, normalize_clothing_description, prompt_template_service |
| `api/v1/trials.py` | qa_checks, scenario_bible, constants, personalize_style_prompt, prompt_template_service |
| `api/v1/orders.py` | VisualPromptValidationError, personalize_style_prompt, constants, prompt_template_service |
| `api/v1/admin/orders.py` | get_display_visual_prompt, constants |
| `api/v1/admin/visual_styles.py` | constants, prompt_template_service |
| `api/v1/admin/prompts.py` | PromptTemplate model, prompt_template_service |
| `api/v1/admin/learning_outcomes.py` | PromptTemplate model |

### 2.3 Task'lar

| Dosya | Import Edilen Semboller |
|---|---|
| `tasks/generate_book.py` | FluxPromptBuilder, personalize_style_prompt, constants, prompt_template_service |

---

## 3. Görsel Tutarsızlığın Kök Nedenleri

1. **V2/V3 çift pipeline**: `page.v3_composed` flag'ine göre dallanma — bazı sayfalar V2, bazıları V3
2. **6 farklı stil enjeksiyon noktası**: leading_prefix, style_anchor, style_block, prefix, suffix ayrı ayrı ekleniyor
3. **Sayfa bazlı çözümleme**: Style config her sayfada ayrı resolve ediliyor
4. **LLM çıktı değişkenliği**: Gemini PASS-2 her sayfa için bağımsız scene_description üretiyor
5. **Kıyafet tespiti**: Bir kez yapılıyor, hata durumunda fallback farklı
6. **Template kaynağı belirsiz**: DB > Scenario > Constants öncelik net değil
7. **Negatif prompt farkı**: V2 sayfa bazlı, V3 kitap bazlı

---

## 4. Korunan Sistem Bileşenleri

Aşağıdaki dosyalar/sistemler SİLİNMEYECEK:

- `gemini_service.py` PASS-1 (hikaye yazımı) — çalışıyor
- `fal_ai_service.py` — görsel üretim altyapısı (prompt entegrasyonu değişecek)
- `gemini_consistent_image.py` — Gemini görsel üretim
- `page_composer.py` — metin bindirme
- `pdf_service.py` — PDF üretimi
- Order, Payment, User, Product, Trial tüm sistemi
- Frontend (admin/prompts hariç diğer tüm sayfalar)

---

## 5. Aktif Stil Tanımları (Yeni Sisteme Taşınacak)

| Key | Frontend Adı | Anchor |
|---|---|---|
| `default` | 2D Hikaye Kitabı | 2D hand-painted storybook |
| `pixar` | Sihirli Animasyon | Pixar-quality 3D CGI animation |
| `watercolor` | Sulu Boya Rüyası | Transparent watercolor painting |
| `soft_pastel` | Yumuşak Pastel | Soft pastel storybook illustration |
| `anime` | Anime Masalı | Studio Ghibli anime cel-shaded |
| `adventure_digital` | Macera Dijital | Digital painting adventure |

### PuLID Konfigürasyonları

| Stil | id_weight | start_step | true_cfg |
|---|---|---|---|
| pixar/disney/3d | 1.0 | 2 | 1.0 |
| 2d/storybook | 1.0 | 1 | 1.0 |
| watercolor/pastel | 1.0 | 1 | 1.2 |
| anime/ghibli | 1.0 | 0 | 1.5 |

---

## 6. Yeni Sistem Tasarımı

### Dosya Yapısı

```
backend/app/prompt/
  __init__.py          # Public API
  book_context.py      # BookContext dataclass
  composer.py          # PromptComposer (tek giriş noktası)
  cover_builder.py     # Kapak prompt oluşturma
  page_builder.py      # İç sayfa prompt oluşturma
  negative_builder.py  # Negatif prompt (basit)
  sanitizer.py         # Temizleme + TR→EN çeviri
  style_config.py      # Stil tanımları + çözümleme
  templates.py         # Default template'lar (DB fallback)
  story_composer.py    # Hikaye yazım prompt'u (PASS-1)
```

### Temel Prensip: Kitap Bazlı Tutarlılık

BookContext kitap başında BİR KEZ oluşturulur, TÜM sayfalara uygulanır.
Tek pipeline, tek composer, tek yol.
