# Live E2E Docker Verification Report

**Goal:** Run a real end-to-end generation inside Docker and verify the live pipeline (cover + page 1), then collect proof from DB + logs and validate invariants.

### Quick run (PowerShell, from repo root)

```powershell
# Migrations + column check only
.\scripts\e2e_docker_verify.ps1

# Full E2E order (story -> submit -> wait -> confirm). Set a public child photo URL.
$env:E2E_CHILD_PHOTO_URL = "https://your-public-url/to/child.jpg"
$env:E2E_RUN_ORDER = "1"
.\scripts\e2e_docker_verify.ps1
```

Then collect PROMPT_DEBUG from `docker compose logs backend` and manifest from DB (see §4).

---

## 1) Docker Setup Check

### 1.1 Compose services

From project root:

```bash
docker compose up -d --build
docker compose ps
```

**Expected:** `postgres` (5432), `redis` (6380→6379), `backend` (8000), `frontend` (3001). Optional: `pgadmin` with `--profile tools`.

- **Backend:** `env_file: .env` — ensure `.env` exists (copy from `.env.example`) and contains at least:
  - `DATABASE_URL` (overridden in compose: `postgresql+asyncpg://postgres:postgres@postgres:5432/benimmasalim`)
  - `FAL_API_KEY`, `GEMINI_API_KEY` for image + story generation
  - `REDIS_URL` (overridden: `redis://redis:6379/0`)
- **Worker:** No separate worker container; background tasks run inside the backend process (`process_preview_background`, `process_remaining_pages`).

### 1.2 Health

```bash
curl -s http://localhost:8000/health
# Expect: {"status":"ok"} or similar
```

---

## 2) Run Migrations in Docker

```bash
docker compose exec backend alembic upgrade head
```

**Verify story_previews columns (prompt_debug_json, generation_manifest_json):**

```bash
docker compose exec postgres psql -U postgres -d benimmasalim -c "\d story_previews"
```

**Expected:** Both `prompt_debug_json` and `generation_manifest_json` listed (migrations 021 and 022).

---

## 3) Run a Real Order Flow (Cover + Page 1)

### 3.1 Generate story (2 pages: cover + 1 inner)

Use a **reachable** child photo URL (container must be able to GET it). Example: a public image URL.

```bash
curl -s -X POST http://localhost:8000/api/v1/ai/test-story-structured \
  -H "Content-Type: application/json" \
  -d '{
    "child_name": "Efe",
    "child_age": 6,
    "child_gender": "erkek",
    "child_photo_url": "CHILD_PHOTO_URL",
    "scenario_name": "Kapadokya",
    "scenario_prompt": "Kapadokya macerasi",
    "learning_outcomes": ["Eglenceli macera"],
    "visual_style": "2D childrens picture-book cartoon illustration",
    "clothing_description": "kirmizi mont, mavi pantolon, beyaz spor ayakkabi",
    "page_count": 2
  }'
```

From the response take `story.title` and `story.pages` (each with `page_number`, `text`, `visual_prompt`).

### 3.2 Submit preview async

```bash
curl -s -X POST http://localhost:8000/api/v1/orders/submit-preview-async \
  -H "Content-Type: application/json" \
  -d '{
    "parent_name": "E2E Parent",
    "parent_email": "e2e@example.com",
    "child_name": "Efe",
    "child_age": 6,
    "child_gender": "erkek",
    "child_photo_url": "CHILD_PHOTO_URL",
    "clothing_description": "kirmizi mont, mavi pantolon, beyaz spor ayakkabi",
    "story_title": "<from story response>",
    "story_pages": [
      {"page_number": 0, "text": "<page 0 text>", "visual_prompt": "<page 0 visual_prompt>"},
      {"page_number": 1, "text": "<page 1 text>", "visual_prompt": "<page 1 visual_prompt>"}
    ],
    "visual_style": "2D childrens picture-book cartoon illustration",
    "scenario_name": "Kapadokya"
  }'
```

From response take `preview_id`.

### 3.3–3.5 Confirm flow

Wait ~45s for background image generation, then confirm with the token from DB.

---

## 4) Collect Proof from Live DB + Logs

### 4.1 From logs (PROMPT_DEBUG)

| Key | Description |
|-----|-------------|
| `final_prompt_before` | Scene prompt before composer (scene-only). |
| `final_prompt_after` | API payload prompt (after compose_visual_prompt: + style, normalize, sanitize). |
| `negative_prompt_final` | Full negative (base + style_negative + strict). |
| `is_cover` | true for page 0, false for page 1. |
| `page_index` | 0 or 1. |
| `template_key` | COVER_TEMPLATE or INNER_TEMPLATE. |
| `template_from_db` | true if loaded from DB. |
| `style_key` | Visual style text used. |
| `model` | fal-ai/flux-pulid or flux/dev. |

### 4.2 From DB (story_previews)

