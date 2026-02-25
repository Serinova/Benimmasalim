"""PDF generation service using ReportLab.

Uses dynamic dimensions from PageTemplate - NEVER hard-code pixel values!
"""

import gc
import io

import httpx
import qrcode
import structlog
from PIL import Image
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models.book_template import BackCoverConfig, PageTemplate
from app.models.order import Order
from app.models.product import Product

logger = structlog.get_logger()


class PDFService:
    """Service for generating print-ready PDF books.

    Uses PageTemplate for dynamic dimensions.
    """

    def __init__(self):
        # Register custom fonts if available
        self._register_fonts()

    def _register_fonts(self):
        """Register custom fonts for Turkish characters. Use 'DejaVuSans' everywhere (TR: ş,ğ,İ,ı)."""
        import os

        # Project-relative path first (bundled font)
        _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        bundled = os.path.join(_root, "fonts", "DejaVuSans.ttf")

        font_paths = [
            bundled,
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "DejaVuSans.ttf",
            "./fonts/DejaVuSans.ttf",
        ]

        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
                    logger.info("Registered Turkish font (DejaVuSans)", path=font_path)
                    font_registered = True
                    break
                except Exception as e:
                    logger.warning("Failed to register font", path=font_path, error=str(e))

        if not font_registered:
            logger.warning("No Turkish font found, using Helvetica (may have character issues)")

    async def generate_book_pdf(
        self,
        order: Order,
        product: Product,
        pages: list[dict],  # [{"text": ..., "image_url": ...}, ...]
        audio_qr_url: str | None = None,
        back_cover_config: "BackCoverConfig | None" = None,
        dedication_image_base64: str | None = None,
        intro_image_base64: str | None = None,
        back_cover_image_url: str | None = None,
    ) -> bytes:
        """
        Generate a print-ready PDF book.

        Page order:
          1. Front cover
          2. Dedication page / karşılama 1 (if any)
          3. Scenario intro page / karşılama 2 (if any)
          4. Inner story pages
          5. QR+text info page (if back_cover_config, rendered as inner page)
          6. Visual back cover (if back_cover_image_url)

        Args:
            order: Order with child info
            product: Product with template references
            pages: List of page content with text and image URLs
            audio_qr_url: Optional URL for audio book QR code
            back_cover_config: Optional QR+text info page config (now inner page)
            dedication_image_base64: Optional dedication page image (karşılama 1)
            intro_image_base64: Optional scenario intro page image (karşılama 2)
            back_cover_image_url: Optional AI-generated visual back cover URL

        Returns:
            PDF file as bytes
        """
        # Get dimensions from the product's inner template
        inner_template = product.inner_template
        if not inner_template:
            # Fallback: yatay A4 (kitap baskı formatı)
            page_width_mm = 297.0
            page_height_mm = 210.0
            bleed_mm = 3.0
            logger.warning(
                "No inner template found for product, using defaults",
                product_id=str(product.id),
            )
        else:
            _w, _h = inner_template.page_width_mm, inner_template.page_height_mm
            # Kitap yatay A4: şablon dikeyse yatay A4 zorla
            if _w < _h:
                from app.utils.resolution_calc import A4_LANDSCAPE_HEIGHT_MM, A4_LANDSCAPE_WIDTH_MM
                page_width_mm, page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
            else:
                page_width_mm, page_height_mm = _w, _h
            bleed_mm = inner_template.bleed_mm

        # Calculate page size with bleed
        page_width_with_bleed_mm = page_width_mm + (2 * bleed_mm)
        page_height_with_bleed_mm = page_height_mm + (2 * bleed_mm)

        # Convert to points (ReportLab uses points)
        page_width = page_width_with_bleed_mm * mm
        page_height = page_height_with_bleed_mm * mm

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create canvas
        c = canvas.Canvas(
            buffer,
            pagesize=(page_width, page_height),
        )

        # Set PDF metadata
        c.setTitle(f"Benim Masalım - {order.child_name}")
        c.setAuthor("Benim Masalım")
        c.setSubject(f"Kişiselleştirilmiş hikaye kitabı: {order.child_name}")

        # Generate each page (skip front_matter — already handled by dedication slot)
        for i, page in enumerate(pages):
            if isinstance(page, dict) and page.get("page_type") == "front_matter":
                continue
            # Use cover template for first page, inner for rest
            if i == 0 and product.cover_template:
                template = product.cover_template
            else:
                template = inner_template

            await self._render_page(
                c=c,
                page_num=i,
                page_data=page,
                template=template,
                page_width=page_width,
                page_height=page_height,
                is_cover=(i == 0),
            )
            c.showPage()

            # Periodic memory cleanup for long books
            if (i + 1) % 3 == 0:
                gc.collect()

            # Insert dedication page (karşılama 1) right after the cover
            if i == 0 and dedication_image_base64:
                self._add_base64_page(c, dedication_image_base64, page_width, page_height)
                c.showPage()
                logger.info("Dedication page added to PDF (after cover)")

            # Insert scenario intro page (karşılama 2) right after dedication
            if i == 0 and intro_image_base64:
                self._add_base64_page(c, intro_image_base64, page_width, page_height)
                c.showPage()
                logger.info("Scenario intro page (karşılama 2) added to PDF")

        # QR+text info page as inner page (before visual back cover)
        if back_cover_config:
            self.render_qr_info_page(
                c=c,
                page_width=page_width,
                page_height=page_height,
                config=back_cover_config,
                audio_qr_url=audio_qr_url,
                child_name=order.child_name,
            )
            c.showPage()
            logger.info("QR info page added to PDF (inner page)")

        # Visual back cover as the final page
        _visual_back_url = back_cover_image_url or getattr(order, "back_cover_image_url", None)
        if _visual_back_url:
            await self._render_visual_back_cover(
                c=c,
                page_width=page_width,
                page_height=page_height,
                image_url=_visual_back_url,
            )
            c.showPage()
            logger.info("Visual back cover added to PDF (final page)")

        c.save()
        buffer.seek(0)

        logger.info(
            "PDF generated",
            order_id=str(order.id),
            pages=len(pages),
            has_qr_info_page=bool(back_cover_config),
            has_visual_back_cover=bool(_visual_back_url),
            has_audio_qr=bool(audio_qr_url),
            width_mm=page_width_mm,
            height_mm=page_height_mm,
            bleed_mm=bleed_mm,
        )

        return buffer.getvalue()

    def generate_book_pdf_from_preview(
        self,
        data: dict,
    ) -> bytes:
        """
        Generate a print-ready PDF book from preview data (synchronous).
        Includes real-time page composition using PageComposer.

        Args:
            data: Dict with child_name, story_pages, cover_image_url, back_cover_config, audio_qr_url,
                  page_width_mm, page_height_mm, bleed_mm, template_config

        Returns:
            PDF file as bytes
        """


        from app.services.page_composer import PageComposer

        child_name = data.get("child_name", "Çocuk")
        story_pages = data.get("story_pages", [])
        page_images = data.get("page_images", {})
        cover_image_url = data.get("cover_image_url")
        back_cover_config = data.get("back_cover_config")
        back_cover_image_url = data.get("back_cover_image_url")
        audio_qr_url = data.get("audio_qr_url")
        template_config = data.get("template_config", {})

        # Get dimensions from data (pre-extracted to avoid lazy loading)
        page_width_mm = data.get("page_width_mm", 297.0)  # Default: Yatay A4
        page_height_mm = data.get("page_height_mm", 210.0)
        bleed_mm = data.get("bleed_mm", 3.0)

        # Calculate page size with bleed
        page_width_with_bleed_mm = page_width_mm + (2 * bleed_mm)
        page_height_with_bleed_mm = page_height_mm + (2 * bleed_mm)

        # Convert to points
        page_width = page_width_with_bleed_mm * mm
        page_height = page_height_with_bleed_mm * mm

        bleed_pt = bleed_mm * mm
        trim_margin_pt = bleed_pt
        safe_area_pt = bleed_pt + (3.0 * mm)

        expected_story_pages = data.get("expected_story_pages")
        if expected_story_pages is not None and len(story_pages) != expected_story_pages:
            raise ValueError(
                f"Page manifest mismatch: got {len(story_pages)} story pages, "
                f"expected {expected_story_pages}. Job FAIL."
            )

        logger.info(
            "Starting PDF generation",
            page_size_mm=f"{page_width_mm}x{page_height_mm}",
            bleed_mm=bleed_mm,
            page_count=len(story_pages),
        )

        # Create PDF buffer
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Set PDF metadata
        c.setTitle(f"Benim Masalım - {child_name}")
        c.setAuthor("Benim Masalım")
        c.setSubject(f"Kişiselleştirilmiş hikaye kitabı: {child_name}")

        # Initialize PageComposer for real-time composition
        page_composer = PageComposer()

        # Reusable sync httpx client (connection pooling across pages)
        _http = httpx.Client(timeout=60.0)
        try:
            return self._build_pdf_pages(
                c, buffer, _http, page_composer,
                story_pages, page_images, child_name,
                page_width, page_height,
                page_width_mm, page_height_mm,
                back_cover_config, audio_qr_url,
                trim_margin_pt, bleed_pt, safe_area_pt,
                template_config=template_config,
                bleed_mm=bleed_mm,
                cover_image_url=cover_image_url,
                data=data,
            )
        finally:
            _http.close()

    def _build_pdf_pages(
        self, c, buffer, _http, page_composer,
        story_pages, page_images, child_name,
        page_width, page_height,
        page_width_mm, page_height_mm,
        back_cover_config, audio_qr_url,
        trim_margin_pt, bleed_pt, safe_area_pt,
        *,
        template_config: dict | None = None,
        bleed_mm: float = 3.0,
        cover_image_url: str | None = None,
        data: dict | None = None,
    ) -> bytes:
        """Internal: render all pages into the PDF canvas and return bytes."""
        import base64

        from PIL import Image as PILImage

        data = data or {}
        template_config = template_config or {}
        images_precomposed = data.get("images_precomposed", False)
        # Helper function to add image from URL
        def add_image_from_url(image_url: str) -> bool:
            img = None
            img_buffer = None
            temp_buffer = None
            try:
                response = _http.get(image_url)
                response.raise_for_status()

                img_buffer = io.BytesIO(response.content)
                img = PILImage.open(img_buffer)

                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    rgb_img = img.convert("RGB")
                    img.close()
                    img = rgb_img

                temp_buffer = io.BytesIO()
                img.save(temp_buffer, format="JPEG", quality=95)
                img.close()
                img = None
                temp_buffer.seek(0)

                # Draw image to fill page
                c.drawImage(
                    ImageReader(temp_buffer),
                    0,
                    0,
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=False,
                )
                return True
            except Exception as e:
                logger.error("Failed to add image from URL", url=image_url[:120], error=str(e), exc_info=True)
                return False
            finally:
                if img is not None:
                    img.close()
                if temp_buffer is not None:
                    temp_buffer.close()
                if img_buffer is not None:
                    img_buffer.close()

        # Helper function to add base64 image (with optional composition)
        def add_composed_image(image_base64: str, text: str, is_cover: bool = False) -> bool:
            img = None
            img_buffer = None
            temp_buffer = None
            try:
                final_base64 = image_base64

                # Only compose if images are NOT already pre-composed
                if not images_precomposed:
                    config = template_config.copy() if template_config else {}
                    config["bleed_mm"] = bleed_mm
                    text_enabled = config.get("text_enabled", True)
                    if not text_enabled:
                        config["image_height_percent"] = 100.0
                        config["text_height_percent"] = 0.0

                    page_text = text if text_enabled else ""
                    final_base64 = page_composer.compose_page(
                        image_base64=image_base64,
                        text=page_text,
                        template_config=config,
                        page_width_mm=page_width_mm,
                        page_height_mm=page_height_mm,
                    )

                if "," in final_base64:
                    img_data = base64.b64decode(final_base64.split(",")[1])
                else:
                    img_data = base64.b64decode(final_base64)
                del final_base64

                img_buffer = io.BytesIO(img_data)
                del img_data
                img = PILImage.open(img_buffer)

                if img.mode in ("RGBA", "P"):
                    rgb_img = img.convert("RGB")
                    img.close()
                    img = rgb_img

                temp_buffer = io.BytesIO()
                img.save(temp_buffer, format="JPEG", quality=95)
                img.close()
                img = None
                temp_buffer.seek(0)

                c.drawImage(
                    ImageReader(temp_buffer),
                    0,
                    0,
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=False,
                )
                return True
            except Exception as e:
                logger.error("Failed to add base64 image", error=str(e), exc_info=True)
                return False
            finally:
                if img is not None:
                    img.close()
                if temp_buffer is not None:
                    temp_buffer.close()
                if img_buffer is not None:
                    img_buffer.close()

        if cover_image_url and add_image_from_url(cover_image_url):
            c.showPage()

        # Extract all special page URLs from data dict
        back_cover_image_url = data.get("back_cover_image_url")

        # Add dedication page / karşılama 1 (right after cover, before story pages)
        dedication_image_b64 = data.get("dedication_image_base64")
        dedication_image_url = data.get("dedication_image_url")
        if dedication_image_b64:
            self._add_base64_page(c, dedication_image_b64, page_width, page_height)
            c.showPage()
            logger.info("Dedication page added to PDF (from base64)")
        elif dedication_image_url:
            if add_image_from_url(dedication_image_url):
                c.showPage()
                logger.info("Dedication page added to PDF (from URL)")
            else:
                logger.warning("Failed to add dedication page from URL: %s", dedication_image_url)

        # Add scenario intro page / karşılama 2 (right after dedication)
        intro_image_b64 = data.get("intro_image_base64")
        intro_image_url = data.get("intro_image_url")
        if intro_image_b64:
            self._add_base64_page(c, intro_image_b64, page_width, page_height)
            c.showPage()
            logger.info("Scenario intro page (karşılama 2) added to PDF (from base64)")
        elif intro_image_url:
            if add_image_from_url(intro_image_url):
                c.showPage()
                logger.info("Scenario intro page (karşılama 2) added to PDF (from URL)")
            else:
                logger.warning("Failed to add intro page from URL: %s", intro_image_url)

        # Add story pages (skip front_matter — already handled by dedication slot)
        pages_added = 0
        for i, page in enumerate(story_pages):
            if isinstance(page, dict) and page.get("page_type") == "front_matter":
                continue
            if isinstance(page, dict):
                image_url = page.get("image_url") or page.get("imageUrl")
                image_base64 = page.get("image_base64") or page.get("imageBase64")
                text = page.get("text", "")

                page_added = False

                # Priority 1: Image from URL
                # If images_precomposed=True, text is already baked into the image
                # by page_composer.compose_page() — skip ReportLab text overlay
                if image_url:
                    page_added = add_image_from_url(image_url)
                    if page_added and text and not images_precomposed and template_config.get("text_enabled", True):
                        self._add_text_from_config(
                            c, text, page_width, page_height, template_config
                        )

                # Priority 2: Compose from raw base64 image
                if not page_added and image_base64:
                    page_added = add_composed_image(
                        image_base64, text, is_cover=(i == 0 and not cover_image_url)
                    )

                # Priority 3: Text-only page
                if not page_added:
                    self._add_text_page(c, text, page_width, page_height, child_name)
                    page_added = True

                if page_added:
                    c.showPage()
                    pages_added += 1
                    # Free memory after each page
                    if pages_added % 3 == 0:
                        gc.collect()

        if pages_added == 0 and len(story_pages) > 0:
            logger.error(
                "PDF_NO_PAGES_RENDERED",
                story_pages_count=len(story_pages),
                has_cover=bool(cover_image_url),
            )

        # QR+text info page as inner page (before visual back cover)
        if back_cover_config:
            self.render_qr_info_page(
                c=c,
                page_width=page_width,
                page_height=page_height,
                config=back_cover_config,
                audio_qr_url=audio_qr_url,
                child_name=child_name,
            )
            c.showPage()

        # Visual back cover as the final page
        if back_cover_image_url:
            try:
                response = _http.get(back_cover_image_url)
                response.raise_for_status()
                _img_buf = io.BytesIO(response.content)
                from PIL import Image as _PILImg
                _img = _PILImg.open(_img_buf)
                if _img.mode != "RGB":
                    _img = _img.convert("RGB")
                _tmp = io.BytesIO()
                _img.save(_tmp, format="JPEG", quality=95)
                _img.close()
                _tmp.seek(0)
                c.drawImage(
                    ImageReader(_tmp), 0, 0,
                    width=page_width, height=page_height,
                    preserveAspectRatio=False,
                )
                _tmp.close()
                c.showPage()
                logger.info("Visual back cover added to preview PDF")
            except Exception as _e:
                logger.warning("Failed to add visual back cover to preview PDF", error=str(_e))

        total_pages = (
            1
            + (1 if (dedication_image_b64 or dedication_image_url) else 0)
            + (1 if (intro_image_b64 or intro_image_url) else 0)
            + pages_added
            + (1 if back_cover_config else 0)
            + (1 if back_cover_image_url else 0)
        )
        expected_total = data.get("expected_total_pages")
        if expected_total is not None and total_pages != expected_total:
            raise ValueError(
                f"PDF page count mismatch: generated {total_pages} pages, "
                f"expected {expected_total}. Job FAIL."
            )

        c.save()
        buffer.seek(0)

        logger.info(
            "PDF generated from preview",
            child_name=child_name,
            pages_added=pages_added,
            has_back_cover=bool(back_cover_config),
            has_audio_qr=bool(audio_qr_url),
            page_size_mm=f"{page_width_mm}x{page_height_mm}",
        )

        return buffer.getvalue()

    def _add_base64_page(self, c, image_base64: str, page_width: float, page_height: float):
        """Add a full-page image from a base64-encoded PNG/JPEG string."""
        import base64 as _b64
        try:
            raw = image_base64
            if "," in raw:
                raw = raw.split(",", 1)[1]
            img_data = _b64.b64decode(raw)
            img_buf = io.BytesIO(img_data)
            del img_data
            img = Image.open(img_buf)
            if img.mode in ("RGBA", "P"):
                rgb_img = img.convert("RGB")
                img.close()
                img = rgb_img
            tmp = io.BytesIO()
            img.save(tmp, format="JPEG", quality=95)
            img.close()
            del img
            tmp.seek(0)
            c.drawImage(
                ImageReader(tmp), 0, 0,
                width=page_width, height=page_height,
                preserveAspectRatio=False,
            )
            tmp.close()
            img_buf.close()
        except Exception as e:
            logger.warning("Failed to add base64 page to PDF: %s", e)

    def _add_text_page(self, c, text: str, page_width: float, page_height: float, child_name: str):
        """Add a text-only page to the PDF (TR-safe font)."""
        c.setFillColorRGB(0.98, 0.95, 0.9)
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        try:
            c.setFont("DejaVuSans", 14)
        except Exception:
            c.setFont("Helvetica", 14)

        margin = 50
        y = page_height - 100
        try:
            _font = "DejaVuSans" if "DejaVuSans" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
        except Exception:
            _font = "Helvetica"
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if c.stringWidth(test_line, _font, 14) < page_width - 2 * margin:
                line = test_line
            else:
                c.drawString(margin, y, line)
                y -= 20
                line = word
                if y < margin:
                    break
        if line:
            c.drawString(margin, y, line)

    async def generate_book_pdf_with_templates(
        self,
        order: Order,
        cover_template: PageTemplate,
        inner_template: PageTemplate,
        back_template: PageTemplate | None,
        pages: list[dict],
        audio_qr_url: str | None = None,
    ) -> bytes:
        """
        Generate PDF with explicit templates.

        Use this when you have direct access to templates.
        """
        # Use inner template dimensions; dikeyse yatay A4 zorla
        _w, _h = inner_template.page_width_mm, inner_template.page_height_mm
        if _w < _h:
            from app.utils.resolution_calc import A4_LANDSCAPE_HEIGHT_MM, A4_LANDSCAPE_WIDTH_MM
            page_width_mm, page_height_mm = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
        else:
            page_width_mm, page_height_mm = _w, _h
        bleed_mm = inner_template.bleed_mm

        page_width_with_bleed_mm = page_width_mm + (2 * bleed_mm)
        page_height_with_bleed_mm = page_height_mm + (2 * bleed_mm)

        page_width = page_width_with_bleed_mm * mm
        page_height = page_height_with_bleed_mm * mm

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        c.setTitle(f"Benim Masalım - {order.child_name}")
        c.setAuthor("Benim Masalım")
        c.setSubject(f"Kişiselleştirilmiş hikaye kitabı: {order.child_name}")

        for i, page in enumerate(pages):
            # Select template based on page position
            if i == 0:
                template = cover_template
            elif back_template and i == len(pages) - 1:
                template = back_template
            else:
                template = inner_template

            await self._render_page(
                c=c,
                page_num=i,
                page_data=page,
                template=template,
                page_width=page_width,
                page_height=page_height,
                is_cover=(i == 0),
            )

            if i == len(pages) - 1 and audio_qr_url:
                self._add_qr_code(c, audio_qr_url, page_width, page_height)

            c.showPage()

        c.save()
        buffer.seek(0)

        logger.info(
            "PDF generated with explicit templates",
            order_id=str(order.id),
            pages=len(pages),
            width_mm=page_width_mm,
            height_mm=page_height_mm,
            bleed_mm=bleed_mm,
        )

        return buffer.getvalue()

    async def _render_page(
        self,
        c: canvas.Canvas,
        page_num: int,
        page_data: dict,
        template: PageTemplate | None,
        page_width: float,
        page_height: float,
        is_cover: bool,
    ):
        """Render a single page with image and text."""
        image_url = page_data.get("image_url")
        text = page_data.get("text", "")

        # Download and place image
        if image_url:
            try:
                image = await self._download_image(image_url)

                # Convert to RGB for PDF
                if image.mode != "RGB":
                    rgb_image = image.convert("RGB")
                    image.close()
                    image = rgb_image

                # Save to temp buffer to reduce memory footprint
                tmp = io.BytesIO()
                image.save(tmp, format="JPEG", quality=95)
                image.close()
                del image
                tmp.seek(0)

                # Place image
                c.drawImage(
                    ImageReader(tmp),
                    0,
                    0,
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=True,
                    anchor="c",
                )
                tmp.close()
            except Exception as e:
                logger.error("Failed to add image to page", page=page_num, error=str(e))
                # Add placeholder color
                c.setFillColorRGB(0.95, 0.95, 0.95)
                c.rect(0, 0, page_width, page_height, fill=1)

        # Add text using template settings
        # Respect text_enabled from template (defaults to True for backward compatibility)
        # If template has text_enabled=False, skip text rendering for this page type
        text_enabled = getattr(template, "text_enabled", True) if template else not is_cover

        if text and text_enabled:
            self._add_text(c, text, page_width, page_height, template)
            logger.debug("Text added to page", page_num=page_num, text_enabled=text_enabled)
        elif text:
            logger.debug("Text skipped (text_enabled=False)", page_num=page_num, is_cover=is_cover)

    def _add_text(
        self,
        c: canvas.Canvas,
        text: str,
        page_width: float,
        page_height: float,
        template: PageTemplate | None,
    ):
        """Add text to page with proper formatting from template."""
        # Get text settings from template or use defaults
        if template:
            margin_mm = template.margin_bottom_mm
            text_height_pct = template.text_height_percent
        else:
            margin_mm = 15.0
            text_height_pct = 25.0

        margin = margin_mm * mm
        text_box_height = page_height * text_height_pct / 100

        # Draw semi-transparent text background
        c.setFillColorRGB(1, 1, 1, alpha=0.85)
        c.rect(
            margin,
            margin,
            page_width - (2 * margin),
            text_box_height,
            fill=1,
            stroke=0,
        )

        # Add text
        c.setFillColorRGB(0, 0, 0)

        # Get font settings from template (8-732 pt; geçersiz/eksik ise 14)
        raw_fs = template.font_size_pt if template else 12
        font_size = 14 if not raw_fs or raw_fs < 8 or raw_fs > 732 else int(raw_fs)
        try:
            c.setFont("DejaVuSans", font_size)
        except Exception:
            c.setFont("Helvetica", font_size)

        # Word wrap and draw
        text_obj = c.beginText(margin + 5 * mm, margin + text_box_height - 10 * mm)
        text_obj.setLeading(font_size * 1.3)

        # Simple word wrap
        words = text.split()
        line = ""
        max_chars = int((page_width - 2 * margin - 10 * mm) / (6 * mm) * 2)

        for word in words:
            if len(line) + len(word) + 1 <= max_chars:
                line += word + " "
            else:
                text_obj.textLine(line.strip())
                line = word + " "

        if line:
            text_obj.textLine(line.strip())

        c.drawText(text_obj)

    def _add_text_from_config(
        self,
        c: canvas.Canvas,
        text: str,
        page_width: float,
        page_height: float,
        config: dict,
    ) -> None:
        """Add vector text overlay using config dict (for preview PDF when no PageTemplate)."""
        margin_mm = float(config.get("margin_bottom_mm", 15.0))
        text_height_pct = float(config.get("text_height_percent", 25.0))
        raw_fs = config.get("font_size_pt", 12)
        font_size = 14 if not raw_fs or raw_fs < 8 or raw_fs > 732 else int(raw_fs)
        margin = margin_mm * mm
        text_box_height = page_height * text_height_pct / 100
        c.setFillColorRGB(1, 1, 1, alpha=0.85)
        c.rect(margin, margin, page_width - 2 * margin, text_box_height, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        try:
            c.setFont("DejaVuSans", font_size)
        except Exception:
            c.setFont("Helvetica", font_size)
        text_obj = c.beginText(margin + 5 * mm, margin + text_box_height - 10 * mm)
        text_obj.setLeading(font_size * 1.3)
        words = text.split()
        line = ""
        max_chars = int((page_width - 2 * margin - 10 * mm) / (6 * mm) * 2)
        for word in words:
            if len(line) + len(word) + 1 <= max_chars:
                line += word + " "
            else:
                text_obj.textLine(line.strip())
                line = word + " "
        if line:
            text_obj.textLine(line.strip())
        c.drawText(text_obj)

    async def _download_image(self, url: str) -> Image.Image:
        """Download image from URL."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            img_buf = io.BytesIO(response.content)
            del response  # Free response body early
            return Image.open(img_buf)

    def _apply_overlay(
        self,
        base: Image.Image,
        overlay: Image.Image,
        opacity: float,
    ) -> Image.Image:
        """Apply overlay PNG on top of base image using LANCZOS."""
        # Ensure RGBA
        base = base.convert("RGBA")
        overlay = overlay.convert("RGBA")

        # Resize overlay to match base using LANCZOS for quality
        overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)

        # Apply opacity
        if opacity < 1.0:
            alpha = overlay.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            overlay.putalpha(alpha)

        # Composite
        result = Image.alpha_composite(base, overlay)

        return result

    def _add_qr_code(
        self,
        c: canvas.Canvas,
        url: str,
        page_width: float,
        page_height: float,
    ):
        """Add QR code for audio book access."""
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to ReportLab image
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        img_reader = ImageReader(qr_buffer)

        # Position in bottom-right corner
        qr_size = 25 * mm
        margin = 10 * mm

        c.drawImage(
            img_reader,
            page_width - qr_size - margin,
            margin,
            width=qr_size,
            height=qr_size,
        )

        # Add label
        c.setFont("Helvetica", 8)
        c.drawString(
            page_width - qr_size - margin,
            margin + qr_size + 2 * mm,
            "Sesli Kitap",
        )

        # Cleanup QR buffer
        qr_buffer.close()

    def _generate_qr_image(self, url: str) -> tuple[ImageReader, io.BytesIO]:
        """Generate QR code image reader. Returns (reader, buffer) so caller can close buffer."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        return ImageReader(qr_buffer), qr_buffer

    async def _render_visual_back_cover(
        self,
        c: canvas.Canvas,
        page_width: float,
        page_height: float,
        image_url: str,
    ) -> None:
        """Render the AI-generated visual back cover as a full-bleed page."""
        try:
            image = await self._download_image(image_url)
            if image.mode != "RGB":
                rgb_image = image.convert("RGB")
                image.close()
                image = rgb_image
            tmp = io.BytesIO()
            image.save(tmp, format="JPEG", quality=95)
            image.close()
            del image
            tmp.seek(0)
            c.drawImage(
                ImageReader(tmp),
                0, 0,
                width=page_width,
                height=page_height,
                preserveAspectRatio=False,
            )
            tmp.close()
        except Exception as e:
            logger.error("Failed to render visual back cover", error=str(e))
            c.setFillColorRGB(0.9, 0.9, 0.9)
            c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    def render_qr_info_page(
        self,
        c: canvas.Canvas,
        page_width: float,
        page_height: float,
        config: "BackCoverConfig",
        audio_qr_url: str | None = None,
        child_name: str | None = None,
    ):
        """
        Render QR+text info page (formerly the back cover).

        Now rendered as an inner page before the visual back cover.
        Solid background color with company info, tips, and QR code.

        Layout:
        - Top: Company logo and tagline
        - Middle: Parent tips
        - Bottom: QR code (if audio), company info, copyright
        """
        return self.render_back_cover(
            c=c,
            page_width=page_width,
            page_height=page_height,
            config=config,
            audio_qr_url=audio_qr_url,
            child_name=child_name,
            back_cover_image_url=None,
        )

    def render_back_cover(
        self,
        c: canvas.Canvas,
        page_width: float,
        page_height: float,
        config: "BackCoverConfig",
        audio_qr_url: str | None = None,
        child_name: str | None = None,
        back_cover_image_url: str | None = None,
    ):
        """
        Render back cover / QR info page design.

        If back_cover_image_url is provided:
          - AI-generated image fills the full page as background
          - A semi-transparent gradient panel at the bottom hosts the text/QR overlay
        Otherwise: solid background color.

        Layout:
        - Top: Company logo and tagline
        - Middle: Parent tips
        - Bottom: QR code (if audio), company info, copyright
        """
        import io as _io

        from reportlab.lib.colors import HexColor

        def safe_hex(color_str: str, fallback: str = "#333333") -> HexColor:
            """Parse hex color with fallback for invalid values."""
            try:
                return HexColor(color_str)
            except Exception:
                logger.warning("Invalid hex color: %s, using fallback: %s", color_str, fallback)
                return HexColor(fallback)

        margin = 15 * mm

        # --- Background: AI image or solid color ---
        _image_background_used = False
        if back_cover_image_url:
            try:
                import httpx as _httpx
                from reportlab.lib.utils import ImageReader as _IR
                _resp = _httpx.get(back_cover_image_url, timeout=15.0)
                _resp.raise_for_status()
                _img_buf = _io.BytesIO(_resp.content)
                _img_reader = _IR(_img_buf)
                c.drawImage(_img_reader, 0, 0, width=page_width, height=page_height, preserveAspectRatio=False)
                _image_background_used = True
                logger.info("BACK_COVER_AI_IMAGE_RENDERED", url=back_cover_image_url[:60])
            except Exception as _e:
                logger.warning("BACK_COVER_IMAGE_LOAD_FAILED", error=str(_e))

        if not _image_background_used:
            # Solid background (legacy / fallback)
            bg_color = safe_hex(config.background_color, "#FFFFFF")
            c.setFillColor(bg_color)
            c.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        if _image_background_used:
            # Semi-transparent dark overlay panel for the bottom 40% — ensures text is readable
            from reportlab.lib.colors import Color as _Color
            _panel_h = page_height * 0.42
            _overlay = _Color(0, 0, 0, alpha=0.55)
            c.setFillColor(_overlay)
            c.rect(0, 0, page_width, _panel_h, fill=1, stroke=0)

        # Border if enabled
        if config.show_border:
            border_color = safe_hex(config.border_color, "#CCCCCC")
            c.setStrokeColor(border_color)
            c.setLineWidth(2)
            c.rect(
                margin / 2, margin / 2, page_width - margin, page_height - margin, fill=0, stroke=1
            )

        # Current Y position (start from top)
        y_pos = page_height - margin - 10 * mm

        # === TOP SECTION: Company name and tagline ===
        # When AI image is used as background, override colors to white for readability
        if _image_background_used:
            primary_color = HexColor("#FFFFFF")
            text_color = HexColor("#F0F0F0")
        else:
            primary_color = safe_hex(config.primary_color, "#333333")
            text_color = safe_hex(config.text_color, "#333333")

        # Helper to set font with Turkish support (must match _register_fonts: DejaVuSans)
        def set_font(size, bold=False):
            try:
                c.setFont("DejaVuSans", size)
            except Exception:
                c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

        # Company name
        c.setFillColor(primary_color)
        set_font(18, bold=True)
        c.drawCentredString(page_width / 2, y_pos, config.company_name)
        y_pos -= 8 * mm

        # Tagline
        c.setFillColor(text_color)
        set_font(11)
        c.drawCentredString(page_width / 2, y_pos, config.tagline)
        y_pos -= 15 * mm

        # Decorative line
        c.setStrokeColor(primary_color)
        c.setLineWidth(1)
        c.line(margin * 2, y_pos, page_width - margin * 2, y_pos)
        y_pos -= 12 * mm

        # === MIDDLE SECTION: Parent tips ===
        # Tips title
        c.setFillColor(primary_color)
        set_font(12, bold=True)
        c.drawCentredString(page_width / 2, y_pos, config.tips_title)
        y_pos -= 8 * mm

        # Tips content
        c.setFillColor(text_color)
        set_font(config.tips_font_size)

        tips_lines = config.tips_content.strip().split("\n")
        for line in tips_lines:
            c.drawString(margin * 1.5, y_pos, line.strip())
            y_pos -= 5 * mm

        y_pos -= 10 * mm

        # === BOTTOM SECTION: QR Code and Company Info ===

        # Debug log for QR
        logger.info(
            "Back cover QR check",
            audio_qr_url=audio_qr_url,
            qr_enabled=config.qr_enabled if config else None,
        )

        # QR Code (if audio book)
        if audio_qr_url and config.qr_enabled:
            qr_size = config.qr_size_mm * mm
            qr_reader, qr_buf = self._generate_qr_image(audio_qr_url)

            # Position based on config
            if config.qr_position == "bottom_left":
                qr_x = margin
            elif config.qr_position == "center":
                qr_x = (page_width - qr_size) / 2
            else:  # bottom_right
                qr_x = page_width - qr_size - margin

            qr_y = margin + 20 * mm

            # QR background
            c.setFillColor(HexColor("#FFFFFF"))
            c.roundRect(
                qr_x - 3 * mm,
                qr_y - 3 * mm,
                qr_size + 6 * mm,
                qr_size + 10 * mm,
                3 * mm,
                fill=1,
                stroke=0,
            )

            # Draw QR
            c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)
            qr_buf.close()  # Free QR buffer after drawing

            # QR Label
            c.setFillColor(primary_color)
            set_font(8)
            c.drawCentredString(qr_x + qr_size / 2, qr_y + qr_size + 2 * mm, config.qr_label)

        # Company info at bottom
        c.setFillColor(text_color)
        set_font(8)

        info_y = margin + 8 * mm
        c.drawCentredString(page_width / 2, info_y, config.company_website)
        info_y -= 4 * mm
        c.drawCentredString(page_width / 2, info_y, config.company_email)

        # Copyright at very bottom
        c.setFillColor(HexColor("#CCCCCC") if _image_background_used else HexColor("#888888"))
        set_font(7)
        c.drawCentredString(page_width / 2, margin, config.copyright_text)

        # Personalization - child name if provided
        if child_name:
            c.setFillColor(primary_color)
            try:
                c.setFont("DejaVuSans", 9)
            except Exception:
                c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(
                page_width / 2,
                page_height - margin - 25 * mm,
                f"Bu kitap {child_name} için özel olarak hazırlandı",
            )

    def convert_to_cmyk(self, pdf_bytes: bytes) -> bytes:
        """
        Convert PDF from RGB to CMYK color space.

        Note: Full CMYK conversion requires Ghostscript or similar.
        This is a placeholder for the full implementation.
        """
        # For production, use Ghostscript:
        # gs -dSAFER -dBATCH -dNOPAUSE -dNOCACHE -sDEVICE=pdfwrite
        #    -sColorConversionStrategy=CMYK -dProcessColorModel=/DeviceCMYK
        #    -sOutputFile=output.pdf input.pdf

        logger.warning("CMYK conversion not implemented - using RGB PDF")
        return pdf_bytes
