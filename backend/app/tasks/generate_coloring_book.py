"""Task for generating coloring books from original story orders."""

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus
from app.models.order_page import OrderPage
from app.models.product import Product
from app.services.order_state_machine import transition_order
from app.services.storage_service import storage_service
from app.tasks._coloring_shared import (
    convert_pages_to_line_art,
    generate_coloring_pdf,
    get_coloring_book_config,
)

logger = structlog.get_logger()


async def generate_coloring_book(order_id: UUID, db: AsyncSession):
    """Generate coloring book from original story order.

    Process:
    1. Lock coloring book order
    2. Find original order
    3. Download original page images
    4. Convert to line-art (parallel)
    5. Generate PDF without text
    6. Upload to GCS
    """
    # Lock order (skip locked to avoid concurrent processing)
    stmt = select(Order).where(Order.id == order_id).with_for_update(skip_locked=True)
    result = await db.execute(stmt)
    coloring_order = result.scalar_one_or_none()

    if not coloring_order:
        logger.error("Coloring book order not found", order_id=str(order_id))
        return

    if not coloring_order.is_coloring_book:
        logger.error("Order is not a coloring book", order_id=str(order_id))
        return

    logger.info("Starting coloring book generation", order_id=str(order_id))

    await transition_order(coloring_order, OrderStatus.PROCESSING, db)

    try:
        # Find original order (reverse lookup via coloring_book_order_id)
        original_order = await _find_original_order(coloring_order.id, db)

        if not original_order:
            raise ValueError("Original order not found")

        logger.info(
            "Found original order",
            coloring_order_id=str(coloring_order.id),
            original_order_id=str(original_order.id),
        )

        # Get original order pages
        pages_result = await db.execute(
            select(OrderPage)
            .where(OrderPage.order_id == original_order.id)
            .order_by(OrderPage.page_number)
        )
        original_pages = pages_result.scalars().all()

        if not original_pages:
            raise ValueError("Original order has no pages")

        logger.info(
            "Found original pages", order_id=str(original_order.id), count=len(original_pages)
        )

        # Get coloring book config (for future line-art tuning)
        await get_coloring_book_config(db)

        # Convert pages to line-art (parallel)
        page_entries = [(p.page_number, p.image_url) for p in original_pages]
        line_art_pages = await convert_pages_to_line_art(
            page_entries, f"coloring/{order_id}"
        )

        # Get product for PDF generation
        product_result = await db.execute(
            select(Product)
            .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
            .where(Product.id == original_order.product_id)
        )
        product = product_result.scalar_one_or_none()

        if not product:
            raise ValueError("Product not found for original order")

        # Generate PDF
        pdf_bytes = generate_coloring_pdf(
            coloring_order.child_name, line_art_pages, product.inner_template
        )

        # Upload PDF to GCS
        pdf_filename = f"coloring/{order_id}/coloring_book.pdf"
        pdf_url = storage_service.provider.upload_bytes(
            pdf_bytes, pdf_filename, content_type="application/pdf"
        )

        logger.info("Coloring book PDF generated", pdf_url=pdf_url)

        # Update order
        coloring_order.final_pdf_url = pdf_url
        coloring_order.total_pages = len(line_art_pages)
        coloring_order.completed_pages = len(line_art_pages)
        await transition_order(coloring_order, OrderStatus.READY_FOR_PRINT, db)

        logger.info("Coloring book generation completed", order_id=str(order_id))

    except Exception as e:
        logger.error(
            "Coloring book generation failed",
            order_id=str(order_id),
            error=str(e),
        )

        coloring_order.generation_error = str(e)
        await transition_order(coloring_order, OrderStatus.CANCELLED, db)

        raise


async def _find_original_order(coloring_order_id: UUID, db: AsyncSession) -> Order | None:
    """Find original story order linked to coloring book order."""
    stmt = (
        select(Order)
        .where(Order.coloring_book_order_id == coloring_order_id)
        .where(Order.is_coloring_book == False)  # noqa: E712
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
