"""
Arq worker for background image generation tasks.

Run with:
    arq app.workers.image_worker.WorkerSettings

This worker handles:
- generate_preview_images: Full preview generation (images + email)
- generate_remaining_pages: Complete missing pages after confirmation

Job state machine:
    QUEUED -> PROCESSING -> COMPOSING -> UPLOADING -> DONE / FAILED
"""

from typing import Any

import structlog
from arq.connections import RedisSettings

from app.config import settings

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Redis connection for Arq
# ---------------------------------------------------------------------------

def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into Arq RedisSettings (supports auth + TLS).

    Upstash Redis requires TLS and aggressively drops idle connections.
    We set generous retry/timeout values to handle transient disconnects.
    """
    from urllib.parse import urlparse

    url = str(settings.redis_url)
    parsed = urlparse(url)

    use_ssl = parsed.scheme == "rediss"
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password or None
    path_str = (parsed.path or "").strip("/")
    database = int(path_str) if path_str.isdigit() else 0

    return RedisSettings(
        host=host,
        port=port,
        password=password,
        database=database,
        ssl=use_ssl,
        ssl_cert_reqs="none",
        conn_timeout=60,
        conn_retries=20,
        conn_retry_delay=3,
    )


# ---------------------------------------------------------------------------
# Task: Generate preview images (background)
# ---------------------------------------------------------------------------

async def generate_preview_images(
    ctx: dict[str, Any],
    preview_id: str,
    story_id: str,
    confirmation_token: str,
    request_data: dict,
) -> dict[str, Any]:
    """
    Arq task: Generate images for a story preview and send confirmation email.
    Replaces process_preview_background from orders.py.
    """
    logger.info("ARQ_TASK_START: generate_preview_images", preview_id=preview_id)

    try:
        # Import here to avoid circular imports and ensure app context
        from app.services.preview_generation_service import process_preview_background_inner

        await process_preview_background_inner(
            preview_id=preview_id,
            story_id=story_id,
            confirmation_token=confirmation_token,
            request_data=request_data,
        )

        logger.info("ARQ_TASK_DONE: generate_preview_images", preview_id=preview_id)
        return {"status": "done", "preview_id": preview_id}

    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_preview_images",
            preview_id=preview_id,
            error=str(e),
        )
        raise  # Let Arq handle retry logic


# ---------------------------------------------------------------------------
# Task: Generate remaining pages
# ---------------------------------------------------------------------------

async def generate_remaining_pages(
    ctx: dict[str, Any],
    preview_id: str,
) -> dict[str, Any]:
    """
    Arq task: Generate missing pages for a confirmed preview.
    Replaces process_remaining_pages from orders.py.
    """
    logger.info("ARQ_TASK_START: generate_remaining_pages", preview_id=preview_id)

    try:
        from app.services.preview_generation_service import process_remaining_pages_inner

        await process_remaining_pages_inner(preview_id=preview_id)

        logger.info("ARQ_TASK_DONE: generate_remaining_pages", preview_id=preview_id)
        return {"status": "done", "preview_id": preview_id}

    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_remaining_pages",
            preview_id=preview_id,
            error=str(e),
        )
        raise


# ---------------------------------------------------------------------------
# Task: Generate admin PDF (background)
# ---------------------------------------------------------------------------

async def generate_admin_pdf_task(
    ctx: dict[str, Any],
    preview_id: str,
) -> dict[str, Any]:
    """Arq task: Generate PDF for admin in the background.
    
    Prevents locking up the main FastAPI event loop when admin requests a PDF.
    """
    logger.info("ARQ_TASK_START: generate_admin_pdf", preview_id=preview_id)
    try:
        from app.services.admin_pdf_service import generate_admin_pdf_inner

        pdf_url = await generate_admin_pdf_inner(preview_id)
        
        logger.info("ARQ_TASK_DONE: generate_admin_pdf", preview_id=preview_id, pdf_url=pdf_url)
        return {"status": "done", "preview_id": preview_id, "pdf_url": pdf_url}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_admin_pdf",
            preview_id=preview_id,
            error=str(e),
        )
        raise

# ---------------------------------------------------------------------------
# Task: Generate trial story (Gemini) + enqueue image generation
# ---------------------------------------------------------------------------

async def generate_trial_story(
    ctx: dict[str, Any],
    trial_id: str,
    request_data: dict,
) -> dict[str, Any]:
    """Arq task: Generate story via Gemini for a trial, then enqueue preview images.

    This moves the heavy Gemini API call out of the HTTP request handler so the
    /trials/create endpoint can return in < 1 s.
    """
    logger.info("ARQ_TASK_START: generate_trial_story", trial_id=trial_id)
    try:
        from app.services.trial_generation_service import generate_trial_story_inner

        await generate_trial_story_inner(trial_id=trial_id, request_data=request_data)

        logger.info("ARQ_TASK_DONE: generate_trial_story", trial_id=trial_id)
        return {"status": "done", "trial_id": trial_id}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_trial_story",
            trial_id=trial_id,
            error=str(e),
        )
        raise


# ---------------------------------------------------------------------------
# Task: Generate trial preview images (3 images, fast)
# ---------------------------------------------------------------------------

async def generate_trial_preview(
    ctx: dict[str, Any],
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    product_name: str | None = None,
    story_title: str = "",
    clothing_description: str = "",
    visual_style_name: str | None = None,
) -> dict[str, Any]:
    """Arq task: Generate 3 preview images for a trial."""
    logger.info("ARQ_TASK_START: generate_trial_preview", trial_id=trial_id)
    try:
        from app.services.trial_generation_service import generate_preview_images_inner

        await generate_preview_images_inner(
            trial_id=trial_id,
            prompts=prompts,
            child_photo_url=child_photo_url,
            visual_style=visual_style,
            product_name=product_name,
            story_title=story_title,
            clothing_description=clothing_description,
            visual_style_name=visual_style_name,
        )
        logger.info("ARQ_TASK_DONE: generate_trial_preview", trial_id=trial_id)
        return {"status": "done", "trial_id": trial_id}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_trial_preview",
            trial_id=trial_id,
            error=str(e),
        )
        raise


# ---------------------------------------------------------------------------
# Task: Generate trial remaining images (after payment)
# ---------------------------------------------------------------------------

async def generate_trial_remaining(
    ctx: dict[str, Any],
    trial_id: str,
    prompts: list[dict],
    product_name: str | None = None,
    visual_style_modifier: str = "",
    child_photo_url: str = "",
    clothing_description: str = "",
) -> dict[str, Any]:
    """Arq task: Generate remaining ~13 images for a completed trial."""
    logger.info("ARQ_TASK_START: generate_trial_remaining", trial_id=trial_id)
    try:
        from app.services.trial_generation_service import generate_remaining_images_inner

        await generate_remaining_images_inner(
            trial_id=trial_id,
            prompts=prompts,
            product_name=product_name,
            visual_style_modifier=visual_style_modifier,
            child_photo_url=child_photo_url,
            clothing_description=clothing_description,
        )
        logger.info("ARQ_TASK_DONE: generate_trial_remaining", trial_id=trial_id)
        return {"status": "done", "trial_id": trial_id}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_trial_remaining",
            trial_id=trial_id,
            error=str(e),
        )
        raise


# ---------------------------------------------------------------------------
# Task: Generate trial composed preview images (with text composition)
# ---------------------------------------------------------------------------

async def generate_trial_composed_preview(
    ctx: dict[str, Any],
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    visual_style_name: str | None = None,
    product_id: str | None = None,
    story_title: str = "",
    clothing_description: str | None = None,
    child_name: str = "",
    child_age: int = 7,
    child_gender: str | None = None,
    id_weight: float | None = None,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Arq task: Generate 3 composed preview images (with text overlay)."""
    logger.info("ARQ_TASK_START: generate_trial_composed_preview", trial_id=trial_id)
    try:
        from app.services.trial_generation_service import generate_composed_preview_inner

        await generate_composed_preview_inner(
            trial_id=trial_id,
            prompts=prompts,
            child_photo_url=child_photo_url,
            visual_style=visual_style,
            visual_style_name=visual_style_name,
            product_id=product_id,
            story_title=story_title,
            clothing_description=clothing_description,
            child_name=child_name,
            child_age=child_age,
            child_gender=child_gender,
            id_weight=id_weight,
            scenario_id=scenario_id,
        )
        logger.info("ARQ_TASK_DONE: generate_trial_composed_preview", trial_id=trial_id)
        return {"status": "done", "trial_id": trial_id}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_trial_composed_preview",
            trial_id=trial_id,
            error=str(e),
        )
        raise


