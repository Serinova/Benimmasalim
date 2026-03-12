"""Shared utilities for coloring book generation (order + trial).

Eliminates code duplication between generate_coloring_book.py
and generate_coloring_book_for_trial.py.
"""

import asyncio
from uuid import UUID

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.services.image_processing import image_processing_service
from app.services.storage_service import storage_service

logger = structlog.get_logger()


async def convert_pages_to_line_art(
    pages: list[tuple[int, str]],
    output_prefix: str,
    *,
    concurrency: int = 3,
) -> list[dict]:
    """Download images, convert to line-art, upload to GCS.

    Args:
        pages: List of (page_number, image_url) tuples.
        output_prefix: GCS path prefix, e.g. "coloring/{order_id}".
        concurrency: Max parallel conversions.

    Returns:
        List of dicts with page_number, image_url, text=None.
    """
    sem = asyncio.Semaphore(concurrency)

    async def _convert(page_num: int, image_url: str) -> dict:
        async with sem:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(image_url)
                resp.raise_for_status()
                image_bytes = resp.content

            line_art_bytes = await image_processing_service.convert_to_line_art_ai(
                image_bytes
            )

            blob_path = f"{output_prefix}/page_{page_num}.png"
            line_art_url = storage_service.provider.upload_bytes(
                line_art_bytes, blob_path, "image/png"
            )

            logger.info(
                "Page converted to line-art",
                page_number=page_num,
                url=line_art_url,
            )

            return {
                "page_number": page_num,
                "image_url": line_art_url,
                "text": None,  # NO TEXT for coloring book
            }

    results = await asyncio.gather(*[_convert(pn, url) for pn, url in pages])
    logger.info("All pages converted to line-art", count=len(results))
    return list(results)


def build_coloring_template_config(inner_template) -> tuple[float, float, float, dict]:
    """Build PDF template config from a product's inner_template.

    Returns:
        (page_width_mm, page_height_mm, bleed_mm, template_config)
    """
    page_width_mm = 297.0
    page_height_mm = 210.0
    bleed_mm = 3.0

    if inner_template:
        tw, th = inner_template.page_width_mm, inner_template.page_height_mm
        if tw < th:
            from app.utils.resolution_calc import (
                A4_LANDSCAPE_HEIGHT_MM,
                A4_LANDSCAPE_WIDTH_MM,
            )
            page_width_mm, page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
        else:
            page_width_mm, page_height_mm = tw, th
        bleed_mm = inner_template.bleed_mm

    template_config: dict = {
        "page_width_mm": page_width_mm,
        "page_height_mm": page_height_mm,
        "bleed_mm": bleed_mm,
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
    if inner_template:
        template_config.update({
            "image_x_percent": inner_template.image_x_percent or 0.0,
            "image_y_percent": inner_template.image_y_percent or 0.0,
            "image_width_percent": inner_template.image_width_percent or 100.0,
            "image_height_percent": 100.0,  # Full page for coloring
            "text_enabled": False,
        })

    return page_width_mm, page_height_mm, bleed_mm, template_config


def build_coloring_pdf_data(
    child_name: str,
    line_art_pages: list[dict],
    page_width_mm: float,
    page_height_mm: float,
    bleed_mm: float,
    template_config: dict,
) -> dict:
    """Build the data dict expected by PDFService.generate_book_pdf_from_preview."""
    return {
        "child_name": child_name,
        "story_pages": line_art_pages,
        "cover_image_url": None,
        "back_cover_config": None,
        "audio_qr_url": None,
        "page_width_mm": page_width_mm,
        "page_height_mm": page_height_mm,
        "bleed_mm": bleed_mm,
        "template_config": template_config,
        "images_precomposed": True,
    }


def generate_coloring_pdf(child_name: str, line_art_pages: list[dict], inner_template) -> bytes:
    """Generate coloring book PDF bytes from line-art pages.

    Combines build_coloring_template_config + build_coloring_pdf_data + PDFService.
    """
    from app.services.pdf_service import PDFService

    pw, ph, bleed, tpl_config = build_coloring_template_config(inner_template)
    pdf_data = build_coloring_pdf_data(child_name, line_art_pages, pw, ph, bleed, tpl_config)

    pdf_service = PDFService()
    return pdf_service.generate_book_pdf_from_preview(pdf_data)


async def get_coloring_book_config(db: AsyncSession) -> dict:
    """Get active coloring book product configuration.

    Returns type_specific_data containing line-art settings.
    """
    stmt = (
        select(Product)
        .where(Product.product_type == "coloring_book")
        .where(Product.is_active == True)  # noqa: E712
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