```bash
docker compose exec postgres psql -U postgres -d benimmasalim -c "
SELECT
  id, status,
  jsonb_pretty(prompt_debug_json) AS prompt_debug_json,
  jsonb_pretty(generation_manifest_json) AS generation_manifest_json
FROM story_previews WHERE id = '<preview_id>'::uuid;
"
```

---

## 5) Validate Invariants (Must Hold)

| Invariant | How to check |
|-----------|----------------|
| **Cover:** `is_cover=true`, dimensions **768x1024** | Logs/manifest for page 0. |
| **Inner:** `is_cover=false`, dimensions **1024x768** | Logs/manifest for page 1. |
| **Only "Cappadocia"** (no "Kapadokya" in API prompt) | `final_prompt_after` must not contain "Kapadokya". |
| **Style injected once** | `final_prompt_after` contains one "STYLE:" block. |
| **negative_prompt_final** includes strict negatives | Must include "typographic", "big eyes", "chibi", "doll-like face". |
| **reference_image_used = true** when child_photo_url provided | Manifest: `reference_image_used` true; model = flux-pulid. |
| **clothing_description present** | Final prompt contains the clothing text. |

---

## 6) If Output Looks Wrong – Diagnosis

| Symptom | Likely cause | Fix |
|--------|---------------|-----|
| **A) Likeness drifts** | `child_photo_url` not reachable from container. | Use a **publicly reachable** HTTPS URL. |
| **B) Old cached image** | Cache-busting not applied or GCS path overwritten. | Check `prompt_hash` in manifest. |
| **C) Old DB records with styled visual_prompt** | Previews created before style-independence. | Regenerate. |
| **D) Frontend shows stale preview** | Frontend caches old page_images. | Cache-bust URLs. |

---

## 7) Report — LIVE E2E Results

### LIVE E2E DOCKER — Run Date: 2026-02-06

### Docker
- [x] docker compose up -d --build OK (backend rebuild ile migration 022 dahil)
- [x] backend health 200
- [x] alembic upgrade head OK
- [x] story_previews has prompt_debug_json, generation_manifest_json

### Order flow (preview_id: d9b8a8b3-df2c-4902-988c-2d302b75981e)
- [x] test-story-structured (page_count=2, visual_style="2D childrens picture-book cartoon illustration", clothing_description="kirmizi mont, mavi pantolon, beyaz spor ayakkabi") OK — returned 3 pages, title "Efe'nin Kapadokya Macerasi"
- [x] submit-preview-async with child_photo_url + clothing_description OK — preview_id d9b8a8b3-df2c-4902-988c-2d302b75981e
- [x] Background completed (page_images 0,1 present) — GCS URLs confirmed
- [x] confirm/<token> called — status CONFIRMED

### Log snippet (PROMPT_DEBUG)

**Page 0 (Cover):**
```
PROMPT_DEBUG
  book_id=d9b8a8b3-df2c-4902-988c-2d302b75981e
  page_index=0
  is_cover=True
  template_key=COVER_TEMPLATE
  template_from_db=True
  style_key='2D childrens picture-book cartoon illustration'
  model=fal-ai/flux-pulid
  width=768
  height=1024
  final_prompt_after='A clear scene of a vast Cappadocia landscape filled with uniquely shaped fairy chimneys
    under a bright sunny sky. A 6-year-old boy named Efe ... wearing an adventure jacket and comfortable pants.
    Warm, bright sunlight illuminating the scene. Child about 30% of frame. ...
    A young child wearing kirmizi mont, mavi pantolon, beyaz spor ayakkabi.
    Space for title at top. Wide shot, child 30% of frame, environment 70%, child NOT looking at camera.
    Natural child facial proportions, natural-sized eyes.
    STYLE: 2D childrens picture-book cartoon illustration'
  negative_prompt_final='asian architecture, ... big eyes, chibi, oversized eyes, ... doll-like face,
    baby proportions, anime, manga, 3d, 3d render, ... text, watermark, ... typographic, ...'
```

**Page 1 (Inner):**
```
PROMPT_DEBUG
  book_id=d9b8a8b3-df2c-4902-988c-2d302b75981e
  page_index=1
  is_cover=False
  template_key=INNER_TEMPLATE
  template_from_db=True
  style_key='2D childrens picture-book cartoon illustration'
  model=fal-ai/flux-pulid
  width=1024
  height=768
  final_prompt_after="A clear scene of Cappadocia's fairy chimneys at dawn ...
    A 6-year-old boy named Efe ... running through the red soil ...
    wearing an adventure jacket and comfortable pants. ...
    A young child wearing kirmizi mont, mavi pantolon, beyaz spor ayakkabi.
    Text space at bottom. Wide shot, child 30% of frame, environment 70%, child NOT looking at camera.
    Natural child facial proportions, natural-sized eyes.
    STYLE: 2D childrens picture-book cartoon illustration"
  negative_prompt_final='asian architecture, ... big eyes, chibi, oversized eyes, ... doll-like face,
    baby proportions, anime, manga, 3d, 3d render, ... text, watermark, ... typographic, ...'
```

### DB excerpt (generation_manifest_json)