# ---------------------------------------------------------------------------
# Task: Generate full book after payment (Order flow)
# ---------------------------------------------------------------------------

async def generate_full_book_task(
    ctx: dict[str, Any],
    order_id: str,
) -> dict[str, Any]:
    """Arq task: Generate all pages + PDF for a paid order."""
    logger.info("ARQ_TASK_START: generate_full_book", order_id=order_id)
    try:
        from app.tasks.generate_book import generate_full_book

        result = await generate_full_book(order_id=order_id)
        logger.info("ARQ_TASK_DONE: generate_full_book", order_id=order_id)
        return {"status": "done", "order_id": order_id, **result}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_full_book",
            order_id=order_id,
            error=str(e),
        )
        raise


# ---------------------------------------------------------------------------
# Task: Generate Trial Coloring Book
# ---------------------------------------------------------------------------

async def generate_coloring_book_for_trial(
    ctx: dict[str, Any],
    trial_id: str,
) -> dict[str, Any]:
    """Arq task: Generate coloring book for a trial."""
    logger.info("ARQ_TASK_START: generate_coloring_book_for_trial", trial_id=trial_id)
    try:
        from app.tasks.generate_coloring_book_for_trial import generate_coloring_book_for_trial as _gen_trial_cb
        from uuid import UUID
        from app.core.database import async_session_factory
        
        trial_uuid = trial_id if isinstance(trial_id, UUID) else UUID(trial_id)

        async with async_session_factory() as db:
            await _gen_trial_cb(trial_id=trial_uuid, db=db)
            
        logger.info("ARQ_TASK_DONE: generate_coloring_book_for_trial", trial_id=str(trial_id))
        return {"status": "done", "trial_id": str(trial_id)}
    except Exception as e:
        logger.error(
            "ARQ_TASK_FAILED: generate_coloring_book_for_trial",
            trial_id=trial_id,
            error=str(e),
        )
        raise

