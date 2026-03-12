"""Task for generating coloring books from StoryPreviews (Trials)."""

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.story_preview import StoryPreview
from app.services.storage_service import storage_service
from app.tasks._coloring_shared import (
    convert_pages_to_line_art,
    generate_coloring_pdf,
    get_coloring_book_config,
)

logger = structlog.get_logger()


async def generate_coloring_book_for_trial(trial_id: UUID, db: AsyncSession):
    """Generate coloring book from a Try Before You Buy Trial (StoryPreview).

    Process:
    1. Lock trial
    2. Download generated page images
    3. Convert to line-art (parallel)
    4. Generate PDF without text using the selected product's size
    5. Upload to GCS and save to the trial
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
        await get_coloring_book_config(db)

        # Extract sorted page entries from trial.page_images dict
        page_entries = []
        for page_num_str, img_url in trial.page_images.items():
            # Skip dedication or back_cover images if present
            if not page_num_str.isdigit():
                continue
            page_entries.append((int(page_num_str), img_url))

        page_entries.sort(key=lambda x: x[0])

        if not page_entries:
            raise ValueError("Trial has no valid numbered pages")

        logger.info(
            "Found trial pages", trial_id=str(trial_id), count=len(page_entries)
        )

        # Convert pages to line-art (parallel)
        line_art_pages = await convert_pages_to_line_art(
            page_entries, f"coloring/trials/{trial_id}"
        )

        # Get product for PDF dimensions
        product = await _get_coloring_product(trial, db)
        if not product:
            raise ValueError("No product found to base the PDF dimensions on")

        # Generate PDF
        pdf_bytes = generate_coloring_pdf(
            trial.child_name, line_art_pages, product.inner_template
        )

        # Upload PDF to GCS
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
        raise


async def _get_coloring_product(trial: StoryPreview, db: AsyncSession) -> Product | None:
    """Find the best product for PDF dimensions.

    Tries coloring_book product first, falls back to trial's product.
    """
    product_result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.inner_template),
            selectinload(Product.cover_template),
        )
        .where(Product.product_type == "coloring_book")
        .limit(1)
    )
    product = product_result.scalar_one_or_none()

    if not product and trial.product_id:
        logger.info("Falling back to trial product for dimensions")
        product_result = await db.execute(
            select(Product)
            .options(
                selectinload(Product.inner_template),
                selectinload(Product.cover_template),
            )
            .where(Product.id == trial.product_id)
        )
        product = product_result.scalar_one_or_none()

    return product
