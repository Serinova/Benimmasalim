"""Preview display helpers — formatting, prompt enrichment, pipeline version detection.

These functions were extracted from app.api.v1.admin.orders to keep the router thin.
All public symbols are importable by admin routes and tests.
"""

from typing import Any

import structlog

from app.models.story_preview import StoryPreview

logger = structlog.get_logger()


def page_images_for_preview(preview: StoryPreview) -> dict | None:
    """Return page_images if populated, otherwise fall back to preview_images (GCS URLs)."""
    if preview.page_images and len(preview.page_images) > 0:
        return preview.page_images
    if preview.preview_images and len(preview.preview_images) > 0:
        return preview.preview_images
    return None


def append_cache_bust(url: str, version: str) -> str:
    """Append ?v= or &v= to avoid breaking signed URLs that already carry a query string."""
    if not url or not version:
        return url
    sep = "&v=" if "?" in url else "?v="
    return url + sep + version


def detect_pipeline_version(preview: StoryPreview) -> str:
    """Detect pipeline version from strongest signal to weakest."""
    cache = getattr(preview, "generated_prompts_cache", None) or {}
    if cache.get("pipeline_version") == "v3":
        return "v3"
    if cache.get("blueprint_json"):
        return "v3"
    cache_prompts = cache.get("prompts") if isinstance(cache, dict) else None
    if isinstance(cache_prompts, list):
        for p in cache_prompts:
            if not isinstance(p, dict):
                continue
            if (
                p.get("pipeline_version") == "v3"
                or p.get("composer_version") == "v3"
                or p.get("v3_composed")
            ):
                return "v3"
    raw_pages = preview.story_pages or []
    for p in raw_pages:
        if not isinstance(p, dict):
            continue
        if (
            p.get("pipeline_version") == "v3"
            or p.get("composer_version") == "v3"
            or p.get("v3_composed")
        ):
            return "v3"
    logger.error(
        "V2_LABEL_BLOCKED: expected v3",
        route="/api/v1/admin/orders/previews/{preview_id}",
        preview_id=str(getattr(preview, "id", "")),
        reason="missing_v3_markers",
    )
    return "v3"


def story_pages_for_display(preview: StoryPreview) -> list[dict]:
    """Return story pages with user-visible visual_prompt (display-safe; never internal Turkish names)."""
    from app.prompt_engine import get_display_visual_prompt

    raw = preview.story_pages or []
    style = getattr(preview, "visual_style_name", None) or ""
    debug = getattr(preview, "prompt_debug_json", None) or {}
    out = []
    for p in raw:
        if not isinstance(p, dict):
            out.append({"text": str(p), "visual_prompt": "", "page_number": len(out)})
            continue
        page_num = p.get("page_number", len(out))
        display_prompt = get_display_visual_prompt(
            p.get("visual_prompt", ""),
            page_num,
            style,
            debug,
        )
        out.append({**p, "visual_prompt": display_prompt})
    return out


def enrich_manifest_with_prompts(preview: StoryPreview) -> dict | None:
    """Inject final_prompt / negative_prompt into each manifest entry from prompt_debug or story_pages."""
    manifest = getattr(preview, "generation_manifest_json", None) or {}
    prompt_debug = getattr(preview, "prompt_debug_json", None) or {}
    raw_pages = preview.story_pages or []
    if not manifest:
        return manifest
    enriched: dict[str, Any] = {}
    for k, m in manifest.items():
        if not isinstance(m, dict):
            enriched[str(k)] = m
            continue
        entry = dict(m)
        key_str = str(k)
        pd = prompt_debug.get(key_str) or prompt_debug.get(k)
        if not entry.get("final_prompt") and pd:
            if isinstance(pd, dict):
                if pd.get("final_prompt"):
                    entry["final_prompt"] = pd["final_prompt"]
                if pd.get("negative_prompt"):
                    entry["negative_prompt"] = pd["negative_prompt"]
        if not entry.get("final_prompt"):
            try:
                idx = int(k)
            except (ValueError, TypeError):
                idx = -1
            if 0 <= idx < len(raw_pages):
                p = raw_pages[idx]
                if isinstance(p, dict) and p.get("visual_prompt"):
                    entry["final_prompt"] = p["visual_prompt"]
        enriched[key_str] = entry
    return enriched


