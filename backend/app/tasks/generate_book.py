"""Background task: generate complete book after payment (Fal.ai + PuLID V3)."""

from __future__ import annotations

import asyncio
import time
from uuid import UUID

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
from app.services.appearance_service import detect_clothing_from_photo, detect_hair_from_photo
from app.services.book_pipeline_steps import (
    generate_back_cover_image,
    pipeline_step_audio,
    pipeline_step_back_cover_config,
    pipeline_step_dedication_pages,
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

    Triggered after successful payment.

    Steps:
    1. Generate all page images (using existing cover)
    2. Apply overlays if needed
    3. Upscale images
    4. Generate PDF
    5. Generate audio if selected
    6. Update order status to READY_FOR_PRINT
    """
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
        _scenario = await db.get(Scenario, order.scenario_id)
        style = await db.get(VisualStyle, order.visual_style_id)

        # Get page templates from product
        cover_template: PageTemplate | None = None
        inner_template: PageTemplate | None = None
        if product.cover_template_id:
            cover_template = await db.get(PageTemplate, product.cover_template_id)
        if product.inner_template_id:
            inner_template = await db.get(PageTemplate, product.inner_template_id)

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
            select(OrderPage)
            .where(OrderPage.order_id == order.id)
            .order_by(OrderPage.page_number)
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

        # ── Resolve appearance (clothing + hair) ──────────────────────────────
        # OUTFIT PRIORITY:
        # 1. Scenario outfit (gender-specific) — highest priority
        # 2. Stored clothing_description from order (trial/preview phase)
        # 3. AI detection from child photo
        # 4. Gender default fallback

        _scenario_outfit = _resolve_scenario_outfit(_scenario, order)
        clothing_description = (getattr(order, "clothing_description", None) or "").strip()
        hair_description = (getattr(order, "hair_description", None) or "").strip()

        if _scenario_outfit:
            clothing_description = _scenario_outfit
            logger.info(
                "Using scenario-specific outfit (highest priority)",
                order_id=order_id,
                clothing=clothing_description[:100],
            )
        elif clothing_description:
            logger.info(
                "Using stored clothing_description from order",
                order_id=order_id,
                clothing=clothing_description[:100],
            )
        elif order.child_photo_url:
            try:
                logger.info(
                    "Detecting appearance from child photo",
                    trace_id=tracer.trace_id,
                    order_id=order_id,
                    child_name=order.child_name,
                    child_photo_hash=mask_photo_url(order.child_photo_url),
                )
                clothing_description, hair_description = await asyncio.gather(
                    detect_clothing_from_photo(
                        photo_url=order.child_photo_url,
                        gender=order.child_gender,
                    ),
                    detect_hair_from_photo(
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

                clothing_description = get_default_clothing(
                    "boy" if order.child_gender == "erkek" else "girl"
                )
                hair_description = get_default_hair()
        else:
            logger.warning(
                "No child photo provided - PuLID face consistency unavailable",
                trace_id=tracer.trace_id,
                order_id=order_id,
            )
            from app.prompt.templates import get_default_clothing, get_default_hair

            clothing_description = get_default_clothing(
                "boy" if order.child_gender == "erkek" else "girl"
            )
            hair_description = get_default_hair()

        from app.services.ai.face_service import resolve_face_reference

        _face_ref_url, _original_photo_url, _face_embedding = await resolve_face_reference(
            order.child_photo_url or "", storage
        )

                # Character description: DB'den oku, yoksa on-the-fly üret
        character_description = (getattr(order, "face_description", None) or "").strip()
        if not character_description and _face_ref_url:
            try:
                from app.services.ai.face_analyzer_service import get_face_analyzer

                _face_analyzer = get_face_analyzer()
                # Use "AI Director" mode for concise description (30-50 words) to avoid prompt dilution
                character_description = await _face_analyzer.analyze_for_ai_director(
                    image_source=_face_ref_url,
                    child_name=order.child_name or "",
                    child_age=order.child_age or 7,
                    child_gender=order.child_gender or "",
                )
                order.face_description = character_description
                await db.commit()
                logger.info(
                    "CHARACTER_DESCRIPTION_GENERATED_CONCISE",
                    order_id=order_id,
                    desc_preview=character_description[:80],
                )
            except Exception as _e:
                logger.warning(
                    "Character description generation failed — face locked via PuLID only",
                    order_id=order_id,
                    error=str(_e),
                )

        # Personalize style modifier
        style_modifier_raw = style.prompt_modifier if style else ""
        style_modifier = style_modifier_raw
        if order.child_name and "{child_name}" in style_modifier:
            style_modifier = style_modifier.replace("{child_name}", order.child_name)
        if "{child_age}" in style_modifier:
            style_modifier = style_modifier.replace("{child_age}", str(order.child_age or 7))

        ai_config = await get_effective_ai_config(db, product_id=order.product_id)
        provider_name = (
            (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
        )
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

        # Build BookContext and PromptComposer once for the entire book
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

        _style_overrides = _extract_style_overrides(style)

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
            id_weight_override=_style_overrides["id_weight"],
            leading_prefix_override=_book_leading_prefix_override,
            style_block_override=_book_style_block_override,
        )
        prompt_composer = PromptComposer(
            book_ctx,
            cover_template=cover_prompt_tpl,
            inner_template=inner_prompt_tpl,
        )

        # ── Generate page images ──────────────────────────────────────────────
        generated_pages: list[dict] = []
        pages_to_generate: list[OrderPage] = []

        for page in existing_pages:
            if page.is_cover and page.image_url:
                # Front cover: upscale + resize for print quality
                cover_page_data = await _process_existing_cover(
                    page=page,
                    order_id=order_id,
                    story_title=_story_title,
                    cover_template=cover_template,
                    storage=storage,
                )
                generated_pages.append(cover_page_data)
            else:
                pages_to_generate.append(page)

        # Mark all pending pages as processing in one batch
        for page in pages_to_generate:
            page.image_generation_status = "processing"
        await db.commit()

        _download_client = httpx.AsyncClient(timeout=60.0)
        _page_sem = asyncio.Semaphore(settings.image_concurrency)

        async def _generate_single_page(
            page: OrderPage,
        ) -> tuple[OrderPage, str | None, str | None]:
            async with _page_sem:
                _img_start = time.monotonic()
                try:
                    scene_action = page.image_prompt or page.text_content or ""
                    current_template = (cover_template or inner_template) if page.is_cover else inner_template

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

                    result = await image_provider.generate_consistent_image(
                        prompt=_final_prompt_text,
                        child_face_url=_face_ref_url,
                        clothing_prompt=clothing_description,
                        style_modifier=style_modifier,
                        width=width,
                        height=height,
                        id_weight=book_ctx.style.id_weight,
                        true_cfg_override=_style_overrides["true_cfg"],
                        start_step_override=_style_overrides["start_step"],
                        num_inference_steps_override=_style_overrides["num_inference_steps"],
                        guidance_scale_override=_style_overrides["guidance_scale"],
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
                        original_photo_url=_original_photo_url,
                    )
                    image_url = result[0] if isinstance(result, tuple) else result

                    resp = await _download_client.get(image_url)
                    image_bytes = resp.content

                    # Upscale → resize to print target
                    image_bytes = await _upscale_and_resize(
                        image_bytes=image_bytes,
                        params=params,
                        page_number=page.page_number,
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

        try:
            if pages_to_generate:
                results = await asyncio.gather(
                    *[_generate_single_page(p) for p in pages_to_generate],
                    return_exceptions=True,
                )
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
                                "text": (_story_title if page.is_cover else page.text_content) or "",
                                "image_url": final_url,
                                "is_cover": page.is_cover,
                                "page_number": page.page_number,
                            }
                        )
                    else:
                        page.image_generation_status = "failed"
                        page.generation_attempt += 1
                await db.commit()
        finally:
            await _download_client.aclose()

        # ── Pipeline steps 5–8b ───────────────────────────────────────────────
        audio_qr_url = await pipeline_step_audio(
            db=db,
            order=order,
            generated_pages=generated_pages,
            storage=storage,
            order_id=order_id,
        )

        back_cover_image_url: str | None = None
        try:
            back_cover_image_url = await generate_back_cover_image(
                order=order,
                book_ctx=book_ctx,
                image_provider=image_provider,
                storage=storage,
                cover_template=cover_template,
                inner_template=inner_template,
                clothing_description=clothing_description,
                style_modifier=style_modifier,
                face_ref_url=_face_ref_url,
                original_photo_url=_original_photo_url,
                face_embedding=_face_embedding,
                true_cfg_override=_style_overrides["true_cfg"],
                start_step_override=_style_overrides["start_step"],
                num_inference_steps_override=_style_overrides["num_inference_steps"],
                guidance_scale_override=_style_overrides["guidance_scale"],
                leading_prefix_override=_book_leading_prefix_override,
                style_block_override=_book_style_block_override,
            )
            if back_cover_image_url:
                order.back_cover_image_url = back_cover_image_url
                await db.commit()
                logger.info(
                    "Back cover image generated",
                    order_id=order_id,
                    url=back_cover_image_url[:80],
                )
        except Exception as e:
            logger.warning(
                "Back cover image generation failed — continuing without it",
                order_id=order_id,
                error=str(e),
            )

        back_cover_config = await pipeline_step_back_cover_config(db)
        dedication_image_base64, intro_image_base64 = await pipeline_step_dedication_pages(
            db=db,
            order=order,
            story_title=_story_title,
            scenario=_scenario,
            order_id=order_id,
        )

        # ── Step 9: Generate PDF ──────────────────────────────────────────────
        # Kapak önce, sonra hikaye sayfaları (page_number sırasına göre) gelsin.
        generated_pages.sort(key=lambda p: (0 if p.get("is_cover") else 1, p.get("page_number", 999)))
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

            pdf_url = storage.upload_pdf(pdf_bytes=pdf_bytes, order_id=str(order.id))
            order.final_pdf_url = pdf_url

            await transition_order(order, OrderStatus.READY_FOR_PRINT, db)

            # Create StoryPreview for customer approval + send confirmation email
            try:
                import secrets as _secrets
                from datetime import datetime, timedelta, timezone

                from app.models.story_preview import PreviewStatus, StoryPreview
                from app.models.user import User
                from app.services.email_service import email_service

                _user = await db.get(User, order.user_id) if order.user_id else None
                _recipient_email = _user.email if _user and _user.email else None
                _recipient_name = (_user.full_name if _user else None) or ""

                if _recipient_email:
                    # Build page_images dict from generated OrderPages
                    _page_images: dict[str, str] = {}
                    _story_pages_data: list[dict] = []
                    _pages_result = await db.execute(
                        select(OrderPage)
                        .where(OrderPage.order_id == order.id)
                        .order_by(OrderPage.page_number)
                    )
                    _all_pages = list(_pages_result.scalars().all())
                    for _op in _all_pages:
                        if _op.image_url:
                            _key = "0" if _op.is_cover else str(_op.page_number)
                            _page_images[_key] = _op.image_url
                        if not _op.is_cover:
                            _story_pages_data.append({
                                "page_number": _op.page_number,
                                "text": _op.text_content or "",
                                "visual_prompt": _op.image_prompt or "",
                            })

                    # Add back cover if generated
                    if back_cover_image_url:
                        _page_images["back_cover"] = back_cover_image_url

                    _confirmation_token = _secrets.token_urlsafe(32)
                    _product_price: float | None = None
                    if product and hasattr(product, "base_price") and product.base_price:
                        _product_price = float(product.base_price)

                    _approval_preview = StoryPreview(
                        confirmation_token=_confirmation_token,
                        status=PreviewStatus.PENDING.value,
                        lead_user_id=order.user_id,
                        parent_name=_recipient_name,
                        parent_email=_recipient_email,
                        child_name=order.child_name,
                        child_age=order.child_age,
                        child_gender=order.child_gender,
                        child_photo_url=order.child_photo_url,
                        product_id=order.product_id,
                        product_name=product.name if product else "",
                        product_price=_product_price,
                        story_title=_story_title,
                        story_pages=_story_pages_data,
                        page_images=_page_images,
                        back_cover_image_url=back_cover_image_url,
                        scenario_name=_scenario.name if _scenario else None,
                        visual_style_name=style.name if style else None,
                        is_preview_mode=False,
                        # Cache prompts for per-page regeneration
                        generated_prompts_cache={
                            "order_id": order_id,
                            "prompts": _story_pages_data,
                        },
                        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
                    )
                    db.add(_approval_preview)
                    await db.commit()

                    _confirmation_url = f"{settings.frontend_url}/confirm/{_confirmation_token}"

                    # No images in email — user reviews them on the website
                    await email_service.send_story_email_with_confirmation_async(
                        recipient_email=_recipient_email,
                        recipient_name=_recipient_name or _recipient_email,
                        child_name=order.child_name,
                        story_title=_story_title,
                        story_pages=[],
                        confirmation_url=_confirmation_url,
                        product_price=_product_price,
                    )
                    logger.info(
                        "ORDER_READY_CONFIRMATION_EMAIL_SENT",
                        order_id=order_id,
                        preview_id=str(_approval_preview.id),
                        confirmation_url=_confirmation_url[:60],
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

            tracer.pipeline_complete(page_count=len(generated_pages))

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
            tracer.pipeline_fail(error_code="PDF_GENERATION_FAILED", error=str(e))
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


# ── Private helpers ───────────────────────────────────────────────────────────


def _resolve_scenario_outfit(scenario: object | None, order: "Order") -> str:
    """Return the gender-specific scenario outfit string, or empty string."""
    if not scenario:
        return ""
    outfit_girl = (getattr(scenario, "outfit_girl", None) or "").strip()
    outfit_boy = (getattr(scenario, "outfit_boy", None) or "").strip()
    gender_norm = (order.child_gender or "").lower().strip()
    if gender_norm in ("kiz", "kız", "girl", "female"):
        outfit = outfit_girl or outfit_boy
    else:
        outfit = outfit_boy or outfit_girl
    if outfit:
        logger.info(
            "Scenario outfit resolved for book generation",
            scenario_name=getattr(scenario, "name", ""),
            gender=gender_norm,
            outfit=outfit[:80],
        )
    return outfit


def _extract_style_overrides(style: object | None) -> dict:
    """Extract nullable numeric overrides from a VisualStyle instance."""
    return {
        "id_weight": float(style.id_weight) if style and style.id_weight is not None else None,
        "true_cfg": (
            float(style.true_cfg)
            if style and getattr(style, "true_cfg", None) is not None
            else None
        ),
        "start_step": (
            int(style.start_step)
            if style and getattr(style, "start_step", None) is not None
            else None
        ),
        "num_inference_steps": (
            int(style.num_inference_steps)
            if style and getattr(style, "num_inference_steps", None) is not None
            else None
        ),
        "guidance_scale": (
            float(style.guidance_scale)
            if style and getattr(style, "guidance_scale", None) is not None
            else None
        ),
    }


async def _process_existing_cover(
    *,
    page: "OrderPage",
    order_id: str,
    story_title: str,
    cover_template: "PageTemplate | None",
    storage: StorageService,
) -> dict:
    """Download, upscale and resize an existing front cover for print quality."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(page.image_url)
            cover_img_bytes = resp.content

        if cover_template:
            cover_params = get_effective_generation_params(cover_template)
        else:
            cover_params = calculate_generation_params_from_mm(
                A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
            )

        cover_img_bytes = await _upscale_and_resize(
            image_bytes=cover_img_bytes,
            params=cover_params,
            page_number=page.page_number,
            is_cover=True,
        )

        highres_cover_url = await storage.upload_generated_image(
            cover_img_bytes,
            str(page.order_id),
            page.page_number,
        )
        logger.info(
            "Front cover upscaled and ready",
            order_id=order_id,
            highres_url=highres_cover_url,
        )
        return {"text": story_title or page.text_content or "", "image_url": highres_cover_url, "is_cover": True, "page_number": page.page_number}

    except Exception as cover_err:
        logger.error(
            "Front cover upscale failed, using original",
            order_id=order_id,
            error=str(cover_err),
        )
        return {"text": story_title or page.text_content or "", "image_url": page.image_url, "is_cover": True, "page_number": page.page_number}


async def _upscale_and_resize(
    *,
    image_bytes: bytes,
    params: dict,
    page_number: int,
    is_cover: bool = False,
) -> bytes:
    """Apply AI upscale (if needed) then resize to print target dimensions."""
    _needs_upscale = params.get("needs_upscale", False)
    _upscale_factor = params.get("upscale_factor", 1)

    if _needs_upscale and _upscale_factor > 1:
        from app.services.upscale_service import upscale_image_bytes_safe

        _before_kb = len(image_bytes) // 1024
        image_bytes = await upscale_image_bytes_safe(
            image_bytes, upscale_factor=_upscale_factor
        )
        logger.info(
            "UPSCALE_APPLIED",
            page=page_number,
            factor=_upscale_factor,
            before_kb=_before_kb,
            after_kb=len(image_bytes) // 1024,
        )

    try:
        _before_resize = len(image_bytes)
        image_bytes = resize_image_bytes_to_target(
            image_bytes,
            params["target_width"],
            params["target_height"],
            is_cover=is_cover,
        )
        logger.info(
            "Image resized to print target",
            page=page_number,
            target=f"{params['target_width']}x{params['target_height']}",
            before_kb=_before_resize // 1024,
            after_kb=len(image_bytes) // 1024,
        )
    except Exception as e:
        logger.warning(
            "Resize to target failed, using current size",
            page=page_number,
            error=str(e),
        )

    return image_bytes
