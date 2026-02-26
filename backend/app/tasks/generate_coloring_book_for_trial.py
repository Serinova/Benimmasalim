"""Task for generating coloring books from StoryPreviews (Trials)."""

import asyncio
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.story_preview import StoryPreview
from app.models.product import Product
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

        # Get coloring book config
        coloring_config = await _get_coloring_book_config(db)

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
             
        # Generate PDF (without text)
        class MockOrder:
            id = trial.id
            child_name = trial.child_name
            language = "tr" # default
            is_coloring_book = True
            
        mock_order = MockOrder()

        pdf_service = PDFService()
        pdf_bytes = await pdf_service.generate_book_pdf(
            order=mock_order, # type: ignore
            product=coloring_product,
            pages=line_art_pages,
            audio_qr_url=None,  # No QR code
            back_cover_config=None,  # No back cover info
            skip_text=True,  # CRITICAL: Skip text rendering
        )

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

