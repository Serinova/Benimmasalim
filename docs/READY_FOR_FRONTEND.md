# Backend V2 — Ready for Frontend

**Date:** 2026-02-06  
**Status:** ✅ STABLE — 90 tests pass, E2E verified, migration applied.

---

## Checklist

- [x] All V2 DB columns created and migrated (Alembic 023)
- [x] COVER_TEMPLATE and INNER_TEMPLATE seeded in `prompt_templates`
- [x] `prompt_engine/` modules complete (7 modules, 51 dedicated tests)
- [x] Story generation (PASS-1) reads `story_prompt_tr` with fallback
- [x] Visual prompts composed via single `compose_visual_prompt` entry point
- [x] Style injection happens ONLY at compose layer (not in scenario)
- [x] Negative prompt always includes strict additions (big eyes, chibi, extra fingers, etc.)
- [x] Location normalized: "Kapadokya" → "Cappadocia" in EN prompts
- [x] `no_family` flag enforced in PASS-1
- [x] `prompt_debug_json` and `generation_manifest_json` populated per preview
- [x] Admin endpoints expose V2 fields (backward-compatible with legacy)
- [x] Full test suite passes (90/90 + 1 skipped E2E)

---

## Admin API Field Mapping

### `/admin/scenarios` (GET/POST/PUT)

| Field | Type | V2 Purpose | Notes |
|-------|------|------------|-------|
| `name` | string | Display name | Required |
| `description` | string | Short description | Optional |
| `story_prompt_tr` | text | **V2** Turkish story-writing prompt for Gemini PASS-1 | Replaces `ai_prompt_template` |
| `location_en` | string(100) | **V2** English location tag (e.g., "Cappadocia") | Used in location constraint |
| `flags` | json | **V2** Flexible flags (e.g., `{"no_family": true}`) | JSONB |
| `default_page_count` | int | **V2** Default story page count | Default: 6 |
| `cover_prompt_template` | text | Legacy cover template | Still accepted |
| `page_prompt_template` | text | Legacy page template | Still accepted |
| `ai_prompt_template` | text | Legacy AI prompt | Fallback for `story_prompt_tr` |
| `thumbnail_url` | text | Card thumbnail | Required |

### `/admin/prompts` (GET/POST/PUT)

| Field | Type | V2 Purpose | Notes |
|-------|------|------------|-------|
| `key` | string | Unique lookup key | e.g., `COVER_TEMPLATE`, `INNER_TEMPLATE` |
| `name` | string | Human-readable name | Required |
| `content` | text | TR prompt content | For story-related templates |
| `template_en` | text | **V2** EN visual template with placeholders | `{scene_description}`, `{clothing_description}` |
| `category` | string | Category grouping | `story_generation`, `visual_director`, etc. |
| `is_active` | bool | Active flag | Default: true |

### `/admin/learning-outcomes` (GET/POST/PUT)

| Field | Type | V2 Purpose | Notes |
|-------|------|------------|-------|
| `name` | string | Display name | Required |
| `ai_prompt_instruction` | text | Value injection prompt (TR) | Primary field |
| `ai_prompt` | text | Legacy AI prompt | Fallback |
| `banned_words_tr` | text | **V2** Comma-separated TR banned words | Used with `no_family` flag |
| `category` | string | Outcome category | Required |

### `/admin/visual-styles` (GET/POST/PUT)

| Field | Type | V2 Purpose | Notes |
|-------|------|------------|-------|
| `name` | string | Display name | Required |
| `prompt_modifier` | text | EN style injection text | e.g., "watercolor children's book illustration" |
| `style_negative_en` | text | **V2** Style-specific negative tokens | Optional |
| `thumbnail_url` | text | Style preview image | Required |
| `id_weight` | float | PuLID face weight | Default: 0.35 |

---

## Frontend Payloads

### 1. Story Generation Request

```json
POST /api/v1/ai/test-story-structured
{
  "child_name": "Zeynep",
  "child_age": 6,
  "child_gender": "kiz",
  "child_photo_url": "https://storage.example.com/photo.jpg",
  "scenario_name": "Kapadokya",
  "scenario_prompt": "Kapadokya macerası",
  "learning_outcomes": ["Cesaret", "Paylaşma"],
  "visual_style": "watercolor children's book illustration",
  "page_count": 6
}
```

### 2. Story Generation Response

```json
{
  "title": "Zeynep'in Kapadokya Macerası",
  "pages": [
    {
      "page_number": 0,
      "text": "Zeynep bir sabah...",
      "scene_description": "A young girl standing at the edge of a fairy chimney valley",
      "visual_prompt": "A young girl standing at..., watercolor children's book illustration, ...",
      "negative_prompt": "asian architecture, ..., big eyes, chibi, extra fingers"
    }
  ]
}
```

### 3. Submit Preview Request

```json
POST /api/v1/orders/submit-preview-async
{
  "parent_name": "Ayşe",
  "parent_email": "ayse@example.com",
  "child_name": "Zeynep",
  "child_age": 6,
  "child_gender": "kiz",
  "child_photo_url": "https://...",
  "story_title": "Zeynep'in Kapadokya Macerası",
  "story_pages": [
    { "page_number": 0, "text": "...", "visual_prompt": "..." },
    { "page_number": 1, "text": "...", "visual_prompt": "..." }
  ],
  "visual_style": "watercolor children's book illustration",
  "scenario_name": "Kapadokya"
}
```

### 4. Submit Preview Response

```json
{
  "preview_id": "uuid",
  "status": "processing",
  "confirmation_token": "abc123...",
  "estimated_wait_seconds": 60
}
```

---

## Image Dimensions

| Type | Width | Height | Aspect |
|------|-------|--------|--------|
| Cover | 768 | 1024 | 3:4 (portrait) |
| Inner page | 1024 | 768 | 4:3 (landscape) |

---

## Public Scenarios Route (Frontend Selection)

```
GET /api/v1/scenarios
```

Returns only display fields: `id`, `name`, `description`, `thumbnail_url`, `gallery_images`.  
Does NOT expose prompt templates or V2 admin fields (by design).

---

## Key Notes for Frontend

1. **Scenario selection:** Use `scenario_name` (string) in story generation requests.
2. **Visual style selection:** Use `prompt_modifier` text from `/admin/visual-styles` as `visual_style` parameter.
3. **Learning outcomes:** Pass outcome names as string array in `learning_outcomes`.
4. **Child photo:** Must be a publicly accessible URL.
5. **Preview flow:** Submit → poll status → confirm when ready.
6. **Style is never stored in scenario:** Frontend does not need to handle style tokens per scenario.
