"""
Abstract Image Generator with Strategy Pattern.

Bu modül, farklı görsel üretim servislerini (Gemini, Fal.ai, vb.)
tek bir interface üzerinden kullanmayı sağlar.

Kullanım:
    from app.services.ai.image_generator import get_image_generator

    generator = get_image_generator()
    image_bytes = await generator.generate(prompt="A cute cat", width=512, height=512)
    image_url = await generator.generate_and_upload(prompt="...", story_id="abc123", page_num=1)

Yeni Provider Eklemek:
    1. BaseImageGenerator'dan türeyen yeni sınıf yaz (örn: FalImageGenerator)
    2. get_image_generator() fonksiyonuna koşul ekle
    3. .env dosyasına gerekli API key'i ekle
"""

import base64
from abc import ABC, abstractmethod
from enum import Enum

import httpx
import structlog

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.rate_limit import rate_limit_retry
from app.prompt_engine import compose_visual_prompt

logger = structlog.get_logger()

# =============================================================================
# FACE CONSISTENCY CONSTANTS
# =============================================================================

# Negative prompts - BLOCKS close-ups and portraits
FACE_CONSISTENCY_NEGATIVE = (
    "wrong face, different person, changed features, "
    "face distortion, blurry face, deformed face, ugly face, scary face, "
    # CRITICAL: Block close-ups and portraits
    "close up, close-up, portrait, headshot, face filling frame, "
    "bust shot, macro lens, zoomed in face, cropped composition, "
    "blurred background, bokeh background, shallow depth of field"
)

# Character consistency - RELAXED for dynamic poses
# PuLID handles face identity, we don't need aggressive text enforcement
CHARACTER_CONSISTENCY_POSITIVE = (
    ", consistent character, allow side profile, allow back view, "
    "character interacting with environment, dynamic natural pose, "
    "child exploring the scene, looking at surroundings"
)


class ImageProvider(str, Enum):
    """Desteklenen görsel üretim servisleri."""

    GEMINI = "gemini"
    GEMINI_FLASH = "gemini_flash"
    FAL = "fal"  # Faz 2'de eklenecek


class ImageSize(str, Enum):
    """Standart görsel boyutları."""

    SQUARE = "1:1"  # 512x512 veya 1024x1024
    PORTRAIT = "3:4"  # Kitap kapağı için
    LANDSCAPE = "4:3"  # Geniş sahneler için
    STORY = "9:16"  # Dikey hikaye formatı


# =============================================================================
# BASE CLASS (ABSTRACT)
# =============================================================================


class BaseImageGenerator(ABC):
    """
    Soyut görsel üretici sınıfı.

    Tüm görsel üretim servisleri bu sınıftan türemeli.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Servis adı (loglama için)."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        style_prompt: str | None = None,
        negative_prompt: str | None = None,
    ) -> bytes:
        """
        Görsel üret ve bytes olarak döndür.

        Args:
            prompt: Görsel açıklaması
            width: Genişlik (piksel)
            height: Yükseklik (piksel)
            style_prompt: Stil modifikasyonu (opsiyonel)
            negative_prompt: İstenmeyen öğeler (opsiyonel)

        Returns:
            PNG formatında görsel bytes

        Raises:
            AIServiceError: Üretim başarısız olursa
        """
        pass

    async def generate_with_aspect_ratio(
        self,
        prompt: str,
        aspect_ratio: ImageSize = ImageSize.SQUARE,
        style_prompt: str | None = None,
        negative_prompt: str | None = None,
    ) -> bytes:
        """
        Aspect ratio ile görsel üret.

        Args:
            prompt: Görsel açıklaması
            aspect_ratio: Oran (1:1, 3:4, 4:3, 9:16)
            style_prompt: Stil modifikasyonu
            negative_prompt: İstenmeyen öğeler

        Returns:
            PNG formatında görsel bytes
        """
        # Aspect ratio'yu boyutlara çevir
        width, height = self._aspect_ratio_to_size(aspect_ratio)
        return await self.generate(
            prompt=prompt,
            width=width,
            height=height,
            style_prompt=style_prompt,
            negative_prompt=negative_prompt,
        )

    def _aspect_ratio_to_size(self, aspect_ratio: ImageSize) -> tuple[int, int]:
        """Aspect ratio'yu piksel boyutlarına çevir."""
        size_map = {
            ImageSize.SQUARE: (1024, 1024),
            ImageSize.PORTRAIT: (768, 1024),
            ImageSize.LANDSCAPE: (1024, 768),
            ImageSize.STORY: (576, 1024),
        }
        return size_map.get(aspect_ratio, (1024, 1024))

    def _build_full_prompt(
        self,
        prompt: str,
        style_prompt: str | None = None,
        negative_prompt: str | None = None,
        enforce_face_consistency: bool = True,
    ) -> str:
        """Build full prompt via prompt_engine (style + quality + face consistency)."""
        full_prompt, _ = compose_visual_prompt(
            scene_description=prompt,
            is_cover=False,
            style_prompt_en=style_prompt or "",
        )
        full_prompt += (
            ", high quality illustration, children's book art style, "
            "vibrant colors, safe for children, detailed, professional artwork"
        )
        if enforce_face_consistency:
            full_prompt += CHARACTER_CONSISTENCY_POSITIVE
        avoid_list = negative_prompt if negative_prompt else FACE_CONSISTENCY_NEGATIVE
        full_prompt += f". AVOID: {avoid_list}"
        return full_prompt


