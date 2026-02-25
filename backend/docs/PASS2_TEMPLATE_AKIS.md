# PASS-2 ve Şablon Akışı (Tek Doğru Kaynak)

## 1. Hedef mimari

- **PASS-2 (Gemini / AI_DIRECTOR_SYSTEM)** sadece şunu üretir:
  - Her sayfa: `scene_description` (İngilizce, 1–3 kısa cümle).
  - Sadece sahne: lokasyon + environment + aksiyon + duygu.
  - Style / negative / lens / camera / render / anime vb. **asla** geçmez.
  - "Space for title at top" / "Empty space at bottom" **PASS-2 çıktısında yazılmaz** (şablonda yönetilir).

- **PASS-3 (Fal prompt)** final prompt’u şablonlarla üretir:
  - **Kapak:** `COVER_TEMPLATE` → `A young child wearing {clothing_description}. {scene_description}. Space for title at top.`
  - **İç sayfa:** `INNER_TEMPLATE` → `A young child wearing {clothing_description}. {scene_description}. Empty space at bottom for captions (no text in image).`

## 2. AI_DIRECTOR_SYSTEM

- Kaynak: `app.services.ai.gemini_service.AI_DIRECTOR_SYSTEM` (tek kaynak).
- DB: Admin panelde görünsün diye `prompt_templates.key = 'AI_DIRECTOR_SYSTEM'` migration ile sync edilir (026).
- İçerik: Çıktı formatı sabit (JSON, scene_description), boşluk metinleri çıktıda yok, yasak liste (anime, ghibli, pixar, 3D, CGI, render, lens, camera, bokeh, cinematic, photorealistic, watermark, logo, vb.), kıyafet en fazla 1 kez veya hiç.

## 3. Cover / Inner template

- **Kaynak:** `app.prompt_engine.constants`
  - `DEFAULT_COVER_TEMPLATE_EN` = `A young child wearing {clothing_description}. {scene_description}. Space for title at top.`
  - `INNER_SAFE_AREA_PHRASE` = `Empty space at bottom for captions (no text in image).`
  - `DEFAULT_INNER_TEMPLATE_EN` = `A young child wearing {clothing_description}. {scene_description}. ` + INNER_SAFE_AREA_PHRASE
- DB: `prompt_templates` (COVER_TEMPLATE, INNER_TEMPLATE) admin panelden düzenlenebilir; kod `get_template_en(db, key, default)` ile DB’den alır, yoksa constants kullanır.
- `scene_description` alanı sadece sahne cümlesi; içinde "space for title" / "empty space bottom" geçmemeli (sanitize ile temizlenir).

## 4. PASS-2 doğrulama (kod)

- **Dosya:** `app.services.ai.gemini_service`
- **Değişiklikler:**
  - `_sanitize_scene_description(scene_desc)`: PASS-2 çıktısı parse edildikten sonra her sayfa için çağrılır.
  - `FORBIDDEN_IN_SCENE`: Şu ifadeler scene_description’dan **otomatik silinir**:
    - space for title, title safe area, empty space at bottom, bottom text space, caption area, watermark, logo, lens, camera, dslr, bokeh, cinematic, photorealistic, render, cgi, anime, ghibli, miyazaki, manga, cel-shaded, pixar, disney, unreal, octane, blender.
  - `_compose_visual_prompts` içinde: `scene_desc = self._sanitize_scene_description(page.scene_description)` ile zorunlu temizlik uygulanır.

## 5. Teslim özeti

| Öğe | Konum |
|-----|--------|
| Güncel AI_DIRECTOR_SYSTEM metni | `gemini_service.AI_DIRECTOR_SYSTEM` + migration 026 (DB sync) |
| Cover template | `constants.DEFAULT_COVER_TEMPLATE_EN`; DB: COVER_TEMPLATE |
| Inner template | `constants.DEFAULT_INNER_TEMPLATE_EN`; DB: INNER_TEMPLATE |
| PASS-2 parse/validate | `gemini_service._sanitize_scene_description` + `FORBIDDEN_IN_SCENE`; `_compose_visual_prompts` içinde her sayfa için çağrı |

Migration çalıştırma: `alembic upgrade head`
