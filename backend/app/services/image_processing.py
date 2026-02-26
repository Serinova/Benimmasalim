"""Image processing service for line-art conversion."""

import io

import cv2
import numpy as np
import structlog
from PIL import Image, ImageFilter, ImageOps

logger = structlog.get_logger()


class ImageProcessingService:
    """Service for image processing operations (primarily line-art conversion)."""

    async def convert_to_line_art(
        self,
        image_bytes: bytes,
        method: str = "canny",
        threshold_low: int = 50,
        threshold_high: int = 150,
        invert: bool = True,
    ) -> bytes:
        """
        Convert image to line-art for coloring books.

        Args:
            image_bytes: Original image bytes
            method: "canny" (recommended) or "pil_edge"
            threshold_low: Canny lower threshold
            threshold_high: Canny upper threshold
            invert: If True, white background with black lines

        Returns:
            Line-art image as PNG bytes

        Raises:
            ValueError: If method is unknown
            Exception: If conversion fails
        """
        try:
            # Load image
            img = Image.open(io.BytesIO(image_bytes))
            img_rgb = img.convert("RGB")

            if method == "canny":
                result = self._canny_edge_detection(
                    img_rgb, threshold_low, threshold_high, invert
                )
            elif method == "pil_edge":
                result = self._pil_edge_detection(img_rgb, invert)
            else:
                raise ValueError(f"Unknown line-art method: {method}")

            # Convert to PNG bytes
            output = io.BytesIO()
            result.save(output, format="PNG", optimize=True)
            logger.info(
                "Line-art conversion successful",
                method=method,
                size=f"{result.width}x{result.height}",
            )
            return output.getvalue()

        except Exception as e:
            logger.error("Line-art conversion failed", error=str(e), method=method)
            raise

    async def convert_to_line_art_ai(
        self,
        image_bytes: bytes,
        prompt: str = "Generate a clean black and white line art coloring book version of this exact image. No shading, simple outlines, white background. KEEP EXACT COMPOSITION.",
    ) -> bytes:
        """
        Convert image to native line-art using Gemini Flash image-to-image.
        """
        import base64
        import httpx
        from app.config import settings
        
        try:
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            api_key = settings.gemini_api_key
            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={api_key}'
            
            payload = {
                'contents': [{'parts': [
                    {'inlineData': {'mimeType': 'image/png', 'data': img_b64}},
                    {'text': prompt}
                ]}],
                'generationConfig': {
                    'responseModalities': ['IMAGE']
                }
            }
            
            async with httpx.AsyncClient(timeout=60) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                
                for candidate in data.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            image_data = part["inlineData"]
                            logger.info(
                                "AI Line-art conversion successful",
                                mime_type=image_data.get("mimeType"),
                            )
                            return base64.b64decode(image_data["data"])
                
                raise ValueError("No image part in Gemini response")

        except Exception as e:
            logger.error("AI Line-art conversion failed", error=str(e))
            raise

    def _canny_edge_detection(
        self, img_rgb: Image.Image, threshold_low: int, threshold_high: int, invert: bool
    ) -> Image.Image:
        """
        Use OpenCV Canny edge detection (best quality).

        Args:
            img_rgb: PIL Image in RGB mode
            threshold_low: Canny lower threshold
            threshold_high: Canny upper threshold
            invert: If True, invert for white background

        Returns:
            Line-art PIL Image
        """
        # Convert PIL to OpenCV format
        img_cv = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

        # Apply strong Gaussian blur to simplify details (kids-friendly)
        gray = cv2.GaussianBlur(gray, (9, 9), 2.5)

        # Canny edge detection
        edges = cv2.Canny(gray, threshold_low, threshold_high)

        # Morphological operations to thicken lines and simplify shapes
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Additional dilation to make lines bolder and easier to see
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Invert for white background (coloring book style)
        if invert:
            edges = cv2.bitwise_not(edges)

        # Convert back to PIL
        return Image.fromarray(edges).convert("RGB")

    def _pil_edge_detection(self, img_rgb: Image.Image, invert: bool) -> Image.Image:
        """
        Use PIL FIND_EDGES filter (faster, simpler).

        Args:
            img_rgb: PIL Image in RGB mode
            invert: If True, invert for white background

        Returns:
            Line-art PIL Image
        """
        # Apply edge detection
        edges = img_rgb.filter(ImageFilter.FIND_EDGES)
        edges_gray = edges.convert("L")

        # Increase contrast
        edges_contrast = ImageOps.autocontrast(edges_gray)

        # Threshold to binary
        threshold = 100
        edges_binary = edges_contrast.point(lambda x: 255 if x > threshold else 0)

        # Invert for white background
        if invert:
            edges_binary = ImageOps.invert(edges_binary)

        return edges_binary.convert("RGB")


# Singleton instance
image_processing_service = ImageProcessingService()
