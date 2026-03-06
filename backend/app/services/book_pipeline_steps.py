"""Book generation pipeline helper steps (audio, back cover, dedication pages)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx
import structlog
from sqlalchemy import select

from app.services.storage_service import StorageService
from app.utils.resolution_calc import (
    A4_LANDSCAPE_HEIGHT_MM,
    A4_LANDSCAPE_WIDTH_MM,
    calculate_generation_params_from_mm,
    get_effective_generation_params,
    resize_image_bytes_to_target,
)

if TYPE_CHECKING:
    from app.models.book_template import PageTemplate
    from app.models.order import Order
    from app.prompt import BookContext

logger = structlog.get_logger()


async def pipeline_step_audio(
    *,
    db: object,
    order: "Order",
    generated_pages: list[dict],
    storage: StorageService,
    order_id: str,
) -> str | None:
    """Pipeline Step 5: Generate audio book if selected.

    Returns:
        Signed QR URL for the audio file, or None.
    """
    if not order.has_audio_book:
        return None

    try:
        from app.services.ai.elevenlabs_service import ElevenLabsService

        full_story_text = "".join(
            page["text"] + "\n\n" for page in generated_pages if page.get("text")
        )
        if not full_story_text.strip():
            return None

        elevenlabs = ElevenLabsService()
        logger.info(
            "Generating audio book",
            order_id=order_id,
            audio_type=order.audio_type,
            text_length=len(full_story_text),
        )

        if order.audio_type == "cloned" and order.audio_voice_id:
            audio_bytes = await elevenlabs.text_to_speech(
                text=full_story_text, voice_id=order.audio_voice_id
            )
        else:
            audio_bytes = await elevenlabs.text_to_speech(
                text=full_story_text, voice_type="female"
            )

        audio_url = storage.upload_audio(
            audio_bytes=audio_bytes, order_id=str(order.id), filename="audiobook.mp3"
        )
        order.audio_file_url = audio_url
        await db.commit()

        audio_qr_url = storage.get_signed_url(audio_url, expiration_hours=24 * 365)
        logger.info(
            "Audio book generated",
            order_id=order_id,
            audio_url=audio_url,
            audio_size=len(audio_bytes),
        )
        return audio_qr_url

    except Exception as e:
        logger.error("Audio generation failed", order_id=order_id, error=str(e))
        return None


async def pipeline_step_back_cover_config(db: object) -> object | None:
    """Pipeline Step 7: Fetch active back cover config.

    Returns:
        Active BackCoverConfig instance or None.
    """
    try:
        from app.models.book_template import BackCoverConfig

        result = await db.execute(
            select(BackCoverConfig)
            .where(BackCoverConfig.is_default == True)  # noqa: E712
            .where(BackCoverConfig.is_active == True)  # noqa: E712
        )
        cfg = result.scalar_one_or_none()
        if cfg:
            logger.info("Using back cover config", config_name=cfg.name)
        return cfg

    except Exception as e:
        logger.warning("Failed to get back cover config", error=str(e))
        return None


async def pipeline_step_dedication_pages(
    *,
    db: object,
    order: "Order",
    story_title: str,
    scenario: object | None,
    order_id: str,
) -> tuple[str | None, str | None]:
    """Pipeline Steps 8 + 8b: Compose dedication and intro pages.

    Returns:
        (dedication_base64, intro_base64)
    """
    from app.models.book_template import PageTemplate
    from app.services.page_composer import PageComposer, build_template_config
    from app.services.scenario_content_service import generate_scenario_intro_text

    dedication_base64: str | None = None
    intro_base64: str | None = None

    # Step 8: dedication page
    child_name: str = getattr(order, "child_name", None) or "Sevgili"
    ded_note = getattr(order, "dedication_note", None)
    if not ded_note:
        for _sp in getattr(order, "story_pages", None) or []:
            if (
                isinstance(_sp, dict)
                and _sp.get("page_type") == "front_matter"
                and (_sp.get("text") or "").strip()
            ):
                ded_note = _sp["text"].strip()
                break

    # Always generate a dedication page — use fallback if no custom note
    if not ded_note:
        ded_note = f"Bu kitap {child_name} için özel olarak hazırlanmıştır."

    try:
        ded_tpl_result = await db.execute(
            select(PageTemplate)
            .where(PageTemplate.page_type == "dedication")
            .where(PageTemplate.is_active == True)  # noqa: E712
            .limit(1)
        )
        ded_tpl = ded_tpl_result.scalar_one_or_none()
        ded_cfg = build_template_config(ded_tpl) if ded_tpl else {}
        dedication_base64 = await asyncio.to_thread(
            PageComposer().compose_dedication_page,
            text=ded_note,
            template_config=ded_cfg,
            dpi=300,
        )
        if dedication_base64:
            logger.info("Dedication page composed for PDF", order_id=order_id)
    except Exception as e:
        logger.warning("Dedication compose failed", order_id=order_id, error=str(e))

    # Step 8b: scenario intro page
    try:
        intro_text = await generate_scenario_intro_text(
            scenario=scenario,
            child_name=order.child_name,
            story_title=story_title,
        )
        if intro_text:
            intro_tpl_result = await db.execute(
                select(PageTemplate)
                .where(PageTemplate.page_type == "dedication")
                .where(PageTemplate.is_active == True)  # noqa: E712
                .limit(1)
            )
            intro_tpl = intro_tpl_result.scalar_one_or_none()
            intro_cfg = build_template_config(intro_tpl) if intro_tpl else {}
            intro_base64 = await asyncio.to_thread(
                PageComposer().compose_dedication_page,
                text=intro_text,
                template_config=intro_cfg,
                dpi=300,
            )
            if intro_base64:
                logger.info("Scenario intro page composed for PDF", order_id=order_id)
    except Exception as e:
        logger.warning("Scenario intro page failed", order_id=order_id, error=str(e))

    return dedication_base64, intro_base64


async def generate_back_cover_image(
    *,
    order: "Order",
    book_ctx: "BookContext",
    image_provider: object,
    storage: StorageService,
    cover_template: "PageTemplate | None",
    inner_template: "PageTemplate | None",
    clothing_description: str,
    style_modifier: str,
    face_ref_url: str | None,
    original_photo_url: str = "",
    face_embedding: object,
    true_cfg_override: float | None,
    start_step_override: int | None,
    num_inference_steps_override: int | None,
    guidance_scale_override: float | None,
    leading_prefix_override: str | None,
    style_block_override: str | None,
) -> str | None:
    """Generate the back cover image (same atmosphere as front, no title).

    Returns:
        GCS URL of the uploaded back cover image, or None on failure.
    """
    from app.prompt.cover_builder import build_back_cover_prompt

    _scenario_name = book_ctx.scenario_name or "magical adventure"
    _location = book_ctx.location_name or "enchanted land"
    back_scene = (
        f"Wide panoramic view of {_location}. "
        f"The same young {book_ctx.child_gender or 'child'} seen from behind or side, "
        f"gazing into the distance of the {_scenario_name} world. "
        f"Continuation of the front cover atmosphere — same lighting, same environment, same mood."
    )

    back_prompt = build_back_cover_prompt(ctx=book_ctx, scene_description=back_scene)

    current_template = cover_template or inner_template
    if current_template:
        params = get_effective_generation_params(current_template)
    else:
        params = calculate_generation_params_from_mm(
            A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
        )

    width, height = params["generation_width"], params["generation_height"]

    result = await image_provider.generate_consistent_image(
        prompt=back_prompt,
        child_face_url=face_ref_url,
        clothing_prompt=clothing_description,
        style_modifier=style_modifier,
        width=width,
        height=height,
        id_weight=book_ctx.style.id_weight,
        true_cfg_override=true_cfg_override,
        start_step_override=start_step_override,
        num_inference_steps_override=num_inference_steps_override,
        guidance_scale_override=guidance_scale_override,
        is_cover=False,
        template_en=None,
        story_title="",
        child_gender=(order.child_gender or "").strip(),
        child_age=order.child_age or 7,
        style_negative_en="",
        base_negative_en="",
        leading_prefix_override=leading_prefix_override,
        style_block_override=style_block_override,
        skip_compose=False,
        precomposed_negative="",
        reference_embedding=face_embedding,
        original_photo_url=original_photo_url,
    )
    image_url = result[0] if isinstance(result, tuple) else result

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        image_bytes = resp.content

    # Upscale back cover image for print quality
    _needs_upscale = params.get("needs_upscale", False)
    _upscale_factor = params.get("upscale_factor", 1)
    if _needs_upscale and _upscale_factor > 1:
        from app.services.upscale_service import upscale_image_bytes_safe

        image_bytes = await upscale_image_bytes_safe(
            image_bytes, upscale_factor=_upscale_factor
        )

    try:
        image_bytes = resize_image_bytes_to_target(
            image_bytes,
            params["target_width"],
            params["target_height"],
        )
    except Exception:
        pass

    final_url = await storage.upload_generated_image(
        image_bytes,
        str(order.id),
        page_number=9999,  # sentinel page number for back cover
    )
    return final_url
