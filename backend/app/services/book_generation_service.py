import asyncio
import base64
import uuid
from typing import Any
from uuid import UUID

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.models.book_template import BackCoverConfig, PageTemplate
from app.models.product import Product
from app.models.scenario import Scenario
from app.models.story_preview import StoryPreview
from app.prompt.book_context import BookContext
from app.prompt.cover_builder import build_back_cover_prompt
from app.services.ai.elevenlabs_service import ElevenLabsService
from app.services.ai.gemini_consistent_image import GeminiConsistentImageService
from app.services.page_composer import PageComposer, build_template_config
from app.services.pdf_service import PDFService
from app.services.preview_display_service import page_images_for_preview as _page_images_for_preview
from app.services.scenario_content_service import generate_scenario_intro_text
from app.services.storage_service import StorageService
from app.utils.resolution_calc import (
    A4_LANDSCAPE_HEIGHT_MM,
    A4_LANDSCAPE_WIDTH_MM,
    calculate_generation_params_from_mm,
    resize_image_bytes_to_target,
)

logger = structlog.get_logger()

class BookGenerationService:
    """Service to orchestrate the book generation process from a StoryPreview."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageService()
        self.pdf_service = PDFService()

    async def generate_full_book(self, preview: StoryPreview) -> dict[str, Any]:
        """
        Takes a confirmed StoryPreview and orchestrates:
        1. Audiobook generation (if requested)
        2. Scenario intro (page 2) image generation
        3. Back cover generation
        4. PDF merging
        
        Returns a dict with audio_file_url, audio_qr_url, pdf_url, pdf_error.
        Changes to preview.page_images or preview.back_cover_image_url are
        committed to the DB during the process.
        """
        # 1. Generate Audiobook
        audio_file_url, audio_qr_url = await self._generate_audiobook(preview)
        
        # 2. Prepare Template Settings
        template_config, page_width_mm, page_height_mm, bleed_mm, back_cover_config = await self._prepare_pdf_settings(preview)

        # 3. Handle specific pages (Cover, inner images)
        cover_image_url, story_pages_with_images, dedication_image_url, page_images = self._prepare_pages(preview)

        # 4. Generate Back Cover and Intro Page (in parallel)
        (intro_image_url, intro_b64), back_cover_image_url = await asyncio.gather(
            self._generate_intro_page(preview, page_images),
            self._generate_back_cover(preview, page_images)
        )

        # 5. Commit incremental asset urls
        needs_commit = False
        if back_cover_image_url and back_cover_image_url != getattr(preview, "back_cover_image_url", None):
            preview.back_cover_image_url = back_cover_image_url
            needs_commit = True
        
        if intro_image_url and intro_image_url != (preview.page_images or {}).get("intro"):
            needs_commit = True # _generate_intro_page modifies dict in place, but safe to commit
            
        if needs_commit:
            await self.db.commit()

        # 6. Generate PDF
        pdf_data = {
            "child_name": preview.child_name,
            "story_pages": story_pages_with_images,
            "cover_image_url": cover_image_url,
            "dedication_image_url": dedication_image_url,
            "intro_image_base64": intro_b64,
            "intro_image_url": intro_image_url,
            "back_cover_config": back_cover_config,
            "back_cover_image_url": back_cover_image_url,
            "audio_qr_url": audio_qr_url,
            "page_width_mm": page_width_mm,
            "page_height_mm": page_height_mm,
            "bleed_mm": bleed_mm,
            "template_config": template_config,
            "images_precomposed": True,
        }

        pdf_url, pdf_error = await self._generate_and_upload_pdf(preview.id, pdf_data)

        return {
            "has_audio": getattr(preview, "has_audio_book", False),
            "audio_file_url": audio_file_url,
            "audio_qr_url": audio_qr_url,
            "pdf_url": pdf_url,
            "pdf_error": pdf_error,
        }

    async def _generate_audiobook(self, preview: StoryPreview) -> tuple[str | None, str | None]:
        if not getattr(preview, "has_audio_book", False):
            return None, None
            
        audio_type = getattr(preview, "audio_type", None)
        audio_voice_id = getattr(preview, "audio_voice_id", None)
        
        try:
            elevenlabs = ElevenLabsService()
            full_story_text = ""
            if preview.story_pages:
                for page in preview.story_pages:
                    if isinstance(page, dict) and page.get("text"):
                        full_story_text += page["text"] + "\n\n"

            if full_story_text.strip():
                logger.info("Generating audio book", preview_id=str(preview.id), audio_type=audio_type)

                if audio_type == "cloned" and audio_voice_id:
                    audio_bytes = await elevenlabs.text_to_speech(text=full_story_text, voice_id=audio_voice_id)
                else:
                    audio_bytes = await elevenlabs.text_to_speech(text=full_story_text, voice_type="female")

                audio_file_url = self.storage.upload_audio(audio_bytes=audio_bytes, order_id=str(preview.id), filename="audiobook.mp3")
                audio_qr_url = self.storage.get_signed_url(audio_file_url, expiration_hours=24 * 365)
                
                logger.info("Audio book generated", preview_id=str(preview.id), audio_url=audio_file_url)
                return audio_file_url, audio_qr_url
        except Exception as e:
            logger.error("Audio generation failed", preview_id=str(preview.id), error=str(e))
        return None, None

    async def _prepare_pdf_settings(self, preview: StoryPreview) -> tuple[dict[str, Any], float, float, float, BackCoverConfig | None]:
        # Get back cover config
        back_cover_config = None
        try:
            result = await self.db.execute(
                select(BackCoverConfig)
                .where(BackCoverConfig.is_active == True)
                .where(BackCoverConfig.is_default == True)
            )
            back_cover_config = result.scalar_one_or_none()
        except Exception as e:
            logger.warning("Failed to get back cover config", error=str(e))

        # Get product with inner_template eagerly loaded
        product = None
        inner_template = None
        page_width_mm = 297.0
        page_height_mm = 210.0
        bleed_mm = 3.0

        if preview.product_id:
            result = await self.db.execute(
                select(Product)
                .where(Product.id == preview.product_id)
                .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
            )
            product = result.scalar_one_or_none()

            if product and product.inner_template:
                inner_template = product.inner_template
                _w = inner_template.page_width_mm
                _h = inner_template.page_height_mm
                if _w < _h:
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
            template_config.update({
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
            })
            
        return template_config, page_width_mm, page_height_mm, bleed_mm, back_cover_config

    def _prepare_pages(self, preview: StoryPreview) -> tuple[str | None, list, str | None, dict]:
        # Get cover image from page_images
        cover_image_url = None
        page_images = _page_images_for_preview(preview) or {}
        if page_images:
            cover_image_url = page_images.get("0") or page_images.get(0) or page_images.get("cover")

        # Build story pages with images
        story_pages_with_images = []
        raw_pages = preview.story_pages or []
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
            story_pages_with_images.append(page_data)

        dedication_image_url = page_images.get("dedication")
        return cover_image_url, story_pages_with_images, dedication_image_url, page_images

    async def _generate_intro_page(self, preview: StoryPreview, page_images: dict) -> tuple[str | None, str | None]:
        intro_url = page_images.get("intro")
        if intro_url:
            return intro_url, None
            
        try:
            # Shared resources logic
            scenario_obj_shared = None
            cache_shared = getattr(preview, "generated_prompts_cache", None) or {}
            sc_id_str = cache_shared.get("scenario_id") if isinstance(cache_shared, dict) else None
            if sc_id_str:
                try:
                    scenario_obj_shared = await self.db.get(Scenario, uuid.UUID(sc_id_str))
                except Exception:
                    pass
            if scenario_obj_shared is None and getattr(preview, "scenario_name", None):
                sc_res2 = await self.db.execute(select(Scenario).where(Scenario.name == preview.scenario_name).limit(1))
                scenario_obj_shared = sc_res2.scalar_one_or_none()

            ded_tpl_result = await self.db.execute(
                select(PageTemplate)
                .where(PageTemplate.page_type == "dedication")
                .where(PageTemplate.is_active == True)
                .limit(1)
            )
            ded_tpl_shared = ded_tpl_result.scalar_one_or_none()

            text = await generate_scenario_intro_text(
                scenario=scenario_obj_shared,
                child_name=preview.child_name or "",
                story_title=getattr(preview, "story_title", "") or "",
            )
            
            if text and (
                "[çocuk adı]" in text.lower() or "[cocuk adi]" in text.lower()
                or "kitap adı:" in text.lower() or "kitap adi:" in text.lower()
            ):
                text = None
                
            if text:
                cfg = build_template_config(ded_tpl_shared) if ded_tpl_shared else {}
                b64 = PageComposer().compose_dedication_page(text=text, template_config=cfg, dpi=300)
                if b64:
                    try:
                        img_bytes = base64.b64decode(b64)
                        intro_gcs_url = await self.storage.upload_generated_image(
                            img_bytes, str(preview.id), page_number=9998
                        )
                        # Save to page_images dict (modify memory)
                        pi = dict(preview.page_images or {})
                        pi["intro"] = intro_gcs_url
                        preview.page_images = pi
                        logger.info("Scenario intro page uploaded to GCS", preview_id=str(preview.id), url=intro_gcs_url[:80])
                        return intro_gcs_url, None
                    except Exception as upload_err:
                        logger.warning("Intro page GCS upload failed, using base64 fallback", error=str(upload_err))
                        return None, b64
        except Exception as e:
            logger.warning("Scenario intro page failed", preview_id=str(preview.id), error=str(e))
        return None, None

    async def _generate_back_cover(self, preview: StoryPreview, page_images: dict) -> str | None:
        existing = page_images.get("backcover") or getattr(preview, "back_cover_image_url", None)
        if existing:
            return existing
            
        try:
            image_svc = GeminiConsistentImageService()
            style_name = getattr(preview, "visual_style_name", None) or ""
            scenario_name = getattr(preview, "scenario_name", None) or "magical adventure"
            child_gender = getattr(preview, "child_gender", None) or "child"
            child_name_bc = preview.child_name or "child"
            child_age_bc = getattr(preview, "child_age", None) or 7
            
            clothing = ""
            scenario_id = getattr(preview, "scenario_id", None)
            if scenario_id:
                try:
                    sc_res = await self.db.execute(select(Scenario).where(Scenario.id == uuid.UUID(str(scenario_id))))
                    sc = sc_res.scalar_one_or_none()
                    if sc:
                        g = (child_gender or "erkek").lower()
                        if g in ("kiz", "kız", "girl", "female"):
                            clothing = (getattr(sc, "outfit_girl", None) or "").strip() or (getattr(sc, "outfit_boy", None) or "").strip()
                        else:
                            clothing = (getattr(sc, "outfit_boy", None) or "").strip() or (getattr(sc, "outfit_girl", None) or "").strip()
                        if clothing:
                            logger.info("back_cover: clothing resolved", scenario_id=str(scenario_id), outfit=clothing[:60])
                except Exception as ce:
                    logger.warning("back_cover: failed to resolve clothing", error=str(ce))
            
            if not clothing:
                clothing = (getattr(preview, "clothing_description", None) or "").strip()
            
            face_ref_url = getattr(preview, "face_crop_url", None) or getattr(preview, "child_photo_url", None)

            book_ctx = BookContext.build(
                child_name=child_name_bc, child_age=child_age_bc, child_gender=child_gender,
                scenario_name=scenario_name, clothing_description=clothing,
                story_title=getattr(preview, "story_title", ""), style_modifier=style_name,
            )
            back_scene = (
                f"Wide panoramic view. The same young {child_gender} seen from behind or side, "
                f"gazing into the distance of the {scenario_name} world. "
                f"Continuation of the front cover atmosphere — same lighting, same environment, same mood."
            )
            back_prompt = build_back_cover_prompt(ctx=book_ctx, scene_description=back_scene)
            params = calculate_generation_params_from_mm(A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM)
            
            back_negative = (
                "text, title, letters, words, writing, book title, story title, "
                "watermark, signature, logo, typography, "
                "close-up, portrait, headshot, face filling frame, cropped body, cut-off legs"
            )
            
            result = await image_svc.generate_consistent_image(
                prompt=back_prompt, child_face_url=face_ref_url, clothing_prompt=clothing,
                style_modifier=style_name, width=params["generation_width"], height=params["generation_height"],
                id_weight=book_ctx.style.id_weight, is_cover=True, template_en=None, story_title="",
                child_gender=child_gender, child_age=child_age_bc, 
                style_negative_en=back_negative, base_negative_en="",
                skip_compose=True,  
                precomposed_negative="",
                reference_embedding=getattr(preview, "face_embedding", None),
                character_description=getattr(preview, "child_description", None) or "",
            )
            
            img_url = result[0] if isinstance(result, tuple) else result
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(img_url)
                img_bytes = resp.content
            
            target_w, target_h = params["target_width"], params["target_height"]
            img_bytes = resize_image_bytes_to_target(img_bytes, target_w, target_h, output_format="JPEG", dpi=300)
            
            bc_url = await self.storage.upload_generated_image(img_bytes, str(preview.id), page_number=9999)
            logger.info("Back cover image generated", preview_id=str(preview.id), url=bc_url[:80])
            return bc_url
        except Exception as bc_err:
            logger.warning("Back cover generation failed", preview_id=str(preview.id), error=str(bc_err))
            return None

    async def _generate_and_upload_pdf(self, preview_id: UUID, pdf_data: dict) -> tuple[str | None, str | None]:
        logger.info("Generating PDF for preview", preview_id=str(preview_id))
        try:
            pdf_bytes = await run_in_threadpool(self.pdf_service.generate_book_pdf_from_preview, pdf_data)
            if pdf_bytes:
                pdf_url = self.storage.upload_pdf(pdf_bytes=pdf_bytes, order_id=str(preview_id))
                logger.info("PDF generated and uploaded", preview_id=str(preview_id), pdf_url=pdf_url)
                return pdf_url, None
            else:
                logger.warning("PDF generation returned empty bytes", preview_id=str(preview_id))
                return None, "PDF üretimi boş sonuç döndürdü"
        except Exception as e:
            logger.error("PDF generation failed", preview_id=str(preview_id), error=str(e), exc_info=True)
            return None, str(e)
