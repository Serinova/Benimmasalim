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
        skip_text: bool = False,  # NEW: Skip text rendering (for coloring books)
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
            skip_text: If True, skip text rendering (for coloring books)

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
            # is_cover: dict'teki flag'e bak; yoksa ilk eleman kapak sayılır (geriye uyumluluk)
            _is_cover = page.get("is_cover", i == 0) if isinstance(page, dict) else (i == 0)
            # Use cover template for cover page, inner for rest
            if _is_cover and product.cover_template:
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
                is_cover=_is_cover,
                skip_text=skip_text,
            )
            c.showPage()

            # Periodic memory cleanup for long books
            if (i + 1) % 3 == 0:
                gc.collect()

            # Insert dedication page (karşılama 1) right after the cover
            if _is_cover and dedication_image_base64:
                self._add_base64_page(c, dedication_image_base64, page_width, page_height)
                c.showPage()
                logger.info("Dedication page added to PDF (after cover)")

            # Insert scenario intro page (karşılama 2) right after dedication
            if _is_cover and intro_image_base64:
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
        skip_text: bool = False,  # NEW: Skip text rendering flag
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

                # Place image — görsel zaten resize_to_target() ile tam PDF oranına getirildi,
                # preserveAspectRatio=True boşluk/bant oluşturur.
                c.drawImage(
                    ImageReader(tmp),
                    0,
                    0,
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=False,
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
        # ALSO: Skip text if skip_text flag is True (for coloring books)
        text_enabled = getattr(template, "text_enabled", True) if template else not is_cover

        if text and text_enabled and not skip_text:
            self._add_text(c, text, page_width, page_height, template)
            logger.debug("Text added to page", page_num=page_num, text_enabled=text_enabled)
        elif text:
            logger.debug("Text skipped", page_num=page_num, skip_text=skip_text, text_enabled=text_enabled, is_cover=is_cover)

    def _add_text(
        self,
        c: canvas.Canvas,
        text: str,
        page_width: float,
        page_height: float,
        template: PageTemplate | None,
    ):
        """Add text to page with proper formatting from template."""
        from reportlab.pdfbase.pdfmetrics import stringWidth

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
        font_name = "DejaVuSans"
        try:
            c.setFont(font_name, font_size)
        except Exception:
            font_name = "Helvetica"
            c.setFont(font_name, font_size)

        # Pixel-accurate word wrap using stringWidth
        text_obj = c.beginText(margin + 5 * mm, margin + text_box_height - 10 * mm)
        text_obj.setLeading(font_size * 1.3)
        max_width = page_width - 2 * margin - 10 * mm

        words = text.split()
        line = ""
        for word in words:
            candidate = (line + " " + word).lstrip() if line else word
            if stringWidth(candidate, font_name, font_size) <= max_width:
                line = candidate
            else:
                if line:
                    text_obj.textLine(line)
                line = word
        if line:
            text_obj.textLine(line)

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
        font_name = "DejaVuSans"
        try:
            c.setFont(font_name, font_size)
        except Exception:
            font_name = "Helvetica"
            c.setFont(font_name, font_size)
        text_obj = c.beginText(margin + 5 * mm, margin + text_box_height - 10 * mm)
        text_obj.setLeading(font_size * 1.3)

        from reportlab.pdfbase.pdfmetrics import stringWidth
        max_width = page_width - 2 * margin - 10 * mm
        words = text.split()
        line = ""
        for word in words:
            candidate = (line + " " + word).lstrip() if line else word
            if stringWidth(candidate, font_name, font_size) <= max_width:
                line = candidate
            else:
                if line:
                    text_obj.textLine(line)
                line = word
        if line:
            text_obj.textLine(line)
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
        Render QR+text info page matching the admin frontend preview design.

        Layout (top to bottom):
        - Gradient background (background_color → background_gradient_end)
        - Decorative corner glows
        - Border (if show_border)
        - 5 Stars row (if show_stars) — accent_color
        - Company name — primary_color, bold
        - Decorative line: short lines + center dot — accent_color (if show_decorative_lines)
        - Tagline — italic, muted
        - Dedication text box — left-accent-border, italic (if dedication_text)
        - Tips section title — UPPERCASE, primary_color
        - Tips content lines
        - Separator: lines + 3 dots (if show_decorative_lines)
        - Bottom: company info (left) + QR code (right)
        - Copyright
        """
        import io as _io
        import math as _math
        from reportlab.lib.colors import HexColor, Color as _RLColor

        def safe_hex(color_str: str, fallback: str = "#333333") -> HexColor:
            try:
                return HexColor(color_str)
            except Exception:
                return HexColor(fallback)

        def hex_to_rgb01(h: HexColor) -> tuple:
            """Return (r, g, b) in 0-1 range."""
            return (h.red, h.green, h.blue)

        def set_font(size, bold=False):
            try:
                c.setFont("DejaVuSans-Bold" if bold else "DejaVuSans", size)
            except Exception:
                c.setFont("Helvetica-Bold" if bold else "Helvetica", size)

        margin = 15 * mm

        # ── Background: gradient (background_color → background_gradient_end) ──
        _image_background_used = False
        if back_cover_image_url:
            try:
                import httpx as _httpx
                from reportlab.lib.utils import ImageReader as _IR
                _resp = _httpx.get(back_cover_image_url, timeout=15.0)
                _resp.raise_for_status()
                _img_buf = _io.BytesIO(_resp.content)
                c.drawImage(_IR(_img_buf), 0, 0, width=page_width, height=page_height,
                            preserveAspectRatio=False)
                _image_background_used = True
                logger.info("BACK_COVER_AI_IMAGE_RENDERED", url=back_cover_image_url[:60])
            except Exception as _e:
                logger.warning("BACK_COVER_IMAGE_LOAD_FAILED", error=str(_e))

        if not _image_background_used:
            bg_start = safe_hex(config.background_color, "#FDF6EC")
            bg_end_hex = getattr(config, "background_gradient_end", config.background_color)
            bg_end = safe_hex(bg_end_hex, "#EDE4F8")
            rs, gs, bs = hex_to_rgb01(bg_start)
            re, ge, be = hex_to_rgb01(bg_end)
            _steps = 60
            for _i in range(_steps):
                _t = _i / max(_steps - 1, 1)
                _band_color = _RLColor(
                    rs + (re - rs) * _t,
                    gs + (ge - gs) * _t,
                    bs + (be - bs) * _t,
                )
                c.setFillColor(_band_color)
                _bh = page_height / _steps
                c.rect(0, _i * _bh, page_width, _bh + 0.5, fill=1, stroke=0)

            # Soft corner glows
            primary_color_str = getattr(config, "primary_color", "#6B21A8")
            accent_color_str = getattr(config, "accent_color", "#F59E0B")
            try:
                _pc = safe_hex(primary_color_str, "#6B21A8")
                _ac = safe_hex(accent_color_str, "#F59E0B")
                _g1 = _RLColor(_pc.red, _pc.green, _pc.blue, alpha=0.08)
                c.setFillColor(_g1)
                c.circle(0, page_height, 30 * mm, fill=1, stroke=0)
                _g2 = _RLColor(_ac.red, _ac.green, _ac.blue, alpha=0.07)
                c.setFillColor(_g2)
                c.circle(page_width, 0, 35 * mm, fill=1, stroke=0)
            except Exception:
                pass

        if _image_background_used:
            _panel_h = page_height * 0.42
            _ov = _RLColor(0, 0, 0, alpha=0.55)
            c.setFillColor(_ov)
            c.rect(0, 0, page_width, _panel_h, fill=1, stroke=0)

        # ── Colors ──────────────────────────────────────────────────────────────
        if _image_background_used:
            primary_color = HexColor("#FFFFFF")
            accent_color = HexColor("#F59E0B")
            text_color = HexColor("#F0F0F0")
            border_col = HexColor("#C4B5FD")
        else:
            primary_color = safe_hex(getattr(config, "primary_color", "#6B21A8"), "#6B21A8")
            accent_color = safe_hex(getattr(config, "accent_color", "#F59E0B"), "#F59E0B")
            text_color = safe_hex(config.text_color, "#2D1B4E")
            border_col = safe_hex(config.border_color, "#C4B5FD")

        # ── Border ──────────────────────────────────────────────────────────────
        if config.show_border:
            c.setStrokeColor(border_col)
            c.setLineWidth(1.5)
            c.roundRect(margin / 2, margin / 2, page_width - margin, page_height - margin,
                        2 * mm, fill=0, stroke=1)

        # ── Layout: top-down ────────────────────────────────────────────────────
        y_pos = page_height - margin - 5 * mm

        # ── Logo (üstte ortalanmış) ───────────────────────────────────────────────
        import os as _os
        from reportlab.lib.utils import ImageReader as _IR2
        try:
            from PIL import Image as _PILImg2
            _pil_available = True
        except ImportError:
            _pil_available = False

        _logo_h_pt = 32.0 * mm  # biraz daha büyük — daha belirgin
        _logo_rendered = False

        _logo_candidates = [
            "/app/assets/logo.png",
            _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
                _os.path.abspath(__file__)))), "assets", "logo.png"),
        ]
        for _lpath in _logo_candidates:
            if _os.path.exists(_lpath):
                try:
                    if _pil_available:
                        _logo_pil = _PILImg2.open(_lpath).convert("RGBA")
                        _lw, _lh = _logo_pil.size
                        _aspect = _lw / _lh
                        _logo_w_pt = _logo_h_pt * _aspect

                        # Arka plan rengiyle composite et → JPEG olarak kaydet
                        # Böylece mask="auto"'nun soluklaştırma sorunu olmaz
                        if not _image_background_used:
                            # Gradient başlangıç rengi (bg_start değişkeni mevcut)
                            try:
                                _bg_r = int(bg_start.red * 255)
                                _bg_g = int(bg_start.green * 255)
                                _bg_b = int(bg_start.blue * 255)
                            except Exception:
                                _bg_r, _bg_g, _bg_b = 253, 246, 236
                        else:
                            _bg_r, _bg_g, _bg_b = 15, 10, 30  # koyu arka plan

                        _bg_layer = _PILImg2.new("RGBA", (_lw, _lh), (_bg_r, _bg_g, _bg_b, 255))
                        _bg_layer.paste(_logo_pil, mask=_logo_pil.split()[3])  # alpha channel ile
                        _composited = _bg_layer.convert("RGB")

                        _logo_buf = _io.BytesIO()
                        _composited.save(_logo_buf, format="JPEG", quality=95)
                        _logo_buf.seek(0)

                        _logo_x = (page_width - _logo_w_pt) / 2
                        _logo_y = y_pos - _logo_h_pt
                        c.drawImage(
                            _IR2(_logo_buf),
                            _logo_x, _logo_y,
                            width=_logo_w_pt, height=_logo_h_pt,
                            preserveAspectRatio=True,
                        )
                    else:
                        # PIL yoksa direkt binary yükle (boyut 1:1 varsay)
                        _aspect = 1.0
                        _logo_w_pt = _logo_h_pt * _aspect
                        _logo_buf = _io.BytesIO()
                        with open(_lpath, "rb") as _lf:
                            _logo_buf.write(_lf.read())
                        _logo_buf.seek(0)
                        _logo_x = (page_width - _logo_w_pt) / 2
                        _logo_y = y_pos - _logo_h_pt
                        c.drawImage(
                            _IR2(_logo_buf),
                            _logo_x, _logo_y,
                            width=_logo_w_pt, height=_logo_h_pt,
                            preserveAspectRatio=True,
                            mask="auto",
                        )

                    y_pos -= _logo_h_pt + 3 * mm
                    _logo_rendered = True
                    logger.info("BACK_COVER_LOGO_RENDERED", path=_lpath)
                    break
                except Exception as _le:
                    logger.warning("BACK_COVER_LOGO_FAILED", path=_lpath, error=str(_le))


        if not _logo_rendered:
            # Fallback: 5 yıldız + company name
            if config.show_stars:
                _star_sz = 3.5 * mm
                _star_gap = 1.0 * mm
                _total_w = 5 * _star_sz + 4 * _star_gap
                _sx0 = (page_width - _total_w) / 2
                c.setFillColor(accent_color)
                for _si in range(5):
                    _cx = _sx0 + _si * (_star_sz + _star_gap) + _star_sz / 2
                    _cy = y_pos - _star_sz / 2
                    _outer = _star_sz / 2
                    _inner = _outer * 0.38
                    _pts = []
                    for _pi in range(10):
                        _ang = _math.radians(-90 + _pi * 36)
                        _r = _outer if _pi % 2 == 0 else _inner
                        _pts.append((_cx + _r * _math.cos(_ang), _cy + _r * _math.sin(_ang)))
                    _path = c.beginPath()
                    _path.moveTo(_pts[0][0], _pts[0][1])
                    for _p in _pts[1:]:
                        _path.lineTo(_p[0], _p[1])
                    _path.close()
                    c.drawPath(_path, fill=1, stroke=0)
                y_pos -= _star_sz + 4 * mm
            c.setFillColor(primary_color)
            set_font(16, bold=True)
            c.drawCentredString(page_width / 2, y_pos, config.company_name)
            y_pos -= 5.5 * mm

        # ── Decorative: line · dot · line ────────────────────────────────────────
        if getattr(config, "show_decorative_lines", True):
            _dot_r = 1.0 * mm
            _line_len = 12 * mm
            _mid_x = page_width / 2
            _dot_y = y_pos - 1.5 * mm
            c.setFillColor(accent_color)
            c.setStrokeColor(accent_color)
            c.setLineWidth(0.6)
            c.line(_mid_x - _dot_r - _line_len, _dot_y, _mid_x - _dot_r - 1, _dot_y)
            c.circle(_mid_x, _dot_y, _dot_r, fill=1, stroke=0)
            c.line(_mid_x + _dot_r + 1, _dot_y, _mid_x + _dot_r + _line_len, _dot_y)
            y_pos -= 5.5 * mm
        else:
            y_pos -= 3 * mm

        # ── Tagline ───────────────────────────────────────────────────────────────
        c.setFillColor(text_color)
        set_font(9.5)
        _tl_text = config.tagline or ""
        _max_tl_w = page_width - 4 * margin
        try:
            _tl_total_w = c.stringWidth(_tl_text, "DejaVuSans", 9.5)
        except Exception:
            _tl_total_w = 0
        if _tl_total_w > _max_tl_w:
            _tl_words = _tl_text.split()
            _tl_lines, _tl_line = [], ""
            for _w in _tl_words:
                _cand = (_tl_line + " " + _w).lstrip() if _tl_line else _w
                try:
                    _fits = c.stringWidth(_cand, "DejaVuSans", 9.5) <= _max_tl_w
                except Exception:
                    _fits = True
                if _fits:
                    _tl_line = _cand
                else:
                    _tl_lines.append(_tl_line)
                    _tl_line = _w
            if _tl_line:
                _tl_lines.append(_tl_line)
            for _tl_l in _tl_lines:
                c.drawCentredString(page_width / 2, y_pos, _tl_l)
                y_pos -= 4.5 * mm
        else:
            c.drawCentredString(page_width / 2, y_pos, _tl_text)
            y_pos -= 4.5 * mm
        y_pos -= 5 * mm

        # ── Dedication text box ────────────────────────────────────────────────────
        _dedication = getattr(config, "dedication_text", "") or ""
        if _dedication:
            _ded_fs = 8.5
            _ded_x = margin * 1.5
            _ded_w = page_width - 3 * margin
            set_font(_ded_fs)
            # Word wrap
            _ded_words = _dedication.split()
            _ded_lines, _ded_l = [], ""
            _max_ded = _ded_w - 8 * mm
            for _w in _ded_words:
                _cand = (_ded_l + " " + _w).lstrip() if _ded_l else _w
                if c.stringWidth(_cand, "DejaVuSans", _ded_fs) <= _max_ded:
                    _ded_l = _cand
                else:
                    _ded_lines.append(_ded_l)
                    _ded_l = _w
            if _ded_l:
                _ded_lines.append(_ded_l)
            _ded_lh = _ded_fs * 0.5 * mm + 1.2 * mm
            _ded_bh = len(_ded_lines) * _ded_lh + 5 * mm
            _ded_by = y_pos - _ded_bh
            # Box background
            try:
                _ded_bg = _RLColor(primary_color.red, primary_color.green, primary_color.blue, alpha=0.06)
                c.setFillColor(_ded_bg)
                c.roundRect(_ded_x, _ded_by, _ded_w, _ded_bh, 1.5 * mm, fill=1, stroke=0)
            except Exception:
                pass
            # Left accent border
            c.setFillColor(accent_color)
            c.rect(_ded_x, _ded_by, 2.5, _ded_bh, fill=1, stroke=0)
            # Text
            c.setFillColor(text_color)
            set_font(_ded_fs)
            _ded_ty = y_pos - 3 * mm
            for _dl in _ded_lines:
                c.drawString(_ded_x + 5 * mm, _ded_ty, _dl)
                _ded_ty -= _ded_lh
            y_pos = _ded_by - 8 * mm

        # ── Tips section title (UPPERCASE, letter-spaced) ─────────────────────────
        c.setFillColor(primary_color)
        set_font(8, bold=True)
        _tips_title = (config.tips_title or "").upper()
        c.drawCentredString(page_width / 2, y_pos, _tips_title)
        y_pos -= 6.5 * mm

        # ── Tips content ──────────────────────────────────────────────────────────
        c.setFillColor(text_color)
        _tfsize = max(7.0, min(float(config.tips_font_size), 11.0))
        set_font(_tfsize)
        _tips_lines = config.tips_content.strip().split("\n")
        _tip_lh = _tfsize * 0.45 * mm + 1.5 * mm
        for _tline in _tips_lines:
            _ts = _tline.strip()
            if _ts:
                c.drawString(margin * 1.5, y_pos, _ts)
                y_pos -= _tip_lh

        # ── Separator: line •••  line ─────────────────────────────────────────────
        y_pos -= 5 * mm
        if getattr(config, "show_decorative_lines", True):
            _sep_y = y_pos
            _sep_mid = page_width / 2
            _avail = page_width - 2 * margin * 1.5
            _dot_span = 6 * mm  # space for 3 dots
            _seg_len = (_avail - _dot_span) / 2
            c.setStrokeColor(border_col)
            c.setLineWidth(0.5)
            c.line(margin * 1.5, _sep_y, margin * 1.5 + _seg_len, _sep_y)
            c.line(_sep_mid + _dot_span / 2, _sep_y, margin * 1.5 + _seg_len + _dot_span + _seg_len, _sep_y)
            c.setFillColor(accent_color)
            for _di, _dx in enumerate([-2.5 * mm, 0, 2.5 * mm]):
                c.circle(_sep_mid + _dx, _sep_y, 0.7 * mm, fill=1, stroke=0)
            y_pos -= 6 * mm

        # ── Bottom section: company info (left) + QR code (right) ─────────────────
        _bottom_base = margin + 4 * mm

        # QR Code
        _qr_rendered = False
        if audio_qr_url and config.qr_enabled:
            _qr_sz = config.qr_size_mm * mm
            _qr_reader, _qr_buf = self._generate_qr_image(audio_qr_url)
            _qr_x = page_width - _qr_sz - margin
            _qr_y = _bottom_base + 3 * mm
            # White rounded box
            c.setFillColor(HexColor("#FFFFFF"))
            c.roundRect(_qr_x - 2.5 * mm, _qr_y - 2.5 * mm,
                        _qr_sz + 5 * mm, _qr_sz + 9 * mm, 2 * mm, fill=1, stroke=0)
            c.drawImage(_qr_reader, _qr_x, _qr_y, width=_qr_sz, height=_qr_sz)
            _qr_buf.close()
            _qr_rendered = True
            c.setFillColor(primary_color)
            set_font(6.5)
            c.drawCentredString(_qr_x + _qr_sz / 2, _qr_y + _qr_sz + 1.5 * mm, config.qr_label)

        # Company info (left side)
        c.setFillColor(primary_color)
        set_font(7.5, bold=True)
        _info_x = margin * 1.3
        _info_y = _bottom_base + 14 * mm
        c.drawString(_info_x, _info_y, config.company_website)
        c.setFillColor(text_color)
        set_font(7)
        _info_y -= 4.5 * mm
        c.drawString(_info_x, _info_y, config.company_email)
        if config.company_phone:
            _info_y -= 4 * mm
            c.drawString(_info_x, _info_y, config.company_phone)

        # Copyright
        c.setFillColor(HexColor("#CCCCCC") if _image_background_used else HexColor("#888888"))
        set_font(6.5)
        c.drawCentredString(page_width / 2, margin - 2 * mm, config.copyright_text)

        logger.info(
            "BACK_COVER_RENDERED",
            has_stars=config.show_stars,
            has_dedication=bool(_dedication),
            has_qr=_qr_rendered,
            has_gradient=not _image_background_used,
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
