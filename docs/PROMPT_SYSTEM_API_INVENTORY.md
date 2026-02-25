# Prompt System — API Endpoint Inventory (Phase 0)

**Scope:** All `/api/v1` routes involved in (a) story generation PASS-1, (b) visual prompt / image generation PASS-2, (c) preview submit/confirm flow.  
**Base URL:** `/api/v1` (mounted in `app/main.py`).

---

## 1) Story generation (PASS-1)

### POST /api/v1/ai/test-story-structured
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `test_structured_story_generation` (~606–832) |
| **Request (prompt-related)** | `TestStructuredStoryRequest`: `child_name`, `child_age`, `child_gender`, `child_photo_url`, `scenario_id`, `scenario_name`, `scenario_prompt`, `learning_outcomes`, `visual_style`, `page_count`, `custom_variables` |
| **Response** | `story.title`, `story.pages` (each: `page_number`, `text`, `visual_prompt`). `metadata.scenario_name`, `metadata.visual_style`. |
| **Call chain** | `GeminiService.generate_story_structured()` → Pass1 (Pure Author) + Pass2 (Technical Director) → `_compose_visual_prompts()` → scene-only `visual_prompt` per page. Then in controller: `compose_visual_prompt()` per page for response (Cappadocia + style). |

### POST /api/v1/ai/test-story
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `test_story_generation` (~559–604) |
| **Request** | `TestStoryRequest`: `child_name`, `child_age`, `scenario` (single string). |
| **Response** | `story` (plain text), `child_name`, `scenario`. No visual prompts. |
| **Call chain** | Direct Gemini `generateContent` (single prompt string). No prompt composition layer. |

### POST /api/v1/ai/generate-story
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `generate_story` (~1392–1429) |
| **Request** | `GenerateStoryRequest`: `order_id`. |
| **Response** | `GenerateStoryResponse`: `story_text`, `status`. |
| **Call chain** | Placeholder only (TODO). Loads `Order` by id; returns fixed placeholder text. No prompt system used. |

### POST /api/v1/trials/create
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/trials.py` → `create_trial` (~92–~313) |
| **Request** | `CreateTrialRequest`: `user_id`, `scenario_id`, `scenario_name`, `child_name`, `child_age`, `child_gender`, `learning_outcomes`, `visual_style`, `visual_style_name`, `product_id`, etc. |
| **Response** | `TrialResponse`: `trial_id`, `status`, etc. |
| **Call chain** | `GeminiService.generate_story_structured()` (same as test-story-structured) → `_compose_visual_prompts()` → `story_pages` with `visual_prompt`; then background generates 3 images via FAL. |

---

## 2) Visual prompt / image generation (PASS-2)

### POST /api/v1/ai/test-image-fal
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `test_fal_image_generation` (~327–389) |
| **Request** | `TestFalImageRequest`: `prompt`, `style`, `face_photo_url`, `clothing`, `id_weight`, `width`, `height`. |
| **Response** | `image_url`, `provider`, `face_consistency`. |
| **Call chain** | `get_fal_service()` → `FalAIService.generate_consistent_image(prompt, style_modifier=request.style, ...)` → `_build_full_prompt()` (scene) → `compose_visual_prompt()` (style + normalize + sanitize) → FAL API; returns `(url, out)` with `final_prompt`, `negative_prompt`. |

### POST /api/v1/ai/test-image
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `test_image_generation` (~1171–1229) |
| **Request** | `TestImageRequest`: `prompt`, `style`, `page_width_mm`, `page_height_mm`, `bleed_mm`, `product_id`. |
| **Response** | Image bytes (PNG) or JSON error. |
| **Call chain** | `compose_visual_prompt(f"{request.prompt}, {request.style}", ...)` → Gemini Imagen 3 `predict`. |

### POST /api/v1/ai/test-image-flash
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `test_image_generation_flash` (~1231–~1339) |
| **Request** | `TestImageRequest`: same as test-image. |
| **Response** | Image bytes or JSON with `image_base64`, `provider`. |
| **Call chain** | Resolution from product/template or request → `GeminiImageService` (or modular generator) → `compose_visual_prompt()` used inside gemini_image_service. |

### POST /api/v1/ai/test-image-modular
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `test_image_modular` (~1339–1391) |
| **Request** | `TestImageRequest`; query `provider` (gemini_flash / gemini / fal). |
| **Response** | Image bytes (PNG) or JSON error. |
| **Call chain** | `get_image_generator(provider)` → `ImageGenerator.generate(prompt, style_prompt, ...)` (strategy pattern). FAL path uses own prompt build; Gemini path may use composer. |

### POST /api/v1/ai/generate-cover
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `generate_cover` (~1432–1458) |
| **Request** | `GenerateCoverRequest`: `order_id`. |
| **Response** | `GenerateCoverResponse`: `cover_url`, `status`. |
| **Call chain** | Placeholder (TODO). No real prompt/image generation. |

### POST /api/v1/ai/orders/{order_id}/regenerate-cover
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/ai.py` → `regenerate_cover` (~1461–1495) |
| **Request** | Path `order_id`. |
| **Response** | `RegenerateCoverResponse`: `cover_url`, `regenerate_count`, `remaining`. |
| **Call chain** | Placeholder (TODO). Increments `cover_regenerate_count`. |

---

## 3) Preview submit / confirm flow

