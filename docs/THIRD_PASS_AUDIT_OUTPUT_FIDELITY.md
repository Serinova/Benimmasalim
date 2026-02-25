# Third-Pass Audit: Output Fidelity

**Focus:** Output fidelity (not only prompts). Prompt drift already addressed via sanitizer + tests; this audit checks UI↔backend consistency, reference conditioning, rendering parameters, and adds a generation manifest.

---

## A) UI Caching / ID Mapping

### Findings

- **Source of truth:** Admin UI gets image URLs from `GET /admin/orders/previews/{id}` → `_page_images_for_preview(preview)` → `preview.page_images` (then fallback to `preview_images`). So the UI always shows what is stored in the DB for that preview.
- **Key convention:** Backend stores `page_images` with **string** keys (`"0"`, `"1"`, …). Admin and frontend use `page_images[idx.toString()]` and `page_images["page_" + idx]`; backend uses `str(k)` when writing. Mapping is consistent.
- **After confirm:** `process_preview_background` and `process_remaining_pages` both merge new uploads into `preview.page_images` and commit. The next admin load returns the updated `page_images`; no separate “preview” cache that could show old images.
- **Cache risk:** Image URLs are plain GCS URLs. If the same object path is overwritten (e.g. re-run), CDN or browser cache can serve the old image. There is no cache-busting query param (`?v=...`) on the URLs we store or serve.

### Conclusion

- No bug found where UI shows a cached preview instead of the latest DB-backed URLs.
- **Recommendation (optional):** When serving or displaying images (e.g. admin proxy), append a version/updated timestamp as query param to avoid stale cache after re-generation.

---

## B) Reference Conditioning (PuLID / Identity)

### Findings

- **Single reference for all pages:** In both `process_preview_background` and `process_remaining_pages`, `child_photo_url` is taken from `request_data.get("child_photo_url")` or `getattr(preview, "child_photo_url", None)` and passed as `child_face_url=child_photo_url or ""` to `generate_consistent_image` for every page (cover and inner). So the **same** reference URL is used for cover and inner pages in a given run.
- **Missing reference:** If `child_photo_url` is missing, we log `"child_photo_url missing, PuLID disabled for remaining pages"` and pass `child_face_url=""`. FAL then uses `FLUX_DEV` (no face). So there is **no silent** fallback that “looks like” PuLID is on but drops the reference; we log and behaviour is explicit.
- **Cover vs inner:** No code path uses a different reference for cover vs inner; both use the same `child_photo_url` / `child_face_url`.

### Conclusion

- No reference conditioning mismatch between cover and inner pages.
- No silent disable of reference conditioning; missing ref is logged and results in non-PuLID model.

---

## C) Rendering Parameters (Cover vs Inner)

### Findings

- **Before fix:** Orders used `width=1024`, `height=768` for **all** pages, including the cover. So the cover was generated in **landscape** (1024×768), while the intended cover aspect is portrait (e.g. 768×1024), and `generate_cover` in `fal_ai_service` defaults to 768×1024. That could cause aspect/letterbox mismatch and style difference when composed with a portrait template.
- **After fix:** In `orders.py` (both `process_preview_background` and `process_remaining_pages`):
  - Cover (page_num == 0): `width=768`, `height=1024`
  - Inner pages: `width=1024`, `height=768`
- **Upscaler / refiner:** The main FAL path used by orders does not run an upscaler or refiner after generation. Separate upscale exists in `fal_service.py` for other flows.
- **Enhance / provider defaults:** No “enhance” flag or extra provider default that would change look in the orders FAL path. Same `GenerationConfig` (steps, guidance) for cover and inner.

### Conclusion

- **Parameter difference (cover vs inner) was present and is fixed:** cover now uses 768×1024, inner 1024×768.
- No other rendering parameter differences (upscale/refiner/enhance) in the orders pipeline.

---

## D) Patch Plan (Minimal)

| Item | Status | Notes |
|------|--------|--------|
| **Cover vs inner dimensions** | **Done** | Orders now pass `(768, 1024)` for page_num==0 and `(1024, 768)` for inner pages in both background and remaining-pages flows. |
| **Generation manifest per page** | **Done** | New `generation_manifest_json` on `StoryPreview` stores per page: `provider`, `model`, `num_inference_steps`, `guidance_scale`, `width`, `height`, `is_cover`, `prompt_hash`, `negative_hash`, `reference_image_used`. Persisted in both `process_preview_background` and `process_remaining_pages`. Admin preview detail API returns `generation_manifest_json` for dump/compare. |
| **Optional: cache-bust image URLs** | Not done | If needed, add `?v=<updated_ts>` (or similar) when serving image URLs so UI does not show stale content after re-generation. |

---

## Generation Manifest Schema (DB)

Stored in `StoryPreview.generation_manifest_json` as `{"0": {...}, "1": {...}}`. Each value:

- `provider`: `"fal"`
- `model`: e.g. `"fal-ai/flux-pulid"`
- `num_inference_steps`, `guidance_scale`: from config
- `width`, `height`, `is_cover`: actual values used
- `prompt_hash`, `negative_hash`: first 16 chars of SHA256 of final prompt/negative
- `reference_image_used`: boolean

Use this to confirm that cover and inner pages used the same model, size, and reference in a given run.

---

## Reproduce / Verify

1. Run one order: create preview, confirm so that cover + page 1 are generated.
2. In DB or via admin API, read `preview.page_images` and `preview.generation_manifest_json`.
3. Confirm:
   - `page_images["0"]` and `page_images["1"]` are the GCS URLs from the **current** run (no old URLs).
   - Manifest for `"0"`: `is_cover: true`, `width: 768`, `height: 1024`, `reference_image_used` as expected.
   - Manifest for `"1"`: `is_cover: false`, `width: 1024`, `height: 768`; same `model` and `reference_image_used` as page 0.
4. In admin UI, open that preview and confirm the displayed images match the URLs in `page_images` (and that manifest in API matches DB).

After applying migration `022_add_generation_manifest_json_to_story_preview`, new runs will populate manifests; re-run one order and dump manifests as above.
