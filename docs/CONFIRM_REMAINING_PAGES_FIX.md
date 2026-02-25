# Confirm Order – Remaining Pages Fix

## A) Call chain

### User flow
1. **Create page** (`frontend/src/app/create/page.tsx`): Step 9 shows 3 preview images (cover + page 1 + 2). Step 10 = Sipariş; user submits via `handleSubmitOrder` → `POST /api/v1/orders/submit-preview-async`.
2. **Backend** (`backend/app/api/v1/orders.py`): `submit_preview_async` saves `StoryPreview` with `status=PROCESSING`, `page_images=initial_page_images` (only first 3 if uploaded), then `background_tasks.add_task(process_preview_background, ...)` and returns immediately.
3. **Background** `process_preview_background`: Uses `request_data["story_pages"]` (all pages; only 0,1,2 have `image_base64`). For each page: if `image_base64` → use it; else call FAL to generate. Then compose, upload to GCS, set `preview.page_images`, `preview.status = "PENDING"`, send email with confirm link.
4. **User** clicks link in email → **Confirm page** (`frontend/src/app/confirm/[token]/page.tsx`) → `GET /api/v1/orders/confirm/{token}`.
5. **Backend** `confirm_order`: Sets `preview.status = "CONFIRMED"`, `preview.confirmed_at`, commits. **Previously did not trigger any further generation.**

### Admin
- **List**: `GET /api/v1/admin/orders/previews-test` → `page_images: _page_images_for_preview(p)` (from `StoryPreview.page_images`).
- **Detail**: `GET /api/v1/admin/orders/previews-test/{id}` → same. Polling every 15s only when `status === "PROCESSING"`.

---

## B) Root cause

1. **Confirm does not trigger generation**  
   `GET /confirm/{token}` only updates status and timestamp. If the first background run never finished (server restart, timeout, partial failure), the preview can be confirmed with only 3 (or 0) images. Nothing was started to generate the rest.

2. **Single-shot background task**  
   `process_preview_background` runs once after submit. If the process is restarted or the task fails partway, remaining pages are never generated and no retry or “complete remaining” path existed.

3. **Admin stops polling after PENDING**  
   Polling was only for `status === "PROCESSING"`. After confirm, status is `CONFIRMED`; if we later add a task to fill remaining pages, the admin UI would not refresh until the user manually reloaded.

---

## C) Minimal patch (implemented)

### 1. Confirm triggers “remaining pages” when incomplete
- **File**: `backend/app/api/v1/orders.py`
- **Change**: `confirm_order` now:
  - Injects `BackgroundTasks` and logs `CONFIRM_START`, `CONFIRM_PREVIEW_FOUND` (with `page_count`, `page_images_count`), `CONFIRM_DONE`.
  - After setting `CONFIRMED` and committing, if `len(preview.page_images) < len(preview.story_pages)`:
    - Logs `CONFIRM_TRIGGER_REMAINING_PAGES` with `missing` count.
    - Calls `background_tasks.add_task(process_remaining_pages, str(preview.id))`.

### 2. New task: `process_remaining_pages(preview_id)`
- **File**: `backend/app/api/v1/orders.py`
- **Behavior**:
  - Opens its own DB session, loads `StoryPreview` by `preview_id`.
  - Builds `story_pages` from `preview.story_pages`; for each page that already has an image in `preview.page_images`, downloads the URL to base64 and sets `image_base64` on that page.
  - For pages without `image_base64`, calls FAL (same as main pipeline), then composes with templates, uploads to GCS.
  - Merges new uploads with existing `preview.page_images`, commits. Does **not** send email again.
- **Logging**: `REMAINING_PAGES_START`, `REMAINING_PAGES_USE_EXISTING`, `REMAINING_PAGES_GENERATE`, `REMAINING_PAGES_GENERATED`, `REMAINING_PAGES_GENERATE_FAILED`, `REMAINING_PAGES_ALL_FAILED`, `REMAINING_PAGES_UPLOAD_FAILED`, `REMAINING_PAGES_DONE`, `REMAINING_PAGES_ERROR`.

### 3. Admin polling for CONFIRMED + incomplete
- **File**: `frontend/src/app/admin/orders/page.tsx`
- **Change**: The 15s polling runs not only when `detailData.status === "PROCESSING"` but also when `detailData.status === "CONFIRMED"` and `page_images` count is less than `page_count`. So when “remaining pages” finish, the open detail view refreshes without manual reload.

---

## D) Flow after fix

1. User submits → background runs; if it completes, all pages are in `page_images` and email is sent.
2. User confirms → if `page_images` is still incomplete, `process_remaining_pages` is scheduled and runs in the background.
3. Admin viewing that preview (CONFIRMED, incomplete) keeps polling every 15s until `page_images` count matches `page_count`, so new images appear automatically.

---

## E) Optional follow-ups

- **Persistent queue**: Move long-running generation to a queue (e.g. Celery/Redis) so tasks survive restarts.
- **Idempotent remaining-pages**: If `process_remaining_pages` is called multiple times (e.g. double confirm), it is safe: it only generates pages that still lack images and merges into `page_images`.