### POST /api/v1/orders/send-preview
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/orders.py` → `send_preview_email` (~84–~310) |
| **Request** | `SendPreviewRequest`: `parent_name`, `parent_email`, `child_name`, `child_age`, `child_gender`, `story_title`, `story_pages` (each: `page_number`, `text`, `visual_prompt`, `image_base64`), `scenario_name`, `visual_style_name`, `learning_outcomes`, product/audio fields. |
| **Response** | `preview_id`, `confirmation_token`, `message`. |
| **Call chain** | Saves `StoryPreview` with `story_pages` (visual_prompt as provided). Composes pages with templates; uploads images; sends email. No prompt composition in this path (uses client-supplied prompts). |

### POST /api/v1/orders/submit-preview-async
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/orders.py` → `submit_preview_async` (~321–~455) |
| **Request** | `AsyncPreviewRequest`: same as send-preview plus `child_photo_url`, `visual_style`, `id_weight`. |
| **Response** | `preview_id`, `confirmation_token`, `message`. |
| **Call chain** | Saves `StoryPreview` with `story_pages` (visual_prompt from request). Starts background task `process_preview_background`: for each page without image, `FalAIService.generate_consistent_image(prompt=page["visual_prompt"], style_modifier=visual_style, ...)` → FAL returns `(url, {manifest, final_prompt, negative_prompt})` → `prompt_debug_collector` / `generation_manifest_collector` → writes `preview.prompt_debug_json`, `preview.generation_manifest_json`, updates `preview.story_pages` with composed `visual_prompt`. |

### GET /api/v1/orders/confirm/{token}
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/orders.py` → `confirm_order` (~997–1091) |
| **Request** | Path `token`. |
| **Response** | `success`, `message`, `preview_id`, `child_name`, `story_title`; or `already_confirmed` / `expired`. |
| **Call chain** | Load `StoryPreview` by `confirmation_token`; set `status=CONFIRMED`; if missing page images, `background_tasks.add_task(process_remaining_pages, preview.id)`. No prompt built here; `process_remaining_pages` uses same FAL + composer + prompt_debug/manifest write as background above. |

---

## 4) Admin — previews and orders (read/regenerate)

### GET /api/v1/admin/orders/previews
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/admin/orders.py` → `list_story_previews` (~219–259) |
| **Request** | Query `status` (optional). |
| **Response** | List of previews: `id`, `status`, `story_title`, `page_count`, `page_images`, etc. No per-page prompts in list. |

### GET /api/v1/admin/orders/previews/{preview_id}
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/admin/orders.py` → `get_preview_detail` (~261–314) |
| **Request** | Path `preview_id`. |
| **Response** | Full preview: `story_pages` (with `visual_prompt` from `_story_pages_for_display(preview)` = composed/debug prompt), `page_images`, `generation_manifest_json`, etc. |
| **Call chain** | `_story_pages_for_display()` → `get_display_visual_prompt()` per page (uses `prompt_debug_json.final_prompt` or `compose_visual_prompt()`). |

### GET /api/v1/admin/orders/previews-test/{preview_id}
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/admin/orders.py` → `get_preview_detail_test` (~135–177) |
| **Request** | Path `preview_id`. |
| **Response** | Same shape as get_preview_detail; includes `story_pages`, `generation_manifest_json`. |

### POST /api/v1/admin/orders/{order_id}/regenerate-page
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/admin/orders.py` → `regenerate_page` (~1217–1238) |
| **Request** | Path `order_id`, query `page_number`. |
| **Response** | `order_id`, `page_number`, `status: "regenerating"`. |
| **Call chain** | TODO placeholder. No prompt/image call yet. |

---

## 5) Trials (preview + complete)

### GET /api/v1/trials/{trial_id}/preview
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/trials.py` → `get_trial_preview` (~339–381) |
| **Request** | Path `trial_id`. |
| **Response** | `PreviewResponse`: trial info + `story_pages` (text, visual_prompt). |
| **Call chain** | Load trial; return stored `story_pages` (visual_prompt from Gemini + _compose_visual_prompts). |

### POST /api/v1/trials/complete
| Field | Value |
|-------|--------|
| **Controller** | `app/api/v1/trials.py` → `complete_trial` (~382–~544) |
| **Request** | Body with trial completion data. |
| **Response** | `TrialResponse`. |
| **Call chain** | Can trigger further generation; uses stored prompts / FAL as needed. |

---

## Summary table

| Category | Endpoints |
|----------|-----------|
| **PASS-1 (story)** | `POST /ai/test-story-structured`, `POST /ai/test-story`, `POST /ai/generate-story`, `POST /trials/create` |
| **PASS-2 (image/prompt)** | `POST /ai/test-image-fal`, `POST /ai/test-image`, `POST /ai/test-image-flash`, `POST /ai/test-image-modular`, `POST /ai/generate-cover`, `POST /ai/orders/{id}/regenerate-cover` |
| **Preview flow** | `POST /orders/send-preview`, `POST /orders/submit-preview-async`, `GET /orders/confirm/{token}` |
| **Admin** | `GET /admin/orders/previews`, `GET /admin/orders/previews/{id}`, `GET /admin/orders/previews-test/{id}`, `POST /admin/orders/{id}/regenerate-page` |
| **Trials** | `GET /trials/{id}/preview`, `POST /trials/complete` |
