"""Background task: generate complete book after payment (Fal.ai + PuLID V3)."""

import asyncio

import httpx
import structlog
from sqlalchemy import select

from app.config import settings
from app.core.database import async_session_factory
from app.models.book_template import PageTemplate
from app.models.learning_outcome import LearningOutcome
from app.models.order import Order, OrderStatus
from app.models.order_page import OrderPage
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.visual_style import VisualStyle
from app.prompt import BookContext, PromptComposer
from app.services.ai.image_provider_dispatch import (
    get_effective_ai_config,
    get_image_provider_for_generation,
)
from app.services.order_state_machine import transition_order
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService
from app.utils.resolution_calc import (
    A4_LANDSCAPE_HEIGHT_MM,
    A4_LANDSCAPE_WIDTH_MM,
    calculate_generation_params_from_mm,
    get_effective_generation_params,
    resize_image_bytes_to_target,
)

logger = structlog.get_logger()


async def generate_full_book(order_id: str) -> dict:
    """
    Generate all pages and PDF for an order.

    This task is triggered after successful payment.

    Steps:
    1. Generate all page images (using existing cover)
    2. Apply overlays if needed
    3. Upscale images
    4. Generate PDF
    5. Generate audio if selected
    6. Update order status to READY_FOR_PRINT

    Args:
        order_id: UUID of the order

    Returns:
        Summary of generation
    """
    import time
    from uuid import UUID

    _start = time.monotonic()
    pdf_service = PDFService()
    storage = StorageService()

    async with async_session_factory() as db:
        # FOR UPDATE lock prevents two workers from picking up the same order simultaneously
        result = await db.execute(
            select(Order).where(Order.id == UUID(order_id)).with_for_update(skip_locked=True)
        )
        order = result.scalar_one_or_none()

        if not order:
            logger.warning(
                "Order not found or already locked by another worker — skipping",
                order_id=order_id,
            )
            return {"error": "Order not found or locked"}

        if order.status != OrderStatus.PAID:
            logger.error("Order not in PAID status", order_id=order_id, status=order.status)
            return {"error": "Order not in PAID status"}

        # Transition to PROCESSING (within the same locked transaction)
        await transition_order(order, OrderStatus.PROCESSING, db)

        # Get related data
        product = await db.get(Product, order.product_id)
        _scenario = await db.get(Scenario, order.scenario_id)  # Reserved for template usage
        style = await db.get(VisualStyle, order.visual_style_id)

        # Get page templates from product
        cover_template = None
        inner_template = None

        if product.cover_template_id:
            cover_template = await db.get(PageTemplate, product.cover_template_id)
        if product.inner_template_id:
            inner_template = await db.get(PageTemplate, product.inner_template_id)

        # Log template info (efektif parametre: şablon dikeyse yatay A4 kullanılır)
        if inner_template:
            params = get_effective_generation_params(inner_template)
            logger.info(
                "Using PageTemplate for generation (yatay A4 uyumlu)",
                inner_template_id=str(product.inner_template_id),
                target_size=f"{params['target_width']}x{params['target_height']}",
                generation_size=f"{params['generation_width']}x{params['generation_height']}",
                upscale_factor=params["upscale_factor"],
            )
        else:
            logger.warning(
                "No PageTemplate found, using defaults",
                product_id=str(product.id),
            )

        # Get learning outcomes
        outcomes = []
        for outcome_id in order.selected_outcomes:
            outcome = await db.get(LearningOutcome, UUID(outcome_id))
            if outcome:
                outcomes.append(outcome)

        # Get existing pages (story text already generated)
        pages_result = await db.execute(
            select(OrderPage).where(OrderPage.order_id == order.id).order_by(OrderPage.page_number)
        )
        existing_pages = list(pages_result.scalars().all())

        from app.core.pipeline_events import PipelineTracer, mask_photo_url

        tracer = PipelineTracer.for_order(
            order_id=order.id,
            user_id=order.user_id,
            product_id=order.product_id,
            requested_page_count=len(existing_pages),
        )
        tracer.pipeline_start(
            scenario_id=str(order.scenario_id) if order.scenario_id else "",
            style_id=str(order.visual_style_id) if order.visual_style_id else "",
            child_photo_hash=mask_photo_url(order.child_photo_url),
        )

        logger.info(
            "Starting book generation",
            trace_id=tracer.trace_id,
            order_id=order_id,
            existing_pages=len(existing_pages),
        )

        # ============================================================
        # APPEARANCE DETECTION (Face handled by PuLID from image)
        # ============================================================
        # PuLID extracts face identity from the photo.
        # We detect CLOTHING + HAIR for cross-page consistency.

        clothing_description = (getattr(order, "clothing_description", None) or "").strip()
        hair_description = (getattr(order, "hair_description", None) or "").strip()

        if clothing_description:
            logger.info(
                "Using stored clothing_description from order",
                order_id=order_id,
                clothing=clothing_description[:100],
            )
        elif order.child_photo_url:
            try:
                logger.info(
                    "Detecting appearance from child photo (PuLID will handle face)",
                    trace_id=tracer.trace_id,
                    order_id=order_id,
                    child_name=order.child_name,
                    child_photo_hash=mask_photo_url(order.child_photo_url),
                )

                import asyncio as _asyncio_detect
                clothing_description, hair_description = await _asyncio_detect.gather(
                    _detect_clothing_from_photo(
                        photo_url=order.child_photo_url,
                        gender=order.child_gender,
                    ),
                    _detect_hair_from_photo(
                        photo_url=order.child_photo_url,
                        gender=order.child_gender,
                    ),
                )

                logger.info(
                    "Appearance detected for character consistency",
                    order_id=order_id,
                    clothing=clothing_description[:100],
                    hair=hair_description[:60],
                )

            except Exception as e:
                logger.warning(
                    "Appearance detection failed, using defaults",
                    order_id=order_id,
                    error=str(e),
                )
                from app.prompt.templates import get_default_clothing, get_default_hair
                clothing_description = get_default_clothing("boy" if order.child_gender == "erkek" else "girl")
                hair_description = get_default_hair()
        else:
            logger.warning(
                "No child photo provided - PuLID face consistency unavailable",
                trace_id=tracer.trace_id,
                order_id=order_id,
            )
            from app.prompt.templates import get_default_clothing, get_default_hair
            clothing_description = get_default_clothing("boy" if order.child_gender == "erkek" else "girl")
            hair_description = get_default_hair()

        from app.services.ai.face_service import resolve_face_reference
        _face_ref_url, _face_embedding = await resolve_face_reference(
            order.child_photo_url or "", storage
        )

        # Character description: DB'den oku, yoksa on-the-fly üret
        # PuLID yüzü fotoğraftan alır; text description saç/ten/göz gibi özellikleri kilitler.
        character_description = (getattr(order, "face_description", None) or "").strip()
        if not character_description and _face_ref_url:
            try:
                from app.services.ai.face_analyzer_service import get_face_analyzer
                _face_analyzer = get_face_analyzer()
                character_description = await _face_analyzer.get_enhanced_child_description(
                    image_source=_face_ref_url,
                    child_name=order.child_name or "",
                    child_age=order.child_age or 7,
                    child_gender=order.child_gender or "",
                )
                # Sonraki kullanımlar için DB'ye kaydet
                order.face_description = character_description
                await db.commit()
                logger.info(
                    "CHARACTER_DESCRIPTION_GENERATED",
                    order_id=order_id,
                    desc_preview=character_description[:80],
                )
            except Exception as _e:
                logger.warning(
                    "Character description generation failed — face locked via PuLID only",
                    order_id=order_id,
                    error=str(_e),
                )

        # Personalize style
        style_modifier_raw = style.prompt_modifier if style else ""
        style_modifier = style_modifier_raw
        if order.child_name and "{child_name}" in style_modifier:
            style_modifier = style_modifier.replace("{child_name}", order.child_name)
        if "{child_age}" in style_modifier:
            style_modifier = style_modifier.replace("{child_age}", str(order.child_age or 7))

        ai_config = await get_effective_ai_config(db, product_id=order.product_id)
        provider_name = (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
        image_provider = get_image_provider_for_generation(provider_name)

        logger.info(
            "IMAGE_ENGINE_USED",
            provider=provider_name,
            model=getattr(ai_config, "image_model", "") if ai_config else "",
            order_id=order_id,
            scenario_id=str(order.scenario_id) if order.scenario_id else "",
            style_id=str(order.visual_style_id) if order.visual_style_id else "",
            page_count=len(existing_pages),
            source="generate_full_book",
        )

        # BookContext: kitap bazlı tüm parametreleri BİR KEZ çözümle
        from app.prompt import DEFAULT_COVER_TEMPLATE, DEFAULT_INNER_TEMPLATE
        from app.prompt.service import PromptService

        _prompt_svc = PromptService(db)
        cover_prompt_tpl = await _prompt_svc.get_en("COVER_TEMPLATE", fallback=DEFAULT_COVER_TEMPLATE)
        inner_prompt_tpl = await _prompt_svc.get_en("INNER_TEMPLATE", fallback=DEFAULT_INNER_TEMPLATE)
        _story_title = ""
        if _scenario and order.child_name:
            _story_title = f"{order.child_name}'in {_scenario.name}"
        elif order.child_name:
            _story_title = f"{order.child_name}'in Masalı"

        _id_weight_override = float(style.id_weight) if style and style.id_weight is not None else None
        _true_cfg_override = float(style.true_cfg) if style and getattr(style, "true_cfg", None) is not None else None
        _start_step_override = int(style.start_step) if style and getattr(style, "start_step", None) is not None else None
        _num_inference_steps_override = int(style.num_inference_steps) if style and getattr(style, "num_inference_steps", None) is not None else None
        _guidance_scale_override = float(style.guidance_scale) if style and getattr(style, "guidance_scale", None) is not None else None

        # Get style overrides from VisualStyle DB (before BookContext so they apply to prompts)
        _book_leading_prefix_override = (
            (style.leading_prefix_override or "").strip() if style else None
        ) or None
        _book_style_block_override = (
            (style.style_block_override or "").strip() if style else None
        ) or None

        book_ctx = BookContext.build(
            child_name=order.child_name or "",
            child_age=order.child_age or 7,
            child_gender=order.child_gender or "",
            style_modifier=style_modifier,
            character_description=character_description,
            clothing_description=clothing_description,
            hair_description=hair_description,
            face_reference_url=_face_ref_url,
            page_count=len(existing_pages),
            story_title=_story_title,
            scenario_name=_scenario.name if _scenario else "",
            location_name=getattr(_scenario, "location_en", "") if _scenario else "",
            id_weight_override=_id_weight_override,
            leading_prefix_override=_book_leading_prefix_override,
            style_block_override=_book_style_block_override,
        )
        prompt_composer = PromptComposer(
            book_ctx,
            cover_template=cover_prompt_tpl,
            inner_template=inner_prompt_tpl,
        )

        # Generate page images
        generated_pages = []

        # Separate cover (already generated) from pages needing generation
        pages_to_generate = []
        for page in existing_pages:
            if page.is_cover and page.image_url:
                # Front cover needs upscaling for print quality
                logger.info(
                    "Processing front cover for upscale",
                    order_id=order_id,
                    cover_url=page.image_url,
                )
                
                try:
                    # Download existing cover image
                    import httpx
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.get(page.image_url)
                        cover_img_bytes = resp.content
                    
                    # Get cover template params for target dimensions
                    if cover_template:
                        cover_params = get_effective_generation_params(cover_template)
                    else:
                        cover_params = calculate_generation_params_from_mm(
                            A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
                        )
                    
                    # Upscale if needed (same as inner pages)
                    _needs_upscale = cover_params.get("needs_upscale", False)
                    _upscale_factor = cover_params.get("upscale_factor", 1)
                    if _needs_upscale and _upscale_factor > 1:
                        from app.services.upscale_service import upscale_image_bytes_safe
                        _before_upscale_kb = len(cover_img_bytes) // 1024
                        cover_img_bytes = await upscale_image_bytes_safe(
                            cover_img_bytes,
                            upscale_factor=_upscale_factor,
                        )
                        logger.info(
                            "COVER_UPSCALE_APPLIED",
                            factor=_upscale_factor,
                            before_kb=_before_upscale_kb,
                            after_kb=len(cover_img_bytes) // 1024,
                        )
                    
                    # Resize to target print dimensions
                    try:
                        _before_resize = len(cover_img_bytes)
                        cover_img_bytes = resize_image_bytes_to_target(
                            cover_img_bytes,
                            cover_params["target_width"],
                            cover_params["target_height"],
                            is_cover=True,
                        )
                        logger.info(
                            "Cover resized to print target",
                            target=f"{cover_params['target_width']}x{cover_params['target_height']}",
                            before_kb=_before_resize // 1024,
                            after_kb=len(cover_img_bytes) // 1024,
                        )
                    except Exception as e:
                        logger.warning(
                            "Cover resize to target failed, using current size",
                            error=str(e),
                        )
                    
                    # Upload high-res version to GCS
                    highres_cover_url = await storage.upload_generated_image(
                        cover_img_bytes,
                        str(order.id),
                        page.page_number,
                    )
                    
                    generated_pages.append({
                        "text": _story_title or page.text_content or "",
                        "image_url": highres_cover_url,
                    })
                    
                    logger.info(
                        "Front cover upscaled and ready",
                        order_id=order_id,
                        highres_url=highres_cover_url,
                    )
                    
                except Exception as cover_err:
                    logger.error(
                        "Front cover upscale failed, using original",
                        order_id=order_id,
                        error=str(cover_err),
                    )
                    # Fallback: use original cover
                    generated_pages.append({
                        "text": _story_title or page.text_content or "",
                        "image_url": page.image_url,
                    })
            else:
                pages_to_generate.append(page)

        # Mark all pending pages as processing in one batch
        for page in pages_to_generate:
            page.image_generation_status = "processing"
        await db.commit()

        # Shared HTTP client for image downloads (reuse TCP connections)
        _download_client = httpx.AsyncClient(timeout=60.0)

        # Parallel image generation with concurrency limit
        _page_sem = asyncio.Semaphore(settings.image_concurrency)

        async def _generate_single_page(page: "OrderPage") -> tuple["OrderPage", str | None, str | None]:
            """Generate image for a single page. Returns (page, final_url, error)."""
            async with _page_sem:
                _img_start = time.monotonic()
                try:
                    scene_action = page.image_prompt or page.text_content or ""

                    if page.is_cover:
                        current_template = cover_template or inner_template
                    else:
                        current_template = inner_template

                    if current_template:
                        params = get_effective_generation_params(current_template)
                    else:
                        params = calculate_generation_params_from_mm(
                            A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
                        )
                    width, height = params["generation_width"], params["generation_height"]

                    tracer.image_gen_requested(
                        page=page.page_number,
                        provider=provider_name,
                        model=getattr(ai_config, "image_model", "") if ai_config else "",
                    )

                    logger.info(
                        "Generating page with PuLID face consistency",
                        trace_id=tracer.trace_id,
                        page=page.page_number,
                        scene_preview=scene_action[:80],
                        has_face_ref=bool(order.child_photo_url),
                    )

                    # V3 prompts are fully composed by enhance_all_pages() — re-composing
                    # would add a second style block and corrupt the prompt.
                    if getattr(page, "v3_composed", False) and scene_action:
                        _final_prompt_text = scene_action
                        _final_negative_text = page.negative_prompt or ""
                        logger.info(
                            "V3_composed page — using stored prompt directly",
                            page=page.page_number,
                            prompt_length=len(_final_prompt_text),
                        )
                    else:
                        if page.is_cover:
                            _pr = prompt_composer.compose_cover(scene_action)
                        else:
                            _pr = prompt_composer.compose_page(scene_action, page.page_number)
                        _final_prompt_text = _pr.prompt
                        _final_negative_text = _pr.negative_prompt

                    page_id_weight = book_ctx.style.id_weight

                    result = await image_provider.generate_consistent_image(
                        prompt=_final_prompt_text,
                        child_face_url=_face_ref_url,
                        clothing_prompt=clothing_description,
                        style_modifier=style_modifier,
                        width=width,
                        height=height,
                        id_weight=page_id_weight,
                        true_cfg_override=_true_cfg_override,
                        start_step_override=_start_step_override,
                        num_inference_steps_override=_num_inference_steps_override,
                        guidance_scale_override=_guidance_scale_override,
                        is_cover=page.is_cover,
                        template_en=None,
                        story_title=book_ctx.story_title if page.is_cover else "",
                        child_gender=(order.child_gender or "").strip(),
                        child_age=order.child_age or 7,
                        style_negative_en="",
                        base_negative_en="",
                        leading_prefix_override=_book_leading_prefix_override,
                        style_block_override=_book_style_block_override,
                        skip_compose=True,
                        precomposed_negative=_final_negative_text,
                        reference_embedding=_face_embedding,
                    )
                    image_url = result[0] if isinstance(result, tuple) else result

                    resp = await _download_client.get(image_url)
                    image_bytes = resp.content

                    # Upscale before resize — AI upscale (Real-ESRGAN) if enabled, else PIL fallback
                    _needs_upscale = params.get("needs_upscale", False)
                    _upscale_factor = params.get("upscale_factor", 1)
                    if _needs_upscale and _upscale_factor > 1:
                        from app.services.upscale_service import upscale_image_bytes_safe
                        _before_upscale_kb = len(image_bytes) // 1024
                        image_bytes = await upscale_image_bytes_safe(
                            image_bytes,
                            upscale_factor=_upscale_factor,
                        )
                        logger.info(
                            "UPSCALE_APPLIED",
                            page=page.page_number,
                            factor=_upscale_factor,
                            before_kb=_before_upscale_kb,
                            after_kb=len(image_bytes) // 1024,
                        )

                    try:
                        _before_resize = len(image_bytes)
                        image_bytes = resize_image_bytes_to_target(
                            image_bytes,
                            params["target_width"],
                            params["target_height"],
                        )
                        logger.info(
                            "Image resized to print target",
                            page=page.page_number,
                            target=f"{params['target_width']}x{params['target_height']}",
                            before_kb=_before_resize // 1024,
                            after_kb=len(image_bytes) // 1024,
                        )
                    except Exception as e:
                        logger.warning(
                            "Resize to target failed, using current size",
                            page=page.page_number,
                            error=str(e),
                        )

                    final_url = await storage.upload_generated_image(
                        image_bytes,
                        str(order.id),
                        page.page_number,
                    )

                    tracer.image_gen_ok(
                        page=page.page_number,
                        latency_ms=(time.monotonic() - _img_start) * 1000,
                        provider=provider_name,
                    )
                    logger.info(
                        "Page generated with PuLID",
                        trace_id=tracer.trace_id,
                        order_id=order_id,
                        page=page.page_number,
                        is_cover=page.is_cover,
                    )
                    return page, final_url, None

                except Exception as e:
                    tracer.image_gen_fail(
                        page=page.page_number,
                        error=str(e),
                        retry_count=page.generation_attempt,
                        provider=provider_name,
                    )
                    logger.error(
                        "Page generation failed",
                        trace_id=tracer.trace_id,
                        order_id=order_id,
                        page=page.page_number,
                        error=str(e),
                    )
                    return page, None, str(e)

        # Run all page generations in parallel
        if pages_to_generate:
            results = await asyncio.gather(
                *[_generate_single_page(p) for p in pages_to_generate],
                return_exceptions=True,
            )

            # Process results and update DB in batch
            for res in results:
                if isinstance(res, Exception):
                    logger.error("Unexpected page gen error", error=str(res))
                    continue
                page, final_url, _error = res
                if final_url:
                    page.image_url = final_url
                    page.image_generation_status = "completed"
                    generated_pages.append(
                        {
                            # Kapak sayfasında başlık kullan; iç sayfalarda text_content
                            "text": (_story_title if page.is_cover else page.text_content) or "",
                            "image_url": final_url,
                        }
                    )
                else:
                    page.image_generation_status = "failed"
                    page.generation_attempt += 1

            await db.commit()

        await _download_client.aclose()

        # Step 5: Generate audio if selected
        audio_qr_url = None
        if order.has_audio_book:
            try:
                from app.services.ai.elevenlabs_service import ElevenLabsService

                elevenlabs = ElevenLabsService()

                # Combine all page texts into one story
                full_story_text = ""
                for page in generated_pages:
                    if page.get("text"):
                        full_story_text += page["text"] + "\n\n"

                if full_story_text.strip():
                    logger.info(
                        "Generating audio book",
                        order_id=order_id,
                        audio_type=order.audio_type,
                        text_length=len(full_story_text),
                    )

                    # Generate audio using ElevenLabs
                    if order.audio_type == "cloned" and order.audio_voice_id:
                        # Use cloned voice
                        audio_bytes = await elevenlabs.text_to_speech(
                            text=full_story_text,
                            voice_id=order.audio_voice_id,
                        )
                    else:
                        # Use system voice (default female)
                        voice_type = "female"  # Could be stored in order if needed
                        audio_bytes = await elevenlabs.text_to_speech(
                            text=full_story_text,
                            voice_type=voice_type,
                        )

                    # Upload audio to GCS
                    audio_url = storage.upload_audio(
                        audio_bytes=audio_bytes,
                        order_id=str(order.id),
                        filename="audiobook.mp3",
                    )

                    order.audio_file_url = audio_url
                    await db.commit()

                    # Generate signed URL for QR code (valid for 1 year)
                    audio_qr_url = storage.get_signed_url(
                        audio_url,
                        expiration_hours=24 * 365,
                    )

                    logger.info(
                        "Audio book generated",
                        order_id=order_id,
                        audio_url=audio_url,
                        audio_size=len(audio_bytes),
                    )

            except Exception as e:
                logger.error(
                    "Audio generation failed",
                    order_id=order_id,
                    error=str(e),
                )
                # Don't fail the whole book generation if audio fails
                # Just log and continue

        # Step 6: Generate back cover image
        back_cover_image_url: str | None = None
        try:
            back_cover_image_url = await _generate_back_cover_image(
                order=order,
                book_ctx=book_ctx,
                image_provider=image_provider,
                storage=storage,
                cover_template=cover_template,
                inner_template=inner_template,
                clothing_description=clothing_description,
                style_modifier=style_modifier,
                face_ref_url=_face_ref_url,
                face_embedding=_face_embedding,
                true_cfg_override=_true_cfg_override,
                start_step_override=_start_step_override,
                num_inference_steps_override=_num_inference_steps_override,
                guidance_scale_override=_guidance_scale_override,
                leading_prefix_override=_book_leading_prefix_override,
                style_block_override=_book_style_block_override,
                provider_name=provider_name,
                ai_config=ai_config,
            )
            if back_cover_image_url:
                order.back_cover_image_url = back_cover_image_url
                await db.commit()
                logger.info("Back cover image generated", order_id=order_id, url=back_cover_image_url[:80])
        except Exception as e:
            logger.warning("Back cover image generation failed — continuing without it", order_id=order_id, error=str(e))

        # Step 7: Get back cover config
        back_cover_config = None
        try:
            from app.models.book_template import BackCoverConfig

            result = await db.execute(
                select(BackCoverConfig)
                .where(BackCoverConfig.is_default == True)
                .where(BackCoverConfig.is_active == True)
            )
            back_cover_config = result.scalar_one_or_none()
            if back_cover_config:
                logger.info("Using back cover config", config_name=back_cover_config.name)
        except Exception as e:
            logger.warning("Failed to get back cover config", error=str(e))

        # Step 8: Compose dedication page (karsilama sayfasi)
        dedication_image_base64: str | None = None
        ded_note = getattr(order, "dedication_note", None)
        if not ded_note:
            # Try AI-generated dedication text from story_pages
            for _sp in (getattr(order, "story_pages", None) or []):
                if isinstance(_sp, dict) and _sp.get("page_type") == "front_matter" and (_sp.get("text") or "").strip():
                    ded_note = _sp["text"].strip()
                    break
        if ded_note:
            try:
                from app.services.page_composer import PageComposer, build_template_config

                ded_composer = PageComposer()

                # Fetch dedication template
                ded_tpl_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == "dedication")
                    .where(PageTemplate.is_active == True)
                    .limit(1)
                )
                ded_tpl = ded_tpl_result.scalar_one_or_none()
                ded_cfg = build_template_config(ded_tpl) if ded_tpl else {}

                dedication_image_base64 = ded_composer.compose_dedication_page(
                    text=ded_note,
                    template_config=ded_cfg,
                    dpi=300,
                )
                if dedication_image_base64:
                    logger.info("Dedication page composed for PDF", order_id=order_id)
            except Exception as e:
                logger.warning("Dedication compose failed", order_id=order_id, error=str(e))

        # Step 8b: Generate "karşılama 2" — scenario intro text page
        intro_image_base64: str | None = None
        try:
            intro_text = await _generate_scenario_intro_text(
                scenario=_scenario,
                child_name=order.child_name,
                story_title=_story_title,
            )
            if intro_text:
                from app.services.page_composer import PageComposer, build_template_config

                _intro_composer = PageComposer()
                _intro_ded_tpl_result = await db.execute(
                    select(PageTemplate)
                    .where(PageTemplate.page_type == "dedication")
                    .where(PageTemplate.is_active == True)
                    .limit(1)
                )
                _intro_ded_tpl = _intro_ded_tpl_result.scalar_one_or_none()
                _intro_cfg = build_template_config(_intro_ded_tpl) if _intro_ded_tpl else {}
                intro_image_base64 = _intro_composer.compose_dedication_page(
                    text=intro_text,
                    template_config=_intro_cfg,
                    dpi=300,
                )
                if intro_image_base64:
                    logger.info("Scenario intro page (karşılama 2) composed for PDF", order_id=order_id)
        except Exception as e:
            logger.warning("Scenario intro page failed", order_id=order_id, error=str(e))

        # Step 9: Generate PDF
        try:
            pdf_bytes = await pdf_service.generate_book_pdf(
                order=order,
                product=product,
                pages=generated_pages,
                audio_qr_url=audio_qr_url,
                back_cover_config=back_cover_config,
                dedication_image_base64=dedication_image_base64,
                intro_image_base64=intro_image_base64,
                back_cover_image_url=back_cover_image_url,
            )

            # Upload PDF
            pdf_url = storage.upload_pdf(pdf_bytes=pdf_bytes, order_id=str(order.id))
            order.final_pdf_url = pdf_url

            # Transition to READY_FOR_PRINT
            await transition_order(order, OrderStatus.READY_FOR_PRINT, db)

            # Send "your book is ready" email to the customer
            try:
                from app.models.user import User
                from app.services.email_service import email_service

                _user = await db.get(User, order.user_id) if order.user_id else None
                _recipient_email = _user.email if _user and _user.email else None
                _recipient_name = _user.full_name if _user else None

                if _recipient_email:
                    await email_service.send_story_email_async(
                        recipient_email=_recipient_email,
                        recipient_name=_recipient_name or _recipient_email,
                        child_name=order.child_name,
                        story_title=f"{order.child_name}'in Masalı",
                        story_pages=[],
                    )
                    logger.info(
                        "ORDER_READY_EMAIL_SENT",
                        order_id=order_id,
                    )
                else:
                    logger.warning(
                        "ORDER_READY_EMAIL_SKIP_NO_EMAIL",
                        order_id=order_id,
                        user_id=str(order.user_id),
                    )
            except Exception as _mail_err:
                logger.warning(
                    "ORDER_READY_EMAIL_FAILED (order still completed)",
                    order_id=order_id,
                    error=str(_mail_err),
                )

            tracer.pipeline_complete(
                page_count=len(generated_pages),
            )

            duration_s = round(time.monotonic() - _start, 2)
            build_report = {
                "used_version": "v3",
                "order_id": order_id,
                "trace_id": tracer.trace_id,
                "page_count": len(generated_pages),
                "total_duration_seconds": duration_s,
                "pdf_url": pdf_url,
                "has_audio": order.has_audio_book,
                "image_provider": provider_name,
                "image_model": getattr(ai_config, "image_model", "") if ai_config else "",
            }
            logger.info("BUILD_REPORT", **build_report)

            return {
                "success": True,
                "order_id": order_id,
                "pages_generated": len(generated_pages),
                "pdf_url": pdf_url,
                "audio_url": order.audio_file_url if order.has_audio_book else None,
                "build_report": build_report,
            }

        except Exception as e:
            tracer.pipeline_fail(
                error_code="PDF_GENERATION_FAILED",
                error=str(e),
            )

            duration_s = round(time.monotonic() - _start, 2)
            build_report = {
                "used_version": "v3",
                "order_id": order_id,
                "trace_id": tracer.trace_id,
                "page_count": 0,
                "total_duration_seconds": duration_s,
                "error": str(e),
                "root_cause": "pdf_generation_failed",
            }
            logger.exception("BUILD_REPORT_FAIL", **build_report)
            return {"error": f"PDF generation failed: {str(e)}", "build_report": build_report}


