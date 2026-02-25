# V3 Prompt System Audit — Özet

**Tam rapor:** [V3_PROMPT_SYSTEM_AUDIT.md](./V3_PROMPT_SYSTEM_AUDIT.md)

---

## Pipeline Özeti

| Aşama | Ne yapılıyor | Nerede |
|-------|----------------|--------|
| Girişler | child_name/age/gender, scenario_id, selected_outcomes, visual_style_id, child_photo_url | UI → Order/Trial |
| PASS-0 | Blueprint JSON (sayfa rolleri, shot_type, cultural_hook, visual_brief_tr) | gemini_service._pass0_generate_blueprint, blueprint_prompt |
| PASS-1 | 22 sayfa: text_tr, image_prompt_en, negative_prompt_en; value_message_tr enjekte | gemini_service._pass1_generate_pages, page_prompt |
| Enhance | CharacterBible, ShotPlan, style, value_visual_motif birleştirilir; sanitize + shot conflict temizliği | visual_prompt_builder.enhance_all_pages, compose_enhanced_prompt |
| Validate | SHOT_CONFLICT, VALUE_MOTIF_MISSING, placeholder, outfit, no-text, style mismatch, embedded text | visual_prompt_validator.validate_all |
| Görsel | Fal Flux-PuLID; reference_image_url, id_weight, start_step, true_cfg; seed opsiyonel | fal_ai_service._generate_with_composed_prompt |

---

## Dosya Haritası (Kısa)

- **Pipeline guard:** `core/pipeline_version.py` (sadece v3).
- **Hikaye + değer:** `gemini_service.py` (PASS-0/1, value message/motif, EDUCATIONAL_VALUE_PROMPTS).
- **Blueprint:** `blueprint_prompt.py`. **Sayfa metni:** `page_prompt.py`.
- **Final prompt:** `visual_prompt_builder.py` (enhance, cover, sanitize, shot conflict, value motif).
- **Validator:** `visual_prompt_validator.py` (shot conflict, value motif, placeholder, outfit, no-text, style, embedded text).
- **Shot plan:** `scene_director.py`. **Stil:** `constants.py`, `style_adapter.py`. **Karakter:** `character_bible.py`.
- **Görsel API:** `fal_ai_service.py`, `fal_request_builder.py`. **Modeller:** `order.py`, `order_page.py`, `visual_style.py`, `scenario.py`.

---

## Kritik Bulgular

1. **Prompt corruption ("a glowing ancient symbolm", "Ia glowing"):** Kaynak: _strip_embedded_text replacement "a glowing ancient symbol" + LLM/regex artefaktı. Çözüm: forbidden token check + sanitizer typo fix + unit test.
2. **Style weight:** id_weight DB (VisualStyle) veya constants (get_pulid_weight_for_style) ile uygulanıyor; UI’da ayrı “strength” yok. Çocuk hep benzer görünüyorsa: id_weight bandı dar (0.72–0.78), veya DB override yok.
3. **Value injection:** Var; value_message_tr PASS-1’e, value_visual_motif her sayfa + kapak prompt’una ekleniyor; VALUE_MOTIF_MISSING validator ile zorunlu.

---

## Validator Özeti

- **Mevcut:** PLACEHOLDER, OUTFIT_LOCK, SHOT_STREAK, ACTION_STREAK, NO_TEXT_MISSING, STYLE_MISMATCH, ANCHOR_CONTEXT, EMBEDDED_TEXT, **SHOT_CONFLICT**, **VALUE_MOTIF_MISSING**, NEAR_DUPLICATE.
- **Önerilen ek:** Forbidden tokens (typo’lar), max length uyarısı.

---

## Observability & PII

- **Şu an:** FINAL_PROMPT_SENT_TO_FAL, PROMPT_DEBUG, manifest (prompt_hash, id_weight, model, vb.).
- **Öneri:** inputs (adventure/value/style id), seed, output image id; çocuk fotoğrafı URL’i log’larda tam saklanmasın, PII stratejisi yazılsın.

---

## Aksiyonlar (Kısa)

| Süre | Aksiyon |
|------|---------|
| 1–3 gün | Forbidden token (typo) + sanitizer fix + test. |
| 1 hafta | Log/manifest’e inputs, seed, id_weight, output id; PII notu. |
| 1 ay | Linter MVP (conflict, forbidden, required, max length); istenirse UI’da id_weight. |