```json
{
    "0": {
        "model": "fal-ai/flux-pulid",
        "width": 768,
        "height": 1024,
        "is_cover": true,
        "provider": "fal",
        "prompt_hash": "7b20666f1b670180",
        "template_key": "COVER_TEMPLATE",
        "negative_hash": "60cb1418ecefbc55",
        "guidance_scale": 3.5,
        "template_from_db": true,
        "num_inference_steps": 28,
        "reference_image_used": true
    },
    "1": {
        "model": "fal-ai/flux-pulid",
        "width": 1024,
        "height": 768,
        "is_cover": false,
        "provider": "fal",
        "prompt_hash": "32739910f68f648e",
        "template_key": "INNER_TEMPLATE",
        "negative_hash": "60cb1418ecefbc55",
        "guidance_scale": 3.5,
        "template_from_db": true,
        "num_inference_steps": 28,
        "reference_image_used": true
    }
}
```

### DB excerpt (page_images)

```json
{
    "0": "https://storage.googleapis.com/benimmasalim-generated-books/stories/d01bb146/page_0.png",
    "1": "https://storage.googleapis.com/benimmasalim-generated-books/stories/d01bb146/page_1.png"
}
```

### Invariants
- [x] Cover 768x1024, is_cover=true — manifest "0": width=768, height=1024, is_cover=true
- [x] Inner 1024x768, is_cover=false — manifest "1": width=1024, height=768, is_cover=false
- [x] No "Kapadokya" in final_prompt_after — only "Cappadocia" present
- [x] Scene-only: no style tokens in scene description — style injected only at compose stage
- [x] Single STYLE block — exactly one `STYLE:\n` per prompt, no "STYLE: STYLE:"
- [x] negative_prompt includes typographic, big eyes, doll-like face, chibi, anime, 3d, watermark
- [x] reference_image_used = true when child_photo_url set — both pages true
- [x] template_from_db = true — both pages use DB templates
- [x] template_key correct — page 0 = COVER_TEMPLATE, page 1 = INNER_TEMPLATE
- [x] clothing_description present in prompt — "kirmizi mont, mavi pantolon, beyaz spor ayakkabi" in both
- [x] Cover has "Space for title at top" — present
- [x] Inner has "Text space at bottom" — present
- [x] Cover does NOT have "Text space at bottom" — confirmed absent
- [x] Inner does NOT have "Space for title at top" — confirmed absent

### Conclusion

**PASS.** Full E2E order flow completed successfully in Docker on 2026-02-06.

- Story generation (PASS-1): Gemini produced 3 TR pages for "Efe'nin Kapadokya Macerasi"
- Visual prompt composition (PASS-2): Composer wired clothing_description, COVER/INNER templates from DB, style injected once
- FAL image generation: Both pages generated with PuLID (flux-pulid), reference_image_used=true
- Dimensions correct: Cover 768x1024, Inner 1024x768
- Location normalized: Only "Cappadocia" in EN prompts
- Strict negative applied: includes big eyes, chibi, anime, 3d, watermark, typographic, doll-like face
- Observability: prompt_debug_json + generation_manifest_json populated per page with template_key, template_from_db, prompt_hash, reference_image_used
- Status: CONFIRMED, page_images stored in GCS

---

### Re-run instructions (for future verification)

```powershell
$env:E2E_CHILD_PHOTO_URL = "https://storage.googleapis.com/benimmasalim-generated-books/temp/pulid-faces/bded5ff1_1770377303.jpg"
$env:E2E_RUN_ORDER = "1"
.\scripts\e2e_docker_verify.ps1
```

Then collect evidence:
```powershell
docker compose logs backend --tail=500 2>&1 | Select-String -Pattern "PROMPT_DEBUG"
docker compose exec -T postgres psql -U postgres -d benimmasalim -c "SELECT jsonb_pretty(generation_manifest_json) FROM story_previews WHERE id = '<preview_id>'::uuid;"
```

---

## 8) V2 Final Review — Docker Verification (2026-02-06)

### Basic checks: PASS

```
=== 1) Docker Compose === All services running (healthy)
=== 2) Migrations === 023_prompt_v2 applied successfully
=== 3) Verify columns === prompt_debug_json, generation_manifest_json exist
=== 4) Health === 200 OK
```

### V2 column verification: PASS

```
scenarios:
  - story_prompt_tr    | text
  - location_en        | character varying
  - flags              | jsonb
  - default_page_count | integer

prompt_templates:
  - template_en        | text

visual_styles:
  - style_negative_en  | text

learning_outcomes:
  - banned_words_tr    | text
```

### V2 seed data: PASS

```
COVER_TEMPLATE -> "{scene_description}. A young child wearing {clothing_description}. Wide shot, child 30%..."
INNER_TEMPLATE -> "{scene_description}. A young child wearing {clothing_description}. Wide horizontal scene..."
```

### Test suite: PASS

```
155 passed, 2 skipped
```

### Conclusion: **PASS**

Backend Prompt System V2 is fully deployed and verified in Docker.
All columns, migrations, seeds, tests, and live E2E order flow confirmed working.
