# V3 Stil Sistemi Deep Dive — 7 Görsel Stil Analizi

> Son güncelleme: 2026-02-17

---

## 1. Stil Tanımı Nerede Yaşıyor?

Stil sistemi **iki katmanlı**: DB + Kod sabitleri. Kod her zaman fallback, DB admin override sağlar.

### Katman 1: DB — `visual_styles` tablosu

**Model:** `backend/app/models/visual_style.py` → `VisualStyle`

| Kolon | Tip | Rol |
|-------|-----|-----|
| `name` | String(255) | Kod eşleme anahtarı (ör. "Sihirli Animasyon") |
| `display_name` | String(255) | Frontend'e gösterilen isim (ör. "Pastel Rüya") |
| `prompt_modifier` | Text | `visual_style` parametresi olarak pipeline'a girer |
| `id_weight` | Float | PuLID yüz ağırlığı (NULL = kod fallback) |
| `style_negative_en` | Text | Stil negatif promptu (NULL = kod fallback) |
| `leading_prefix_override` | Text | Admin: leading prefix override (NULL = constants) |
| `style_block_override` | Text | Admin: STYLE: bloğu override (NULL = constants) |
| `is_active` | Boolean | Aktif/pasif |

### Katman 2: Kod — İki dosya

**`constants.py`** → `StyleConfig` dataclass presets (5 aktif: DEFAULT, PIXAR, WATERCOLOR, SOFT_PASTEL, ANIME, ADVENTURE_DIGITAL)

Her `StyleConfig`:
- `prefix` / `suffix` / `cover_prefix` / `cover_suffix` → V2 legacy compose path
- `leading_prefix` → prompt başına eklenen agresif stil bildirimi
- `style_block` → `STYLE:` bloğu olarak prompt sonuna eklenen stil DNA'sı

**`style_adapter.py`** → `_STYLE_DEFS` dict + `StyleMapping` dataclass (9 stil ailesi: default, pixar, watercolor, soft_pastel, anime, adventure_digital, 3d, realistic, comic)