async def _generate_back_cover_image(
    *,
    order: "Order",
    book_ctx: "BookContext",
    image_provider: object,
    storage: "StorageService",
    cover_template: "PageTemplate | None",
    inner_template: "PageTemplate | None",
    clothing_description: str,
    style_modifier: str,
    face_ref_url: str | None,
    face_embedding: object,
    true_cfg_override: float | None,
    start_step_override: int | None,
    num_inference_steps_override: int | None,
    guidance_scale_override: float | None,
    leading_prefix_override: str | None,
    style_block_override: str | None,
    provider_name: str,  # noqa: ARG001
    ai_config: object,  # noqa: ARG001
) -> str | None:
    """Generate the back cover image (same atmosphere as front, no title)."""
    from app.prompt.cover_builder import build_back_cover_prompt

    # Use the same scene description as the front cover but from a different angle
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
        from app.utils.resolution_calc import get_effective_generation_params
        params = get_effective_generation_params(current_template)
    else:
        from app.utils.resolution_calc import (
            A4_LANDSCAPE_HEIGHT_MM,
            A4_LANDSCAPE_WIDTH_MM,
            calculate_generation_params_from_mm,
        )
        params = calculate_generation_params_from_mm(A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM)

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
        image_bytes = await upscale_image_bytes_safe(image_bytes, upscale_factor=_upscale_factor)

    try:
        from app.utils.resolution_calc import resize_image_bytes_to_target
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


