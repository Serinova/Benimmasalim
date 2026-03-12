"""Admin PDF generation service.

Contains the Arq worker entry point for background PDF generation.
Extracted from app.api.v1.admin.orders to break the API→service coupling
and allow image_worker to import from the service layer (not the router).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.story_preview import StoryPreview


async def generate_admin_pdf_inner(preview_id: str) -> str:
    """Arq worker entry point. Generates PDF, uploads to GCS, saves URL to preview/order."""

    import structlog
    from starlette.concurrency import run_in_threadpool

    from app.core.database import async_session_factory
    from app.models.book_template import BackCoverConfig
    from app.models.order import Order
    from app.models.story_preview import StoryPreview
    from app.services.admin_pdf_service import _build_template_config_for_preview  # local helper
    from app.services.pdf_service import PDFService
    from app.services.preview_display_service import page_images_for_preview
    from app.services.storage_service import StorageService

    logger = structlog.get_logger()

    async with async_session_factory() as db:
        result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
        preview = result.scalar_one_or_none()

        if not preview:
            logger.error("PDF task: Preview not found", preview_id=preview_id)
            raise ValueError(f"Preview {preview_id} not found")

        page_width_mm, page_height_mm, bleed_mm, template_config = await _build_template_config_for_preview(preview, db)

        back_cover_config = None
        try:
            result = await db.execute(
                select(BackCoverConfig)
                .where(BackCoverConfig.is_active == True)  # noqa: E712
                .where(BackCoverConfig.is_default == True)  # noqa: E712
            )
            back_cover_config = result.scalar_one_or_none()
        except Exception as e:
            logger.warning("Failed to get back cover config", error=str(e))

        page_images = page_images_for_preview(preview) or {}
        raw_pages = preview.story_pages or []

        cover_image_url = None
        if page_images:
            cover_image_url = page_images.get("0") or page_images.get(0) or page_images.get("cover")

        story_pages = []
        for i, page in enumerate(raw_pages):
            if i == 0 and cover_image_url:
                continue
            if isinstance(page, dict) and page.get("page_type") == "front_matter":
                continue

            page_data = dict(page) if isinstance(page, dict) else {"text": str(page)}
            page_num = page.get("page_number", i) if isinstance(page, dict) else i
            page_key = str(page_num)

            if page_key in page_images:
                page_data["image_url"] = page_images[page_key]
                page_data.pop("image_base64", None)
                page_data.pop("imageBase64", None)
            elif page_num in page_images:
                page_data["image_url"] = page_images[page_num]
                page_data.pop("image_base64", None)
                page_data.pop("imageBase64", None)

            story_pages.append(page_data)

        audio_qr_url = None
        has_audio = getattr(preview, "has_audio_book", False)

        if has_audio:
            stored_audio_url = getattr(preview, "audio_file_url", None)
            if stored_audio_url:
                audio_qr_url = stored_audio_url
            else:
                try:
                    from app.services.ai.elevenlabs_service import ElevenLabsService
                    from app.services.storage_service import StorageService as _S

                    _storage = _S()
                    elevenlabs = ElevenLabsService()

                    full_story_text = ""
                    if preview.story_pages:
                        for _page in preview.story_pages:
                            if isinstance(_page, dict) and _page.get("text"):
                                full_story_text += _page["text"] + "\n\n"

                    if full_story_text.strip():
                        audio_type = getattr(preview, "audio_type", "system")
                        audio_voice_id = getattr(preview, "audio_voice_id", None)

                        if audio_type == "cloned" and audio_voice_id:
                            audio_bytes = await elevenlabs.text_to_speech(
                                text=full_story_text,
                                voice_id=audio_voice_id,
                            )
                        else:
                            audio_bytes = await elevenlabs.text_to_speech(
                                text=full_story_text,
                                voice_type="female",
                            )

                        audio_file_url = _storage.upload_audio(
                            audio_bytes=audio_bytes,
                            order_id=str(preview.id),
                            filename="audiobook.mp3",
                        )
                        preview.audio_file_url = audio_file_url
                        await db.commit()
                        audio_qr_url = audio_file_url
                except Exception as e:
                    logger.error("Failed to generate audio for PDF", preview_id=str(preview_id), error=str(e))

        dedication_image_url = page_images.get("dedication")

        _admin_intro_image_url: str | None = page_images.get("intro")
        _admin_intro_b64: str | None = None
        if not _admin_intro_image_url:
            try:
                from app.models.scenario import Scenario as _AdminScenario
                from app.services.scenario_content_service import (
                    generate_scenario_intro_text as _generate_scenario_intro_text,
                )

                _admin_scenario_obj = None
                _admin_cache = getattr(preview, "generated_prompts_cache", None) or {}
                _admin_sc_id_str = _admin_cache.get("scenario_id") if isinstance(_admin_cache, dict) else None
                if _admin_sc_id_str:
                    try:
                        import uuid as _admin_uuid
                        _admin_scenario_obj = await db.get(_AdminScenario, _admin_uuid.UUID(_admin_sc_id_str))
                    except Exception:
                        pass
                if _admin_scenario_obj is None and getattr(preview, "scenario_name", None):
                    from sqlalchemy import select as _sel_sc
                    _sc_res = await db.execute(
                        _sel_sc(_AdminScenario).where(_AdminScenario.name == preview.scenario_name).limit(1)
                    )
                    _admin_scenario_obj = _sc_res.scalar_one_or_none()

                _admin_intro_text = await _generate_scenario_intro_text(
                    scenario=_admin_scenario_obj,
                    child_name=preview.child_name or "",
                    story_title=getattr(preview, "story_title", "") or "",
                )
                if _admin_intro_text:
                    from sqlalchemy import select as _admin_select

                    from app.models.book_template import PageTemplate as _PageTemplate
                    from app.services.page_composer import PageComposer, build_template_config

                    _ded_tpl_result = await db.execute(
                        _admin_select(_PageTemplate)
                        .where(_PageTemplate.page_type == "dedication")
                        .where(_PageTemplate.is_active == True)  # noqa: E712
                        .limit(1)
                    )
                    _admin_ded_tpl = _ded_tpl_result.scalar_one_or_none()
                    _admin_intro_cfg = build_template_config(_admin_ded_tpl) if _admin_ded_tpl else {}
                    _admin_intro_b64 = PageComposer().compose_dedication_page(
                        text=_admin_intro_text,
                        template_config=_admin_intro_cfg,
                        dpi=300,
                    )
                    if _admin_intro_b64:
                        logger.info("Scenario intro page composed for admin PDF", preview_id=str(preview_id))
            except Exception as _intro_err:
                logger.warning("Scenario intro page failed — continuing without it", preview_id=str(preview_id), error=str(_intro_err))

        back_cover_image_url = (
            page_images.get("backcover")
            or getattr(preview, "back_cover_image_url", None)
        )

        if not back_cover_image_url:
            try:
                from app.prompt.book_context import BookContext
                from app.prompt.cover_builder import build_back_cover_prompt
                from app.services.ai.gemini_consistent_image import GeminiConsistentImageService
                from app.services.storage_service import StorageService as _StorageService
                from app.utils.resolution_calc import (
                    A4_LANDSCAPE_HEIGHT_MM,
                    A4_LANDSCAPE_WIDTH_MM,
                    calculate_generation_params_from_mm,
                    resize_image_bytes_to_target,
                )

                _storage_bc = _StorageService()
                _image_svc = GeminiConsistentImageService()
                _style_name = getattr(preview, "visual_style_name", None) or ""
                _scenario_name = getattr(preview, "scenario_name", None) or "magical adventure"
                _child_gender = getattr(preview, "child_gender", None) or "child"
                _child_name = preview.child_name or "child"
                _child_age = getattr(preview, "child_age", None) or 7

                _clothing = ""
                _scenario_id = getattr(preview, "scenario_id", None)
                if _scenario_id:
                    try:
                        from uuid import UUID as _U2

                        from sqlalchemy import select as _sel2

                        from app.models.scenario import Scenario as _Scen2
                        _sc_res2 = await db.execute(_sel2(_Scen2).where(_Scen2.id == _U2(str(_scenario_id))))
                        _sc2 = _sc_res2.scalar_one_or_none()
                        if _sc2:
                            _g2 = (_child_gender or "erkek").lower()
                            if _g2 in ("kiz", "kız", "girl", "female"):
                                _clothing = (getattr(_sc2, "outfit_girl", None) or "").strip() or (getattr(_sc2, "outfit_boy", None) or "").strip()
                            else:
                                _clothing = (getattr(_sc2, "outfit_boy", None) or "").strip() or (getattr(_sc2, "outfit_girl", None) or "").strip()
                            if _clothing:
                                logger.info("back_cover_admin: clothing resolved from scenario", scenario_id=str(_scenario_id), outfit=_clothing[:60])
                    except Exception as _ce2:
                        logger.warning("back_cover_admin: failed to resolve clothing from scenario", error=str(_ce2))

                if not _clothing:
                    _clothing = (getattr(preview, "clothing_description", None) or "").strip()

                _face_ref_url = getattr(preview, "face_crop_url", None) or getattr(preview, "child_photo_url", None)

                _book_ctx = BookContext.build(
                    child_name=_child_name,
                    child_age=_child_age,
                    child_gender=_child_gender,
                    scenario_name=_scenario_name,
                    clothing_description=_clothing,
                    story_title=getattr(preview, "story_title", ""),
                    style_modifier=_style_name,
                )

                _back_scene = (
                    f"Wide panoramic view. "
                    f"The same young {_child_gender} seen from behind or side, "
                    f"gazing into the distance of the {_scenario_name} world. "
                    f"Continuation of the front cover atmosphere — same lighting, same environment, same mood."
                )
                _back_prompt = build_back_cover_prompt(ctx=_book_ctx, scene_description=_back_scene)
                _params = calculate_generation_params_from_mm(A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM)
                _back_negative = (
                    "text, title, letters, words, writing, book title, story title, "
                    "watermark, signature, logo, typography, "
                    "close-up, portrait, headshot, face filling frame, cropped body, cut-off legs"
                )

                _result = await _image_svc.generate_consistent_image(
                    prompt=_back_prompt,
                    child_face_url=_face_ref_url,
                    clothing_prompt=_clothing,
                    style_modifier=_style_name,
                    width=_params["generation_width"],
                    height=_params["generation_height"],
                    id_weight=_book_ctx.style.id_weight,
                    is_cover=True,
                    template_en=None,
                    story_title="",
                    child_gender=_child_gender,
                    child_age=_child_age,
                    style_negative_en=_back_negative,
                    base_negative_en="",
                    skip_compose=False,
                    precomposed_negative="",
                    reference_embedding=getattr(preview, "face_embedding", None),
                    character_description=getattr(preview, "child_description", None) or "",
                )
                _img_url = _result[0] if isinstance(_result, tuple) else _result

                import httpx as _httpx
                async with _httpx.AsyncClient(timeout=60.0) as _client:
                    _resp = await _client.get(_img_url)
                    _img_bytes = _resp.content

                _target_w, _target_h = _params["target_width"], _params["target_height"]
                logger.info("back_cover_admin: resizing to target", gen_size=f"{_params['generation_width']}x{_params['generation_height']}", target_size=f"{_target_w}x{_target_h}")
                _img_bytes = resize_image_bytes_to_target(_img_bytes, _target_w, _target_h, output_format="JPEG", dpi=300)

                back_cover_image_url = await _storage_bc.upload_generated_image(
                    _img_bytes,
                    str(preview.id),
                    page_number=9999,
                )

                preview.back_cover_image_url = back_cover_image_url
                await db.commit()
                logger.info("Back cover image generated for admin PDF", preview_id=str(preview_id), url=back_cover_image_url[:80])
            except Exception as _bc_err:
                logger.warning("Back cover generation failed — continuing without it", preview_id=str(preview_id), error=str(_bc_err))

        pdf_data = {
            "child_name": preview.child_name,
            "story_pages": story_pages,
            "cover_image_url": cover_image_url,
            "dedication_image_url": dedication_image_url,
            "intro_image_base64": _admin_intro_b64,
            "intro_image_url": _admin_intro_image_url,
            "back_cover_config": back_cover_config,
            "back_cover_image_url": back_cover_image_url,
            "audio_qr_url": audio_qr_url,
            "page_width_mm": page_width_mm,
            "page_height_mm": page_height_mm,
            "bleed_mm": bleed_mm,
            "template_config": template_config,
            "images_precomposed": True,
        }

        pdf_service = PDFService()
        pdf_bytes = await run_in_threadpool(pdf_service.generate_book_pdf_from_preview, pdf_data)

        if not pdf_bytes:
            raise ValueError("PDF oluşturulamadı (boş)")

        storage = StorageService()
        pdf_url = storage.upload_pdf(pdf_bytes=pdf_bytes, order_id=str(preview.id))

        manifest = dict(preview.generation_manifest_json) if preview.generation_manifest_json else {}
        manifest["final_pdf_url"] = pdf_url
        preview.generation_manifest_json = manifest

        result = await db.execute(select(Order).where(Order.id == preview.id))
        order = result.scalar_one_or_none()
        if order:
            order.final_pdf_url = pdf_url

        await db.commit()

        return pdf_url


async def _build_template_config_for_preview(preview: StoryPreview, db: AsyncSession) -> tuple[float, float, float, dict]:
    """Load product template from DB and return (page_width_mm, page_height_mm, bleed_mm, template_config).

    Used by both generate_admin_pdf_inner and the generate_book_from_preview endpoint.
    """
    from sqlalchemy.orm import selectinload

    from app.models.product import Product

    page_width_mm = 297.0
    page_height_mm = 210.0
    bleed_mm = 3.0
    inner_template = None

    if preview.product_id:
        result = await db.execute(
            select(Product)
            .where(Product.id == preview.product_id)
            .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
        )
        product = result.scalar_one_or_none()

        if product and product.inner_template:
            inner_template = product.inner_template
            _w, _h = inner_template.page_width_mm, inner_template.page_height_mm
            if _w < _h:
                from app.utils.resolution_calc import (
                    A4_LANDSCAPE_HEIGHT_MM,
                    A4_LANDSCAPE_WIDTH_MM,
                )
                page_width_mm, page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
            else:
                page_width_mm, page_height_mm = _w, _h
            bleed_mm = inner_template.bleed_mm

    template_config: dict = {
        "page_width_mm": page_width_mm,
        "page_height_mm": page_height_mm,
        "bleed_mm": bleed_mm,
        "image_x_percent": 0.0,
        "image_y_percent": 0.0,
        "image_width_percent": 100.0,
        "image_height_percent": 70.0,
        "text_x_percent": 5.0,
        "text_y_percent": 72.0,
        "text_width_percent": 90.0,
        "text_height_percent": 25.0,
        "text_position": "bottom",
        "text_align": "center",
        "font_family": "Arial",
        "font_size_pt": 16,
        "font_color": "#333333",
        "background_color": "#FFFFFF",
    }

    if inner_template:
        template_config.update(
            {
                "image_x_percent": inner_template.image_x_percent or 0.0,
                "image_y_percent": inner_template.image_y_percent or 0.0,
                "image_width_percent": inner_template.image_width_percent or 100.0,
                "image_height_percent": inner_template.image_height_percent or 70.0,
                "text_x_percent": inner_template.text_x_percent or 5.0,
                "text_y_percent": inner_template.text_y_percent or 72.0,
                "text_width_percent": inner_template.text_width_percent or 90.0,
                "text_height_percent": inner_template.text_height_percent or 25.0,
                "text_position": inner_template.text_position or "bottom",
                "text_align": inner_template.text_align or "center",
                "font_family": inner_template.font_family or "Arial",
                "font_size_pt": inner_template.font_size_pt or 16,
                "font_color": inner_template.font_color or "#333333",
                "background_color": inner_template.background_color or "#FFFFFF",
            }
        )

    return page_width_mm, page_height_mm, bleed_mm, template_config