# ---------------------------------------------------------------------------
# Startup / Shutdown hooks
# ---------------------------------------------------------------------------

async def startup(ctx: dict[str, Any]) -> None:
    """Called when the worker starts."""
    logger.info("Arq image worker starting up")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Called when the worker shuts down."""
    logger.info("Arq image worker shutting down")


# ---------------------------------------------------------------------------
# Arq WorkerSettings
# ---------------------------------------------------------------------------

class WorkerSettings:
    """Arq worker configuration.

    Production Scaling (Cloud Run):
        Each worker instance runs up to max_jobs parallel tasks.
        With min 2 / max 5 instances and max_jobs=8, the system handles
        16-40 concurrent generation jobs.

        Scale up with:
            gcloud run services update benimmasalim-worker \
              --min-instances=2 --max-instances=5 \
              --region=europe-west1 --project=gen-lang-client-0784096400
    """

    # Task functions
    functions = [
        generate_preview_images,
        generate_remaining_pages,
        generate_admin_pdf_task,
        generate_trial_story,
        generate_trial_preview,
        generate_trial_remaining,
        generate_trial_composed_preview,
        generate_full_book_task,
        generate_coloring_book_for_trial,
    ]

    # Redis connection
    redis_settings = get_redis_settings()

    # Concurrency: Reduced to 8 to prevent overwhelming the Gemini API
    # and to ensure quality doesn't degrade under heavy burst load.
    # 8 jobs * 5 image_concurrency = 40 parallel generations per worker instance.
    max_jobs = 8

    # Job timeout: 30 minutes per job (pages may queue long on Fal.ai)
    job_timeout = 1800

    # Retry: 2 retries on failure (total 3 attempts)
    max_tries = 3

    # Health check interval — keep Redis alive (Upstash drops idle connections)
    health_check_interval = 10

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Queue name
    queue_name = "benimmasalim:image_gen"