async def _detect_clothing_from_photo(photo_url: str, gender: str) -> str:
    """
    Detect clothing from child's photo using Gemini Vision.

    This is critical for outfit consistency across all pages.
    PuLID handles face, but clothing must be described in text.

    Args:
        photo_url: URL of child's photo
        gender: "erkek" or "kiz" for fallback

    Returns:
        Clothing description (e.g., "a red striped t-shirt and blue shorts")
    """
    import base64

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(photo_url)
            response.raise_for_status()
            image_bytes = response.content

        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        api_key = settings.gemini_api_key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": "image/jpeg", "data": base64_data}},
                        {
                            "text": """Analyze this child's photo and describe ONLY their clothing.

RULES:
- Describe what the child is WEARING (not face, not background)
- Be specific about colors and patterns
- Keep it concise (one phrase)

FORMAT: Respond with ONLY a clothing description that can complete:
"a child wearing ___"

EXAMPLES:
- "a bright red striped t-shirt and blue denim shorts"
- "a pink princess dress with sparkly details"
- "a yellow hoodie and gray sweatpants"

Just the clothing description, nothing else."""
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 100,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        clothing = result["candidates"][0]["content"]["parts"][0]["text"].strip()

        clothing = clothing.replace('"', "").replace("'", "")
        if clothing.lower().startswith("a child wearing "):
            clothing = clothing[16:]
        elif clothing.lower().startswith("wearing "):
            clothing = clothing[8:]

        logger.info("Clothing detected from photo", clothing=clothing[:50])
        return clothing

    except Exception as e:
        logger.warning("Clothing detection failed", error=str(e))
        from app.prompt.templates import get_default_clothing
        return get_default_clothing("boy" if gender == "erkek" else "girl")


async def _detect_hair_from_photo(photo_url: str, gender: str) -> str:  # noqa: ARG001
    """Detect hair style from child's photo for character consistency.

    Returns a short English phrase like "long curly dark brown hair".
    """
    import base64

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(photo_url)
            response.raise_for_status()
            image_bytes = response.content

        base64_data = base64.b64encode(image_bytes).decode("utf-8")

        api_key = settings.gemini_api_key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"inlineData": {"mimeType": "image/jpeg", "data": base64_data}},
                        {
                            "text": """Analyze this child's photo and describe ONLY their hair with maximum precision.

RULES:
- Describe hair LENGTH: very short (above ears), short (ear-length), medium (chin to shoulder), long (below shoulder), very long
- Describe hair TEXTURE: pin-straight, straight, slightly wavy, wavy, curly, coily
- Describe hair COLOR with exact shade: jet black, dark brown, medium brown, warm brown, light brown, dark blonde, golden blonde, light blonde, strawberry blonde, auburn, red, etc.
- Describe bangs/fringe if present: thick straight bangs, side-swept bangs, no bangs
- Describe parting if visible: center part, side part, no visible part
- Keep it to ONE descriptive phrase, max 12 words

FORMAT: Respond with ONLY a hair description like:
"short straight dark brown hair with thick straight bangs"
"long wavy light brown hair, center part, no bangs"
"medium curly black hair, no bangs"

Just the hair description, nothing else."""
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 80,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

        hair = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        hair = hair.replace('"', "").replace("'", "").lower()
        if not hair.endswith("hair"):
            hair = hair + " hair"

        logger.info("Hair detected from photo", hair=hair[:50])
        return hair

    except Exception as e:
        logger.warning("Hair detection failed, using default", error=str(e))
        from app.prompt.templates import get_default_hair
        return get_default_hair()


async def _generate_scenario_intro_text(
    *,
    scenario: "Scenario | None",
    child_name: str,
    story_title: str,
) -> str | None:
    """Generate a child-friendly intro paragraph about the scenario location (karşılama 2)."""
    # 1. Use scenario.description if available and meaningful
    if scenario and getattr(scenario, "description", None) and len(scenario.description) > 20:
        return scenario.description[:500]

    # 2. Use scenario_bible cultural_facts
    if scenario and getattr(scenario, "scenario_bible", None):
        facts = scenario.scenario_bible.get("cultural_facts", [])
        if facts:
            return " ".join(str(f) for f in facts[:2])

    # 3. Gemini fallback — generate a short child-friendly intro
    if scenario:
        location = getattr(scenario, "location_en", None) or getattr(scenario, "name", None)
        if not location:
            return None

        prompt = (
            f"'{story_title}' adlı çocuk kitabı için '{location}' hakkında "
            f"2-3 cümlelik, çocuk dostu, eğitici ve büyülü bir giriş paragrafı yaz. "
            f"Türkçe yaz. Sadece paragrafı yaz, başlık veya açıklama ekleme."
        )
        api_key = settings.gemini_api_key
        if not api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200},
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text[:500] if text else None
        except Exception as e:
            logger.warning("Gemini scenario intro text failed", error=str(e))
            return None

    return None