Her `_STYLE_DEFS` entry:
- `style_block` → detaylı stil açıklaması (prompt'a "STYLE: ..." olarak eklenir)
- `render_language` → kısa EN render talimatları (PASS-1'e veriliyor)
- `forbidden_terms` → negatif prompt'a eklenen yasak terimler
- `style_anchor` → prompt'un EN BAŞINA eklenen 2-5 kelime (en yüksek diffusion weight)

---

## 2. Akış: Stil Seçimi → Prompt Enjeksiyonu

```
UI: visual_style seçimi (ör. "Sulu Boya Rüyası")
        │
        ▼
DB: VisualStyle.prompt_modifier (ör. "Transparent watercolor on textured paper...")
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  PASS-1 (Gemini LLM) — style_adapter.py                  │
│  get_style_instructions_for_prompt(visual_style)          │
│                                                           │
│  LLM'e verilen talimatlar:                                │
│  • "Stil: watercolor"                                     │
│  • "Render dili: watercolor texture, paper grain..."      │
│  • "Her image_prompt_en'in BAŞINA ekle: Transparent..."   │
│  • "YASAKLI terimler: 3D, CGI, Pixar..."                  │
│                                                           │
│  → LLM bu talimatları takip etmeli ama GARANTİ YOK       │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  POST-LLM: visual_prompt_builder.py                       │
│  compose_enhanced_prompt()                                │
│                                                           │
│  DETERMİNİSTİK enjeksiyon (LLM çıktısına bağlı değil):   │
│                                                           │
│  1. style_anchor → PROMPT BAŞI (en yüksek weight)         │
│     "Transparent watercolor painting."                    │
│                                                           │
│  2. character_bible.prompt_block → karakter kimliği        │
│                                                           │
│  3. cleaned LLM prompt → sahne açıklaması                 │
│                                                           │
│  4. key_objects, iconic_anchors                            │
│                                                           │
│  5. shot_plan.prompt_fragment → kamera                    │
│                                                           │
│  6. value_visual_motif                                    │
│                                                           │
│  7. emotion                                               │
│                                                           │
│  8. "STYLE: {style_block}" → PROMPT SONU                  │
│     "STYLE: Transparent watercolor illustration on..."    │
│                                                           │
│  9. "no text, no watermark, no logo"                      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│  NEGATIVE PROMPT: build_enhanced_negative()                │
│                                                           │
│  Formula:                                                 │
│    GLOBAL_NEGATIVE_PROMPT_EN                               │
│  + character_bible.negative_tokens                         │
│  + style_mapping.forbidden_terms ← STİLE GÖRE DEĞİŞİR    │
│  + gender negatives                                       │
│  + text-blocking tokens                                   │
│                                                           │
│  Tüm tokenlar dedup edilir.                                │
└──────────────────────────────────────────────────────────┘
```

**Kaynak dosyalar:**
- `style_adapter.py:280` → `adapt_style()` — stil ailesi çözme + StyleMapping döndürme
- `style_adapter.py:310` → `get_style_instructions_for_prompt()` — LLM'e stil talimatı
- `visual_prompt_builder.py:475` → `compose_enhanced_prompt()` — deterministik prompt assembly
- `visual_prompt_builder.py:619` → `build_enhanced_negative()` — negative prompt assembly
- `constants.py:444` → `get_style_config()` — StyleConfig preset seçimi

---

## 3. Stil Bazlı Detay Tablosu (7 Aktif + 2 Ek)

### 3.1 DEFAULT — 2D Hand-Painted Storybook

| Alan | Değer |
|------|-------|
| **style_tag** | `default` |
| **Eşleşme** | `2d` + `storybook/children's book`; diğer stillere uymayan her şey |
| **DB Kaynak** | `VisualStyle.prompt_modifier` → keywords: "2D", "children's book", "storybook" |
| **Kod Kaynak** | `constants.py:249` → `DEFAULT_STYLE`, `style_adapter.py:65` → `_STYLE_DEFS["default"]` |
| **style_anchor** | `"2D hand-painted storybook."` |
| **Inject yeri** | Prompt'un EN BAŞI (1. token grubu) |
| **STYLE: block** | `"Cheerful 2D hand-painted storybook illustration, traditional gouache/acrylic feel, crisp but organic linework, simplified shapes, warm vibrant colors (greens, blues, yellows, pinks), soft shading, subtle paper texture, bright inviting light, detailed layered background"` |
| **Inject yeri** | Prompt SONU: `"STYLE: Cheerful 2D..."` |
| **leading_prefix** | `"Art style: Cheerful 2D hand-painted storybook illustration. Crisp lineart, simplified shapes, vibrant warm colors (greens, blues, yellows, pinks), soft shading, subtle paper texture, bright light, detailed layered background. NOT 3D, NOT anime, NOT digital, NO cinematic, NO film still, NO lens terms."` |
| **Inject yeri** | V2 legacy path başı; V3'te kullanılmaz |
| **forbidden_terms** | `3D, CGI, Pixar, Disney, photorealistic, photography, anime, manga, cel-shaded, ray tracing, film still` |
| **Negative ek** | `"text overlay, logo, letters on image, head rotated, anime, manga, 3d render, CGI, big eyes, chibi, oversized head, wrong hair color, wrong skin color, different hair length, inconsistent hairstyle, cropped body, cut-off legs, missing feet"` |
| **PuLID id_weight** | 0.70–0.75 (keywords: `2d`→0.75, `children's book`→0.70) |

---

### 3.2 PIXAR — 3D CGI Animation

| Alan | Değer |
|------|-------|
| **style_tag** | `pixar` |
| **Eşleşme** | `pixar`, `disney`, `cizgi film`, `cinematic` + `3d/cgi` |
| **style_anchor** | `"Pixar-quality 3D CGI animation."` |
| **STYLE: block** | `"Pixar-quality 3D CGI animation, smooth 3D surfaces, subsurface scattering on skin, rim lighting, ambient occlusion, warm cinematic color grading, fully modeled 3D environment, soft global illumination, high detail"` |
| **leading_prefix** | `"Art style: Pixar-quality 3D CGI animation. Smooth 3D surfaces, subsurface scattering, rim lighting, warm cinematic illumination, Disney/Pixar look. NOT 2D, NOT hand-painted, NOT lineart, NOT watercolor, NOT paper texture."` |
| **forbidden_terms** | `watercolor, paper texture, lineart, 2D hand-painted, gouache, oil paint, pencil sketch, brush strokes, flat shading, cel-shaded, anime, manga` |
| **Negative ek** | `"text overlay, logo, letters on image, head rotated, 2d, flat, flat shading, lineart, hand-drawn, hand-painted, watercolor, gouache, oil paint, pencil sketch, paper texture, brush strokes, cartoon 2d, anime, manga, cel-shaded, big eyes, chibi, oversized head, ..."` |
| **PuLID id_weight** | 0.78 |

---

### 3.3 WATERCOLOR — Transparent Watercolor

| Alan | Değer |
|------|-------|
| **style_tag** | `watercolor` |
| **Eşleşme** | `watercolor`, `sulu boya`, `suluboya`, `watercolour` |
| **style_anchor** | `"Transparent watercolor painting."` |
| **STYLE: block** | `"Transparent watercolor illustration on textured cold-pressed paper, soft washes, wet-on-wet bleeding edges, visible brush strokes, paper grain, pigment granulation, transparent color layers, dreamy pastel palette, luminous atmosphere"` |
| **leading_prefix** | `"Art style: Transparent watercolor on textured paper. Wet-on-wet bleeding, granulating pigments, layered washes, soft pastel palette (lavender, pink, sage green). Dreamy atmosphere. NO digital, NO flat, NO 3D."` |
| **forbidden_terms** | `3D, CGI, Pixar, Disney, film still, cinematic lens, ray tracing, photorealistic, photography, studio lighting` |
| **Negative ek** | `"text overlay, logo, letters on image, head rotated, 3d render, CGI, photorealistic, big eyes, chibi, oversized head, ..."` |
| **PuLID id_weight** | 0.72 |

---

### 3.4 SOFT_PASTEL — Yumuşak Pastel

| Alan | Değer |
|------|-------|
| **style_tag** | `soft_pastel` |
| **Eşleşme** | `soft pastel`, `yumusak pastel`, `pastel ruya`, `cosy illustration`, `warm pastel` |
| **style_anchor** | `"Soft pastel storybook illustration."` |
| **STYLE: block** | `"Soft pastel storybook illustration, gentle hand-drawn outlines (thin brown/gray lines), warm muted palette (beige, cream, soft coral, gentle blues), paper-like softness, cosy atmosphere, soft diffused lighting"` |
| **leading_prefix** | `"Art style: Soft pastel storybook. Thin brown/gray outlines, gentle hand-drawn look, warm muted palette (beige, cream, coral, blues), pastel texture, cosy atmosphere, soft light. NOT 3D, NOT photorealistic, NOT bold cartoon."` |
| **forbidden_terms** | `3D, CGI, Pixar, photorealistic, bold black outlines, harsh contrast, neon colors, anime, cel-shaded` |
| **Negative ek** | `"text overlay, logo, letters on image, head rotated, 3d render, CGI, photorealistic, harsh black outlines, big eyes, chibi, oversized head, ..."` |
| **PuLID id_weight** | 0.74–0.75 |

---

### 3.5 ANIME — Studio Ghibli Cel-Shaded

| Alan | Değer |
|------|-------|
| **style_tag** | `anime` |
| **Eşleşme** | `ghibli`, `cel-shading`, `cel shading`, `anime` (soft pastel yoksa) |
| **style_anchor** | `"Studio Ghibli anime cel-shaded."` |
| **STYLE: block** | `"Studio Ghibli anime cel-shaded illustration, bold ink outlines, flat color fills with subtle gradients, vibrant saturated colors, Miyazaki-style backgrounds, rich scenic environment, vivid sky"` |
| **leading_prefix** | `"Art style: Studio Ghibli anime cel-shaded. Bold ink outlines, flat color fills, vibrant gradients, Miyazaki-style backgrounds, vivid sky, rich saturated colors. NOT 3D, NOT realistic, NOT Western cartoon, NOT watercolor."` |
| **forbidden_terms** | `3D, CGI, photorealistic, photography, studio lighting, watercolor bleeding, paper grain, gouache texture` |
| **Negative ek** | `"text overlay, logo, letters on image, head rotated, 3d render, CGI, photorealistic, big eyes, chibi, oversized head, ..."` |
| **PuLID id_weight** | 0.76 |

---

### 3.6 ADVENTURE_DIGITAL — Macera Dijital Boyama

| Alan | Değer |
|------|-------|
| **style_tag** | `adventure_digital` |
| **Eşleşme** | `adventure`, `digital painting`, `macera`, `painterly`, `earth tones`, `dijital boyama` |
| **style_anchor** | `"Digital painting adventure."` |
| **STYLE: block** | `"Vibrant digital painting for children's adventure book, warm natural lighting, detailed textures, traditional gouache/acrylic look, painterly brushwork, cheerful mood, rich saturated earth-tone colors"` |
| **leading_prefix** | `"Art style: Adventure 2D digital painting for children's storybook. Vibrant warm colors (greens, blues, golden yellows, browns), bright lighting, painterly brushwork, detailed textures, cheerful mood. NOT cartoon flat, NOT anime, NOT 3D, NOT gouache."` |
| **forbidden_terms** | `3D, CGI, Pixar, photorealistic, anime, manga, cel-shaded, flat shading` |
| **Negative ek** | `"text overlay, logo, letters on image, head rotated, anime, manga, 3d render, big eyes, chibi, oversized head, ..."` |
| **PuLID id_weight** | 0.72 |

---

### 3.7 3D — Generic 3D Render

| Alan | Değer |
|------|-------|
| **style_tag** | `3d` |
| **Eşleşme** | `3d` (Pixar/Disney keyword'leri yoksa) |
| **style_anchor** | `"3D rendered illustration."` |
| **STYLE: block** | `"3D render, soft studio lighting, smooth materials, depth of field, ambient occlusion, global illumination, clean 3D environment"` |
| **forbidden_terms** | `watercolor, hand-painted, lineart, paper texture, gouache, anime, cel-shaded` |
| **PuLID id_weight** | 0.78 (`3d` keyword) |

---

### Ek: REALISTIC ve COMIC (style_adapter.py'de tanımlı, aktif DB stili yok)

| style_tag | style_anchor | forbidden_terms |
|-----------|-------------|-----------------|
| `realistic` | `"Realistic illustration."` | anime, manga, cel-shaded, cartoon, chibi, flat colors, bold outlines |
| `comic` | `"Comic book illustration."` | 3D, CGI, photorealistic, watercolor, paper grain |

---

## 4. Prompt'a Enjeksiyon Noktaları — Detaylı

### V3 Pipeline (Aktif)

Stil, prompt'a **3 noktada** enjekte edilir:

```
┌─────────────────────────────────────────────────────────────┐
│ [1] style_anchor (2-5 kelime) — PROMPT BAŞI                 │
│     "Transparent watercolor painting."                      │
│     Kaynak: style_adapter.py → _STYLE_DEFS[family]          │
│     Weight: EN YÜKSEK (diffusion modeli ilk tokenlere        │
│             en çok ağırlık verir)                            │
│                                                              │
│ [2] ... character + scene + objects + camera + emotion ...    │
│                                                              │
│ [3] "STYLE: {style_block}" — PROMPT SONU                    │
│     "STYLE: Transparent watercolor illustration on           │
│      textured cold-pressed paper, soft washes, wet-on-wet    │
│      bleeding edges, visible brush strokes, paper grain..."  │
│     Kaynak: style_adapter.py → _STYLE_DEFS[family]          │
│     Weight: DÜŞÜK (son tokenler daha az ağırlık alır)        │
└─────────────────────────────────────────────────────────────┘

NEGATIVE PROMPT:
┌─────────────────────────────────────────────────────────────┐
│ [N1] GLOBAL_NEGATIVE_PROMPT_EN (evrensel: text, blurry...)   │
│ [N2] character_bible.negative_tokens                         │
│ [N3] style_mapping.forbidden_terms ← STİLE GÖRE             │
│      "3d, cgi, pixar, disney, film still, cinematic lens..." │
│ [N4] gender negatives                                        │
│ [N5] text-blocking tokens                                    │
└─────────────────────────────────────────────────────────────┘
```

**Ayrıca PASS-1'de (LLM'e):**
- `get_style_instructions_for_prompt()` → LLM'e stil adı, render dili, style_anchor ve yasaklı terimleri verir
- LLM bunu takip etmeli ama **deterministik garanti yok** — post-LLM enhancement garantiler

### V2 Legacy Path (skip_compose=False)

V2'de ek olarak `leading_prefix` de prompt başına eklenir ve DB override'lar (`leading_prefix_override`, `style_block_override`) devreye girer. V3'te `skip_compose=True` olduğundan bu path **atlanır**.

---

## 5. Stil "Weak" Kalmasının 5 Temel Nedeni

### Neden 1: `STYLE:` Bloğu Prompt Sonunda — Düşük Token Weight

**Problem:** Diffusion modelleri (Flux dahil) ilk tokenlere daha fazla ağırlık verir. `STYLE:` bloğu prompt'un EN SONUNDA (~pozisyon 400-500 karakter). `max_sequence_length=512` token'da son bölüm zayıf kalır.

**Etki:** Stil direktifleri (renk paleti, doku, ışık) uygulanmıyor veya zayıf uygulanıyor.

**Kanıt:**
```
compose_enhanced_prompt() assembly sırası:
  1. style_anchor ← KISA (2-5 kelime) — güçlü ama yetersiz
  ...
  8. "STYLE: {full_style_block}" ← 80-150 kelime — ÇOK GEÇ
```

**Kaynak:** `visual_prompt_builder.py:540-573`

**Çözüm önerisi:** Style block'un en kritik 3-4 token'ını (`style_anchor` gibi) prompt'un ilk 50 karakterine taşı. Ayrıca `leading_prefix` V3 path'te kullanılmıyor — kullanılmalı.

---

### Neden 2: Style Anchor Çok Kısa (2-5 kelime)

**Problem:** `style_anchor` sadece 2-5 kelime:
- `"Transparent watercolor painting."` (3 kelime)
- `"Soft pastel storybook illustration."` (4 kelime)

Bu, diffusion modelinin stil yönünü belirlemek için **yetersiz**. Geri kalan 400+ kelimelik prompt'ta sahne, karakter, kamera, obje bilgisi stil anchor'ı eziyor.

**Kaynak:** `style_adapter.py:64-208` → `_STYLE_DEFS`

---

### Neden 3: `leading_prefix` V3'te Kullanılmıyor

**Problem:** `constants.py`'daki `StyleConfig.leading_prefix` V3 pipeline'da hiç enjekte edilmiyor. Bu leading_prefix agresif stil bildirimi içerir (80-120 kelime, "NOT 3D, NOT anime..." gibi negasyon dahil) ve V2'de prompt başına eklenir.

V3'te `compose_enhanced_prompt()` sadece `style_anchor` (kısa) ve `STYLE:` bloğunu (sonda) kullanır. `leading_prefix` kayıp.

**Kod kanıtı:**
```python
# V3: compose_enhanced_prompt() — leading_prefix KULLANILMIYOR
parts = []
if style_mapping.style_anchor:       # ← kısa (2-5 kelime)
    parts.append(style_mapping.style_anchor)
parts.append(character_bible.prompt_block)
# ... 6 katman daha ...
if style_mapping.style_block:         # ← sonda (düşük weight)
    parts.append(f"STYLE: {style_mapping.style_block}")
```

**Kaynak:** `visual_prompt_builder.py:540-573`

**Karşılaştırma — V2:**
```python
# V2: compose_visual_prompt() — leading_prefix prompt BAŞINDA
leading_prefix = leading_prefix_override or get_style_leading_prefix(effective_style)
prompt = f"{leading_prefix} {prompt}"
# ... sonra STYLE bloğu da eklenir
```

**Kaynak:** `visual_prompt_composer.py:624`

---

### Neden 4: Prompt Çok Uzun — Token Budget Taşması

**Problem:** V3 enhanced prompt tipik olarak 350-500 karakter / 80-120 token. `STYLE:` bloğu ile birlikte 500-700 karakter / 130-170 token olur. Fal.ai `max_sequence_length=512` token. Gerçek token sayısı ~4 char/token değil, BPE tokenizer kullanır — bazı stil terimleri çok token yer. `STYLE:` bloğu kısmen kesilir.

**Kaynak:** `constants.py:49-51` → `MAX_FAL_PROMPT_CHARS = 2048`

**Ama dikkat:** Fal server-side da 512 token ile truncate eder. Backend'de 2048 char geçse bile Fal'ın kendi token limiti stil bloğunun sonunu kesebilir.

---

### Neden 5: Sanitizer Stil Terimlerini Siliyor

**Problem:** `constants.py:121-159` → `CINEMATIC_LENS_TERMS` regex listesi "cinematic", "volumetric lighting", "studio lighting", "concept art" gibi terimleri siler. Pixar stili "warm cinematic color grading" içerir ama sanitizer bunu temizleyebilir (eğer V2 legacy path'te `_strip_cinematic_lens_terms` çağrılırsa).

V3'te `compose_enhanced_prompt()` bu sanitizer'ı **doğrudan çağırmıyor**, ama `_strip_existing_composition()` bazı shot/composition direktiflerini siler.

**V3'te etki**: Düşük — ama LLM'in ürettiği `image_prompt_en`'de "cinematic" geçerse `_kids_safe_rewrite` veya `_strip_embedded_text` onu silmez, sadece `_strip_existing_composition` bazı kamera terimlerini siler.

---

## 6. DB Override Mekanizması

Admin panelde her stil için 3 override alanı var:

| DB Kolon | Kullanım | Öncelik |
|----------|----------|---------|
| `leading_prefix_override` | V2: prompt başındaki stil prefix | DB dolu → kullanılır; boş → `constants.get_style_leading_prefix()` |
| `style_block_override` | V2: "STYLE:" bloğu içeriği | DB dolu → kullanılır; boş → `StyleConfig.style_block` |
| `id_weight` | PuLID face weight | DB dolu → kullanılır; boş → `STYLE_PULID_WEIGHTS` fallback |

**KRİTİK:** Bu override'lar **sadece V2 legacy path**'te (`compose_visual_prompt`) çalışır. V3 pipeline `skip_compose=True` ile Fal'a gittiğinde bu override'lar **bypass edilir**. V3'te stil bilgisi `adapt_style()` + `_STYLE_DEFS` + `StyleConfig` preset'lerinden gelir — DB override'lar etkisiz.

**Kaynak:**
- V2 override kullanımı: `visual_prompt_composer.py:624-636`
- V3 stil çözme: `visual_prompt_builder.py:715` → `adapt_style(visual_style)`
- V3 Fal çağrısı: `fal_ai_service.py:381-385` → `skip_compose=True` → `leading_prefix_override` ve `style_block_override` parametreleri Fal'a geçirilir ama `generate_consistent_image()` içinde V3 path'te **kullanılmaz**

---

## 7. Özet Tablo: 7 Stil Karşılaştırması

| # | style_tag | style_anchor (prompt başı) | STYLE: block (prompt sonu, ~chars) | forbidden_terms (negative) | id_weight | render_language (LLM'e) |
|---|-----------|---------------------------|----------------------------------|---------------------------|-----------|------------------------|
| 1 | `default` | `2D hand-painted storybook.` | Cheerful 2D hand-painted storybook... (~200ch) | 3D, CGI, Pixar, Disney, photorealistic, photography, anime, manga, cel-shaded, ray tracing, film still | 0.70-0.75 | cheerful 2D children's book illustration, hand-painted feel, crisp lineart, warm vibrant colors, soft shading, subtle paper texture |
| 2 | `pixar` | `Pixar-quality 3D CGI animation.` | Pixar-quality 3D CGI animation, smooth 3D surfaces... (~180ch) | watercolor, paper texture, lineart, 2D hand-painted, gouache, oil paint, pencil sketch, brush strokes, flat shading, cel-shaded, anime, manga | 0.78 | Pixar-quality 3D CGI, smooth rounded 3D forms, soft subsurface scattering, volumetric lighting, rim lighting, warm cinematic color grading |
| 3 | `watercolor` | `Transparent watercolor painting.` | Transparent watercolor illustration on textured cold-pressed paper... (~200ch) | 3D, CGI, Pixar, Disney, film still, cinematic lens, ray tracing, photorealistic, photography, studio lighting | 0.72 | watercolor texture, paper grain, soft washes, visible brush strokes, wet-on-wet bleeding edges, pigment granulation |
| 4 | `soft_pastel` | `Soft pastel storybook illustration.` | Soft pastel storybook illustration, gentle hand-drawn outlines... (~170ch) | 3D, CGI, Pixar, photorealistic, bold black outlines, harsh contrast, neon colors, anime, cel-shaded | 0.74-0.75 | soft pastel colors, gentle outlines, dreamy atmosphere, muted warm tones, thin brown/gray outlines, cosy mood |
| 5 | `anime` | `Studio Ghibli anime cel-shaded.` | Studio Ghibli anime cel-shaded illustration, bold ink outlines... (~170ch) | 3D, CGI, photorealistic, photography, studio lighting, watercolor bleeding, paper grain, gouache texture | 0.76 | anime illustration, clean lineart, cel-shading, flat color fills with gradients, bold ink outlines, vibrant saturated colors |
| 6 | `adventure_digital` | `Digital painting adventure.` | Vibrant digital painting for children's adventure book... (~165ch) | 3D, CGI, Pixar, photorealistic, anime, manga, cel-shaded, flat shading | 0.72 | vibrant digital painting, warm natural lighting, detailed textures, painterly brushwork, cheerful adventure mood |
| 7 | `3d` | `3D rendered illustration.` | 3D render, soft studio lighting, smooth materials... (~110ch) | watercolor, hand-painted, lineart, paper texture, gouache, anime, cel-shaded | 0.78 | 3D render, soft studio lighting, smooth materials, depth of field, ambient occlusion |

---

## 8. Aksiyon Planı: Stil Güçlendirme

### Kısa Vade (1-3 gün)

1. **V3'te `leading_prefix` enjekte et**
   - `compose_enhanced_prompt()`'a `style_mapping.leading_prefix` parametresi ekle
   - `style_anchor`'dan hemen sonra, `character_bible`'dan önce inject et
   - Diffusion weight sıralaması: anchor → leading_prefix → character → scene → ... → STYLE:

2. **STYLE: bloğunu kısalt**
   - Mevcut 150-200 char → 80-100 char'a düşür
   - Sadece benzersiz stil DNA'sı bırak (renk paleti, doku, ışık)
   - Tekrarlayan "natural proportions", "sharp focus" gibi genel terimler çıkar

3. **DB override'ları V3'te aktif et**
   - `enhance_all_pages()`'e `leading_prefix_override` ve `style_block_override` parametreleri geçir
   - DB değer doluysa `_STYLE_DEFS` yerine DB değerini kullan

### Orta Vade (1 hafta)

4. **Token bütçesi kontrolü**
   - Her stil için max prompt token sayısını ölç (Fal BPE tokenizer ile)
   - Style block'un kesilmediğini doğrula
   - Prompt'u "pre-STYLE" ve "STYLE" bölümlerine ayır, toplam 480 token hedefle

5. **Stil A/B testi**
   - Aynı sahne, 7 stil ile üret → görsel fark ölç
   - "Weak" olan stilleri tespit et → style_anchor/block güçlendir

### Uzun Vade (1 ay)

6. **Stil-aware prompt template**
   - Her stil ailesi için ayrı prompt şablonu (shot, ışık, kamera)
   - Watercolor: "gentle wash of colors", Pixar: "clean 3D geometry"
   - Generic "wide shot, child 30%" yerine stile özgü kamera dili

7. **Admin stil editörü**
   - DB override'ları V3'te çalışır hale getir
   - Admin panelde "prompt preview" → stilin son prompt'taki etkisini göster
