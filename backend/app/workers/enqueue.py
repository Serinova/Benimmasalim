"""
Helper to enqueue Arq jobs from the API layer.

Usage:
    from app.workers.enqueue import enqueue_preview_generation

    await enqueue_preview_generation(preview_id, story_id, token, data)
"""

import asyncio

import structlog
from arq.connections import ArqRedis, create_pool

from app.workers.image_worker import get_redis_settings

logger = structlog.get_logger()

# Module-level pool (lazy-init, guarded by lock)
_pool: ArqRedis | None = None
_pool_lock = asyncio.Lock()


async def _get_pool() -> ArqRedis:
    """Get or create the Arq Redis connection pool (thread-safe)."""
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is None:
            _pool = await create_pool(
                get_redis_settings(),
                default_queue_name="benimmasalim:image_gen",
            )
    return _pool


async def enqueue_preview_generation(
    preview_id: str,
    story_id: str,
    confirmation_token: str,
    request_data: dict,
) -> str | None:
    """
    Enqueue a preview image generation job.

    Returns the Arq job ID if successful, None if enqueueing fails
    (in which case the caller should fall back to BackgroundTasks).
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_preview_images",
            preview_id=preview_id,
            story_id=story_id,
            confirmation_token=confirmation_token,
            request_data=request_data,
        )
        if job:
            logger.info(
                "Job enqueued via Arq",
                job_id=job.job_id,
                preview_id=preview_id,
                function="generate_preview_images",
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed, will fall back to BackgroundTasks",
            error=str(e),
            preview_id=preview_id,
        )
        return None


async def enqueue_remaining_pages(preview_id: str) -> str | None:
    """
    Enqueue a remaining-pages generation job.

    Returns the Arq job ID if successful, None if enqueueing fails.
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_remaining_pages",
            preview_id=preview_id,
        )
        if job:
            logger.info(
                "Job enqueued via Arq",
                job_id=job.job_id,
                preview_id=preview_id,
                function="generate_remaining_pages",
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed, will fall back to BackgroundTasks",
            error=str(e),
            preview_id=preview_id,
        )
        return None


async def enqueue_trial_story(
    trial_id: str,
    request_data: dict,
) -> str | None:
    """Enqueue story generation (Gemini) for a trial.

    The worker generates the story and then enqueues preview image generation.
    Returns the Arq job ID if successful, None on failure.
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_trial_story",
            trial_id=trial_id,
            request_data=request_data,
        )
        if job:
            logger.info(
                "Trial story job enqueued via Arq",
                job_id=job.job_id,
                trial_id=trial_id,
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed for trial story generation",
            error=str(e),
            trial_id=trial_id,
        )
        return None


async def enqueue_trial_preview(
    trial_id: str,
    prompts: list[dict],
    child_photo_url: str | None,
    visual_style: str | None,
    product_name: str | None = None,
    story_title: str = "",
    clothing_description: str = "",
    visual_style_name: str | None = None,
) -> str | None:
    """
    Enqueue a trial preview image generation job (3 images).

    Returns the Arq job ID if successful, None if enqueueing fails
    (caller should fall back to BackgroundTasks).
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_trial_preview",
            trial_id=trial_id,
            prompts=prompts,
            child_photo_url=child_photo_url,
            visual_style=visual_style,
            product_name=product_name,
            story_title=story_title,
            clothing_description=clothing_description,
            visual_style_name=visual_style_name,
        )
        if job:
            logger.info(
                "Trial preview job enqueued via Arq",
                job_id=job.job_id,
                trial_id=trial_id,
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed for trial preview, falling back to BackgroundTasks",
            error=str(e),
            trial_id=trial_id,
        )
        return None


async def enqueue_trial_remaining(
    trial_id: str,
    prompts: list[dict],
    product_name: str | None = None,
    visual_style_modifier: str = "",
    child_photo_url: str = "",
    clothing_description: str = "",
) -> str | None:
    """
    Enqueue a trial remaining-pages generation job (~13 images).

    Returns the Arq job ID if successful, None if enqueueing fails.
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_trial_remaining",
            trial_id=trial_id,
            prompts=prompts,
            product_name=product_name,
            visual_style_modifier=visual_style_modifier,
            child_photo_url=child_photo_url,
            clothing_description=clothing_description,
        )
        if job:
            logger.info(
                "Trial remaining job enqueued via Arq",
                job_id=job.job_id,
                trial_id=trial_id,
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed for trial remaining, falling back to BackgroundTasks",
            error=str(e),
            trial_id=trial_id,
        )
        return None


async def enqueue_full_book_generation(order_id: str) -> str | None:
    """
    Enqueue a full book generation job (all pages + PDF) for a paid order.

    Returns the Arq job ID if successful, None if enqueueing fails.
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_full_book_task",
            order_id=order_id,
        )
        if job:
            logger.info(
                "Full book generation job enqueued via Arq",
                job_id=job.job_id,
                order_id=order_id,
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed for full book generation",
            error=str(e),
            order_id=order_id,
        )
        return None


async def enqueue_trial_composed_preview(
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
) -> str | None:
    """
    Enqueue a composed trial preview image generation job (3 images + text overlay).

    Returns the Arq job ID if successful, None if enqueueing fails.
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(
            "generate_trial_composed_preview",
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
        if job:
            logger.info(
                "Trial composed preview job enqueued via Arq",
                job_id=job.job_id,
                trial_id=trial_id,
            )
            return job.job_id
        return None
    except Exception as e:
        logger.warning(
            "Arq enqueue failed for trial composed preview, falling back to BackgroundTasks",
            error=str(e),
            trial_id=trial_id,
        )
        return None


async def get_queue_depth() -> int:
    """Return the number of pending jobs in the Arq queue.

    Uses the cached module-level Redis pool to avoid creating a new
    connection on every call.
    """
    try:
        pool = await _get_pool()
        return int(await pool.zcard("benimmasalim:image_gen") or 0)
    except Exception:
        return 0


async def enqueue_job(function: str, *args, **kwargs) -> str | None:
    """
    Generic helper to enqueue an Arq job.
    Returns the job ID if successful, None otherwise.
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(function, *args, **kwargs)
        if job:
            logger.info(
                "Job enqueued via generic helper",
                job_id=job.job_id,
                function=function,
            )
            return job.job_id
        return None
    except Exception as e:
        logger.error("Failed to enqueue job via generic helper", error=str(e), function=function)
        return None