def page_images_with_cache_bust(preview: StoryPreview) -> dict | None:
    """Return page_images dict with cache-bust param: ?v=prompt_hash or ?v=updated_at."""
    raw = page_images_for_preview(preview)
    if not raw:
        return None
    manifest = getattr(preview, "generation_manifest_json", None) or {}
    updated_at = getattr(preview, "updated_at", None)
    updated_ts = updated_at.isoformat() if updated_at else ""
    out: dict[str, Any] = {}
    for k, v in raw.items():
        if not isinstance(v, str):
            out[str(k)] = v
            continue
        if v.startswith("data:"):
            out[str(k)] = v
            continue
        page_manifest = manifest.get(str(k)) if isinstance(manifest, dict) else {}
        ver = (
            page_manifest.get("prompt_hash") if isinstance(page_manifest, dict) else None
        ) or updated_ts
        out[str(k)] = append_cache_bust(v, ver) if ver else v
    return out


def extract_pdf_url(preview: StoryPreview) -> str | None:
    """Extract PDF URL from generation_manifest_json or admin_notes fallback."""
    manifest = getattr(preview, "generation_manifest_json", None) or {}
    if isinstance(manifest, dict) and manifest.get("final_pdf_url"):
        return manifest["final_pdf_url"]
    notes = getattr(preview, "admin_notes", None) or ""
    for line in notes.splitlines():
        line = line.strip()
        if line.startswith("PDF URL:"):
            url = line[len("PDF URL:"):].strip()
            if url:
                return url
    return None


def build_prompts_by_page(preview: StoryPreview) -> dict[str, dict]:
    """Per-page prompt data with metadata — keyed by page_number string.

    Returns dict[page_number_str, {final_prompt, negative_prompt, page_type,
    page_index, story_page_number, composer_version, pipeline_version}].
    """
    from app.prompt_engine.constants import NEGATIVE_PROMPT, STRICT_NEGATIVE_ADDITIONS

    prompt_debug = getattr(preview, "prompt_debug_json", None) or {}
    cache = getattr(preview, "generated_prompts_cache", None) or {}
    cache_prompts = cache.get("prompts") if isinstance(cache, dict) else None
    cache_by_page: dict[str, dict] = {}
    if isinstance(cache_prompts, list):
        for cp in cache_prompts:
            if not isinstance(cp, dict):
                continue
            cp_key = str(cp.get("page_number", len(cache_by_page)))
            cache_by_page[cp_key] = cp
    raw_pages = preview.story_pages or []
    _fallback_neg = f"{NEGATIVE_PROMPT} {STRICT_NEGATIVE_ADDITIONS}".strip()

    out: dict[str, dict] = {}
    for i, page in enumerate(raw_pages):
        if not isinstance(page, dict):
            continue

        page_num = page.get("page_number", i)
        key = str(page_num)

        pd = prompt_debug.get(key) or prompt_debug.get(str(page_num)) or prompt_debug.get(page_num)
        final_p = ""
        neg_p = ""
        if isinstance(pd, dict):
            final_p = pd.get("final_prompt") or ""
            neg_p = pd.get("negative_prompt") or ""

        if not final_p:
            final_p = page.get("visual_prompt", "")
        if not neg_p:
            neg_p = page.get("negative_prompt", "") or (_fallback_neg if final_p else "")

        cp = cache_by_page.get(key) or {}
        composer_ver = page.get("composer_version", "") or cp.get("composer_version", "")
        page_v3 = page.get("v3_composed", False) or bool(cp.get("v3_composed"))
        page_pipeline = page.get("pipeline_version", "") or cp.get("pipeline_version", "")

        if page_pipeline == "v3" or composer_ver == "v3" or page_v3:
            pipeline_ver = "v3"
        else:
            logger.error(
                "V2_LABEL_BLOCKED: expected v3",
                route="/api/v1/admin/orders/previews/{preview_id}",
                preview_id=str(getattr(preview, "id", "")),
                page_number=page_num,
                page_pipeline=page_pipeline or None,
                composer_version=composer_ver or None,
            )
            pipeline_ver = "v3"

        if final_p or neg_p:
            out[key] = {
                "final_prompt": final_p,
                "negative_prompt": neg_p,
                "pipeline_version": pipeline_ver,
                "composer_version": composer_ver or pipeline_ver,
                "page_type": page.get("page_type", "inner"),
                "page_index": page.get("page_index", i),
                "story_page_number": page.get("story_page_number"),
            }
    return out