# =============================================================================
# GEMINI IMPLEMENTATION (Imagen 3)
# =============================================================================


class GeminiImageGenerator(BaseImageGenerator):
    """
    Google Gemini Imagen 3 ile görsel üretimi.

    API: https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict
    """

    IMAGEN_API_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
    )

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.timeout = 90.0  # Imagen biraz yavaş olabiliyor

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment")

    @property
    def provider_name(self) -> str:
        return "Gemini Imagen 3"

    async def generate(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        style_prompt: str | None = None,
        negative_prompt: str | None = None,
    ) -> bytes:
        """Gemini Imagen 3 ile görsel üret."""

        full_prompt = self._build_full_prompt(
            prompt,
            style_prompt,
            negative_prompt,
            enforce_face_consistency=True,
        )

        # Boyutlardan aspect ratio hesapla
        aspect_ratio = self._calculate_aspect_ratio(width, height)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.IMAGEN_API_URL}?key={self.api_key}",
                    json={
                        "instances": [{"prompt": full_prompt}],
                        "parameters": {
                            "sampleCount": 1,
                            "aspectRatio": aspect_ratio,
                            "safetyFilterLevel": "block_some",
                            "personGeneration": "allow_adult",
                        },
                    },
                )
                response.raise_for_status()

                data = response.json()

                # Görsel çıkar
                if "predictions" in data and len(data["predictions"]) > 0:
                    image_b64 = data["predictions"][0].get("bytesBase64Encoded")
                    if image_b64:
                        logger.info(
                            "Image generated",
                            provider=self.provider_name,
                            prompt_length=len(prompt),
                            aspect_ratio=aspect_ratio,
                        )
                        return base64.b64decode(image_b64)

                raise AIServiceError(self.provider_name, "Görsel üretilemedi - boş yanıt")

        except httpx.TimeoutException:
            logger.error("Imagen API timeout", provider=self.provider_name)
            raise AIServiceError(
                self.provider_name,
                "Görsel üretimi zaman aşımına uğradı. Lütfen tekrar deneyin.",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Imagen API error",
                provider=self.provider_name,
                status=e.response.status_code,
                body=e.response.text[:500],
            )
            raise AIServiceError(
                self.provider_name,
                f"API hatası: {e.response.status_code}",
            )
        except Exception as e:
            logger.exception("Unexpected Imagen error", provider=self.provider_name)
            raise AIServiceError(self.provider_name, str(e))

    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """Piksel boyutlarından en yakın aspect ratio'yu hesapla."""
        ratio = width / height

        if ratio > 1.2:
            return "4:3"  # Landscape
        elif ratio < 0.8:
            return "3:4"  # Portrait
        else:
            return "1:1"  # Square


