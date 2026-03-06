"""Task for generating coloring books from original story orders."""

import asyncio
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.order_page import OrderPage
from app.models.product import Product
from app.services.image_processing import image_processing_service
from app.services.order_state_machine import transition_order
from app.services.pdf_service import PDFService
from app.services.storage_service import storage_service

logger = structlog.get_logger()


async def generate_coloring_book(order_id: UUID, db: AsyncSession):
    """
    Generate coloring book from original story order.

    Process:
    1. Lock coloring book order
    2. Find original order
    3. Download original page images
    4. Convert to line-art (parallel)
    5. Generate PDF without text
    6. Upload to GCS

    Args:
        order_id: Coloring book order ID
        db: Database session
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
        _coloring_config = await _get_coloring_book_config(db)

        # Convert pages to line-art (parallel processing)
        sem = asyncio.Semaphore(3)
        async def convert_page(page: OrderPage) -> dict:
            """Convert single page to line-art."""
            async with sem:
                try:
                    # Download original image
                    import httpx
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(page.image_url)
                        resp.raise_for_status()
                        image_bytes = resp.content

                    # Convert to line-art using Gemini
                    line_art_bytes = await image_processing_service.convert_to_line_art_ai(
                        image_bytes
                    )

                    # Upload to GCS
                    filename = f"coloring/{order_id}/page_{page.page_number}.png"
                    line_art_url = storage_service.provider.upload_bytes(
                        line_art_bytes, filename, content_type="image/png"
                    )

                    logger.info(
                        "Page converted to line-art",
                        page_number=page.page_number,
                        url=line_art_url,
                    )

                    return {
                        "page_number": page.page_number,
                        "image_url": line_art_url,
                        "text": None,  # NO TEXT for coloring book
                    }

                except Exception as e:
                    logger.error(
                        "Failed to convert page",
                        page_number=page.page_number,
                        error=str(e),
                    )
                    raise

        # Process all pages in parallel
        line_art_pages = await asyncio.gather(*[convert_page(p) for p in original_pages])

        logger.info("All pages converted to line-art", count=len(line_art_pages))

        # Get product for PDF generation
        from app.models.product import Product
        from sqlalchemy.orm import selectinload
        product_result = await db.execute(
            select(Product)
            .options(selectinload(Product.inner_template), selectinload(Product.cover_template))
            .where(Product.id == original_order.product_id)
        )
        product = product_result.scalar_one_or_none()
        
        if not product:
            raise ValueError("Product not found for original order")

        # Build template_config from product's inner_template
        _inner_tpl = product.inner_template
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
            "child_name": coloring_order.child_name,
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

        # Generate PDF (without text — coloring book)
        pdf_service = PDFService()
        pdf_bytes = pdf_service.generate_book_pdf_from_preview(_pdf_data)

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
        .where(Order.is_coloring_book == False)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


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
        # Fallback to defaults if no coloring product found
        logger.warning("No active coloring book product found, using defaults")
        return {
            "line_art_method": "canny",
            "edge_threshold_low": 80,
            "edge_threshold_high": 200,
        }

    # Extract config from type_specific_data JSONB
    config = product.type_specific_data or {}
    return {
        "line_art_method": config.get("line_art_method", "canny"),
        "edge_threshold_low": config.get("edge_threshold_low", 80),
        "edge_threshold_high": config.get("edge_threshold_high", 200),
    }
