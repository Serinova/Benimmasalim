"""Task for generating coloring books from StoryPreviews (Trials)."""

import asyncio
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.story_preview import StoryPreview
from app.services.image_processing import image_processing_service
from app.services.pdf_service import PDFService
from app.services.storage_service import storage_service

logger = structlog.get_logger()


async def generate_coloring_book_for_trial(trial_id: UUID, db: AsyncSession):
    """
    Generate coloring book from a Try Before You Buy Trial (StoryPreview).

    Process:
    1. Lock trial
    2. Download generated page images
    3. Convert to line-art (parallel)
    4. Generate PDF without text using the selected product's size
    5. Upload to GCS and save to the trial

    Args:
        trial_id: StoryPreview ID
        db: Database session
    """
    stmt = select(StoryPreview).where(StoryPreview.id == trial_id).with_for_update(skip_locked=True)
    result = await db.execute(stmt)
    trial = result.scalar_one_or_none()

    if not trial:
        logger.error("StoryPreview not found", trial_id=str(trial_id))
        return

    if not trial.has_coloring_book:
        logger.warning(
            "StoryPreview does not have coloring book flag set", trial_id=str(trial_id)
        )
        return

    logger.info("Starting coloring book generation for trial", trial_id=str(trial_id))

    try:
        # Get trial pages
        if not trial.page_images:
            raise ValueError("Trial has no generated pages")

        # Get coloring book config (for future line-art tuning)
        _coloring_config = await _get_coloring_book_config(db)

        # We need to process pages in order (or pass them correctly to PDFService)
        # Note: trial.page_images is a dict {page_number_str: "url"}
        page_entries = []
        for page_num_str, img_url in trial.page_images.items():
            # Skip dedication or back_cover images if present, we only want story pages 0-15
            if not page_num_str.isdigit():
                continue
            
            page_num = int(page_num_str)
            page_entries.append((page_num, img_url))
        
        # Sort by page number
        page_entries.sort(key=lambda x: x[0])
        
        if not page_entries:
            raise ValueError("Trial has no valid numbered pages")

        logger.info(
            "Found trial pages", trial_id=str(trial_id), count=len(page_entries)
        )

        sem = asyncio.Semaphore(3)
        async def convert_page(page_num: int, image_url: str) -> dict:
            """Convert single page to line-art."""
            async with sem:
                try:
                    # Download original image via httpx (storage_service has no download method)
                    import httpx
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.get(image_url)
                        response.raise_for_status()
                        image_bytes = response.content

                    # Convert to line-art using Gemini
                    line_art_bytes = await image_processing_service.convert_to_line_art_ai(
                        image_bytes
                    )

                    # Upload to GCS via provider
                    blob_path = f"coloring/trials/{trial_id}/page_{page_num}.png"
                    line_art_url = storage_service.provider.upload_bytes(
                        line_art_bytes, blob_path, "image/png"
                    )

                    logger.info(
                        "Trial page converted to line-art",
                        page_number=page_num,
                        url=line_art_url,
                    )

                    return {
                        "page_number": page_num,
                        "image_url": line_art_url,
                        "text": None,  # NO TEXT for coloring book
                    }

                except Exception as e:
                    logger.error(
                        "Failed to convert trial page",
                        page_number=page_num,
                        error=str(e),
                    )
                    raise
                
        # Process all pages in parallel
        line_art_pages = await asyncio.gather(*[convert_page(p_num, url) for p_num, url in page_entries])

        logger.info("All trial pages converted to line-art", count=len(line_art_pages))

        from sqlalchemy.orm import selectinload

        # We need a Product configuration to size the PDF (A4/US Letter size usually)
        # We can either fetch the generic "coloring_book" product or use the trial's product
        product_result = await db.execute(
            select(Product)
            .options(
                selectinload(Product.inner_template),
                selectinload(Product.cover_template)
            )
            .where(Product.product_type == "coloring_book")
            .limit(1)
        )
        coloring_product = product_result.scalar_one_or_none()

        if not coloring_product and trial.product_id:
            logger.info("Falling back to trial product for dimensions")
            product_result = await db.execute(
                select(Product)
                .options(
                    selectinload(Product.inner_template),
                    selectinload(Product.cover_template)
                )
                .where(Product.id == trial.product_id)
            )
            coloring_product = product_result.scalar_one_or_none()
            
        if not coloring_product:
             raise ValueError("No product found to base the PDF dimensions on")

        # Build template_config from product's inner_template
        _inner_tpl = coloring_product.inner_template
        _page_width_mm = 297.0
        _page_height_mm = 210.0
        _bleed_mm = 3.0
        if _inner_tpl:
            _tw, _th = _inner_tpl.page_width_mm, _inner_tpl.page_height_mm
            if _tw < _th:
                from app.utils.resolution_calc import (
                    A4_LANDSCAPE_HEIGHT_MM,
                    A4_LANDSCAPE_WIDTH_MM,
                )
                _page_width_mm, _page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
            else:
                _page_width_mm, _page_height_mm = _tw, _th
            _bleed_mm = _inner_tpl.bleed_mm

        _template_config: dict = {
            "page_width_mm": _page_width_mm,
            "page_height_mm": _page_height_mm,
            "bleed_mm": _bleed_mm,
            "image_x_percent": 0.0,
            "image_y_percent": 0.0,
            "image_width_percent": 100.0,
            "image_height_percent": 100.0,
            "text_x_percent": 0.0,
            "text_y_percent": 0.0,
            "text_width_percent": 0.0,
            "text_height_percent": 0.0,
            "text_enabled": False,
        }
        if _inner_tpl:
            _template_config.update({
                "image_x_percent": _inner_tpl.image_x_percent or 0.0,
                "image_y_percent": _inner_tpl.image_y_percent or 0.0,
                "image_width_percent": _inner_tpl.image_width_percent or 100.0,
                "image_height_percent": 100.0,  # Full page for coloring
                "text_enabled": False,
            })

        _pdf_data = {
            "child_name": trial.child_name,
            "story_pages": line_art_pages,
            "cover_image_url": None,
            "back_cover_config": None,
            "audio_qr_url": None,
            "page_width_mm": _page_width_mm,
            "page_height_mm": _page_height_mm,
            "bleed_mm": _bleed_mm,
            "template_config": _template_config,
            "images_precomposed": True,  # Line-art images are ready, no text
        }

        pdf_service = PDFService()
        pdf_bytes = pdf_service.generate_book_pdf_from_preview(_pdf_data)

        # Upload PDF to GCS via provider
        pdf_blob_path = f"coloring/trials/{trial_id}/coloring_book.pdf"
        pdf_url = storage_service.provider.upload_bytes(
            pdf_bytes, pdf_blob_path, "application/pdf"
        )

        logger.info("Coloring book PDF generated for trial", pdf_url=pdf_url)

        # Update Trial
        trial.coloring_pdf_url = pdf_url
        await db.commit()

        logger.info("Coloring book generation completed for trial", trial_id=str(trial_id))

    except Exception as e:
        logger.error(
            "Coloring book generation failed for trial",
            trial_id=str(trial_id),
            error=str(e),
        )
        # We don't change the trial status to cancelled because the main storybook succeeded
        # We could add a 'coloring_generation_failed' flag later if needed
        raise


async def _get_coloring_book_config(db: AsyncSession) -> dict:
    """
    Get active coloring book product configuration from unified products table.
    
    Returns type_specific_data containing line-art settings.
    """
    stmt = (
        select(Product)
        .where(Product.product_type == "coloring_book")
        .where(Product.is_active == True)
        .limit(1)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        logger.warning("No active coloring book product found, using defaults")
        return {
            "line_art_method": "canny",
            "edge_threshold_low": 80,
            "edge_threshold_high": 200,
        }

    config = product.type_specific_data or {}
    return {
        "line_art_method": config.get("line_art_method", "canny"),
        "edge_threshold_low": config.get("edge_threshold_low", 80),
        "edge_threshold_high": config.get("edge_threshold_high", 200),
    }