# =============================================================================
# GEMINI FLASH IMPLEMENTATION (Experimental)
# =============================================================================


class GeminiFlashImageGenerator(BaseImageGenerator):
    """
    Gemini 3.1 Flash Image (Nano Banana 2) ile görsel üretimi.

    Model: gemini-3.1-flash-image-preview (yüksek kota limitleri, 2K+ çözünürlük)
    """

    FLASH_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent"

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.timeout = 60.0

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment")

    @property
    def provider_name(self) -> str:
        return "Gemini 3.1 Flash (Nano Banana 2)"

    @rate_limit_retry(service="gemini", max_attempts=4, timeout_attempts=2)
    async def generate(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        style_prompt: str | None = None,
        negative_prompt: str | None = None,
    ) -> bytes:
        """Gemini Flash ile görsel üret."""

        full_prompt = self._build_full_prompt(
            prompt,
            style_prompt,
            negative_prompt,
            enforce_face_consistency=True,
        )

        from app.services.ai.gemini_consistent_image import _width_height_to_gemini_aspect

        gemini_aspect = _width_height_to_gemini_aspect(width, height)
        gen_config: dict = {
            "responseModalities": ["TEXT", "IMAGE"],
        }
        if gemini_aspect:
            gen_config["imageConfig"] = {
                "aspectRatio": gemini_aspect,
                "imageSize": "2K",  # Nano Banana 2: native 2K resolution
            }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.FLASH_API_URL}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": f"Generate an image. NO text, NO watermark, NO logo. {full_prompt}"}]}],
                        "generationConfig": gen_config,
                    },
                )

                # Log response for debugging
                logger.info(
                    "Flash API response",
                    status=response.status_code,
                    content_length=len(response.content),
                )

                if response.status_code != 200:
                    logger.error(
                        "Flash API error response",
                        status=response.status_code,
                        body=response.text[:500],
                    )

                response.raise_for_status()

                data = response.json()

                # Görsel çıkar
                for candidate in data.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            image_data = part["inlineData"]
                            if image_data.get("mimeType", "").startswith("image/"):
                                logger.info(
                                    "Image generated",
                                    provider=self.provider_name,
                                    prompt_length=len(prompt),
                                    mime_type=image_data.get("mimeType"),
                                )
                                return base64.b64decode(image_data["data"])

                # Log full response if no image found
                logger.error(
                    "No image in response",
                    provider=self.provider_name,
                    response_keys=list(data.keys()),
                    candidates_count=len(data.get("candidates", [])),
                )
                raise AIServiceError(self.provider_name, "Görsel üretilemedi - yanıtta görsel yok")

        except httpx.TimeoutException:
            logger.error("Flash API timeout", provider=self.provider_name)
            raise AIServiceError(
                self.provider_name,
                "Görsel üretimi zaman aşımına uğradı.",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Flash API error",
                provider=self.provider_name,
                status=e.response.status_code,
                body=e.response.text[:300],
            )
            raise AIServiceError(self.provider_name, f"API hatası: {e.response.status_code}")
        except Exception as e:
            logger.exception("Unexpected Flash error", provider=self.provider_name)
            raise AIServiceError(self.provider_name, str(e))


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def get_image_generator(
    provider: ImageProvider | str = ImageProvider.GEMINI_FLASH,
    with_face_consistency: bool = True,
) -> BaseImageGenerator:
    if isinstance(provider, str):
        provider_map = {
            "gemini": ImageProvider.GEMINI,
            "gemini_flash": ImageProvider.GEMINI_FLASH,
        }
        provider = provider_map.get(provider.lower(), ImageProvider.GEMINI_FLASH)

    if provider == ImageProvider.GEMINI:
        return GeminiImageGenerator()
    return GeminiFlashImageGenerator()

def get_face_consistent_generator() -> GeminiFlashImageGenerator:
    return GeminiFlashImageGenerator()

default_generator = get_image_generator(ImageProvider.GEMINI_FLASH, with_face_consistency=False)
