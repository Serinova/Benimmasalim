# Patch Plan: Final Hardening (Cache Bust, Regression Test, Admin Debug, Reference Warning)

## 1) Cache busting

- **Backend:** `backend/app/api/v1/admin/orders.py`
  - `_append_cache_bust(url, version)`: appends `&v=` if URL already has `?`, else `?v=`. Safe for signed URLs.
  - `_page_images_with_cache_bust(preview)`: builds version from `generation_manifest_json[page_key].prompt_hash` or fallback `preview.updated_at.isoformat()`; skips non-strings and `data:` URLs.
  - All admin JSON responses that return `page_images` now use `_page_images_with_cache_bust()`:
    - List (test + auth), single preview detail (test + auth).
  - Proxy endpoint still uses raw `_page_images_for_preview()` for server-side fetch.

## 2) Regression test (cover portrait, inner landscape)

- **Source of truth:** `backend/app/core/image_dimensions.py`
  - `get_page_image_dimensions(page_num)`: returns `(768, 1024)` for `page_num == 0`, else `(1024, 768)`.
  - Constants: `COVER_WIDTH`, `COVER_HEIGHT`, `INNER_WIDTH`, `INNER_HEIGHT`.
- **Orders:** `backend/app/api/v1/orders.py` uses `get_page_image_dimensions(page_num)` in both `process_preview_background` and `process_remaining_pages` (replacing inline `(768,1024)` / `(1024,768)`).
- **Tests:** `backend/tests/test_image_dimensions.py`
  - `test_cover_is_portrait_768x1024`: page 0 → 768×1024.
  - `test_inner_pages_are_landscape_1024x768`: pages 1,2,3,10 → 1024×768.
  - `test_dimensions_swapped_fails`: cover ≠ inner and exact values; fails if someone swaps.

**Run:** `pytest tests/test_image_dimensions.py -v` (from backend with venv).

## 3) Admin debug panel

- **Frontend:** `frontend/src/app/admin/orders/page.tsx`
  - `StoryPreview` extended with `generation_manifest_json` (optional).
  - When `detailData.generation_manifest_json` exists, a collapsible **"Generation manifest (debug)"** section shows per page:
    - provider, model, num_inference_steps, guidance_scale, width, height, is_cover, prompt_hash, negative_hash, reference_image_used.
  - Rendered in a `<details>` block; pages sorted by index.

## 4) Reference missing warning

- **Frontend:** same page, in the detail card header (next to status badge).
  - If `generation_manifest_json` exists and any page has `reference_image_used === false`, a warning badge is shown: **"Referans yok"** (amber), with title "En az bir sayfada referans (PuLID) kullanılmadı".

---

## Files changed

| File | Change |
|------|--------|
| `backend/app/api/v1/admin/orders.py` | `_append_cache_bust`, `_page_images_with_cache_bust`; all client-facing `page_images` use cache-busted. |
| `backend/app/core/image_dimensions.py` | New: `get_page_image_dimensions`, constants. |
| `backend/app/api/v1/orders.py` | Import and use `get_page_image_dimensions(page_num)` in both generation loops. |
| `backend/tests/test_image_dimensions.py` | New: cover 768×1024, inner 1024×768, swap-fail tests. |
| `frontend/src/app/admin/orders/page.tsx` | `generation_manifest_json` on type; debug panel; "Referans yok" badge. |
| `docs/PATCH_PLAN_FINAL_HARDENING.md` | This patch plan. |

## Minimal checklist

- [x] Cache-bust: `?v=` / `&v=` from manifest or `updated_at`; signed-URL safe.
- [x] Regression test: cover 768×1024, inner 1024×768; test fails if swapped.
- [x] Admin: manifest (provider/model/steps/guidance/width/height/is_cover/hashes/reference_image_used) per page.
- [x] Admin: warning badge when any page has `reference_image_used === false`.
