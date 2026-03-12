"""Image provider seçim testleri — routing doğruluğu ve Gemini 3.1 (Nano Banana 2) kullanım tespiti.

Hangi provider adı hangi generator sınıfını döndürüyor?
GeminiConsistentImageService hangi modeli kullanıyor?
Imagen 3.0 URL doğru mu?
"""

import pytest

from app.services.ai.gemini_consistent_image import (
    GEMINI_IMAGE_API_URL,
    GEMINI_IMAGE_MODEL,
    GeminiConsistentImageService,
)
from app.services.ai.image_generator import (
    GeminiFlashImageGenerator,
    GeminiImageGenerator,
    ImageProvider,
    get_image_generator,
)
from app.services.ai.image_provider_dispatch import (
    DEFAULT_PROVIDER_FALLBACK,
    GEMINI_PROVIDER_VALUES,
    get_image_provider_for_generation,
)


class TestImageGeneratorFactory:
    """get_image_generator() doğru sınıfı döndürür."""

    def test_default_provider_is_gemini_flash(self):
        """Argümansız çağrı GeminiFlashImageGenerator döndürür."""
        generator = get_image_generator()
        assert isinstance(generator, GeminiFlashImageGenerator), (
            "Default provider GEMINI_FLASH olmalı"
        )

    def test_gemini_flash_enum_returns_flash_generator(self):
        """ImageProvider.GEMINI_FLASH → GeminiFlashImageGenerator"""
        generator = get_image_generator(ImageProvider.GEMINI_FLASH)
        assert isinstance(generator, GeminiFlashImageGenerator)

    def test_gemini_enum_returns_imagen3_generator(self):
        """ImageProvider.GEMINI → GeminiImageGenerator (Imagen 3.0)"""
        generator = get_image_generator(ImageProvider.GEMINI)
        assert isinstance(generator, GeminiImageGenerator)

    def test_string_gemini_flash_returns_flash_generator(self):
        """String 'gemini_flash' → GeminiFlashImageGenerator"""
        generator = get_image_generator("gemini_flash")
        assert isinstance(generator, GeminiFlashImageGenerator)

    def test_string_gemini_returns_imagen3_generator(self):
        """String 'gemini' → GeminiImageGenerator (Imagen 3.0)"""
        generator = get_image_generator("gemini")
        assert isinstance(generator, GeminiImageGenerator)

    def test_unknown_string_falls_back_to_flash(self):
        """Bilinmeyen provider string → GeminiFlashImageGenerator (fallback)"""
        generator = get_image_generator("unknown_provider")
        assert isinstance(generator, GeminiFlashImageGenerator)

    def test_flash_generator_not_imagen3(self):
        """Flash ve Imagen3 farklı sınıflar."""
        flash = get_image_generator(ImageProvider.GEMINI_FLASH)
        imagen = get_image_generator(ImageProvider.GEMINI)
        assert type(flash) is not type(imagen)


class TestModelEndpoints:
    """Doğru model URL'leri kullanılıyor."""

    def test_imagen3_url_contains_correct_model(self):
        """GeminiImageGenerator Imagen 3.0 modelini kullanıyor."""
        assert "imagen-3.0-generate-002" in GeminiImageGenerator.IMAGEN_API_URL

    def test_flash_url_contains_flash_model(self):
        """GeminiFlashImageGenerator Gemini 3.1 Flash Image (Nano Banana 2) modelini kullanıyor."""
        assert "gemini-3.1-flash-image-preview" in GeminiFlashImageGenerator.FLASH_API_URL

    def test_gemini_consistent_uses_flash_model(self):
        """GeminiConsistentImageService gemini-3.1-flash-image-preview (Nano Banana 2) modelini kullanıyor.

        NOT: Bu servis referans fotoğraf + prompt birleştirdiğinden
        Gemini multimodal endpoint kullanması beklenen davranış.
        Nano Banana 2 karakter tutarlılığında çok daha iyi.
        """
        assert GEMINI_IMAGE_MODEL == "gemini-3.1-flash-image-preview", (
            "GeminiConsistentImageService 'gemini-3.1-flash-image-preview' modeline bağlı"
        )

    def test_gemini_consistent_api_url_matches_model(self):
        """API URL model adıyla tutarlı."""
        assert GEMINI_IMAGE_MODEL in GEMINI_IMAGE_API_URL


class TestProviderDispatch:
    """get_image_provider_for_generation() davranışı."""

    def test_dispatch_returns_gemini_consistent_service(self):
        """Fal kaldırıldığından her zaman GeminiConsistentImageService döner."""
        service = get_image_provider_for_generation("gemini")
        assert isinstance(service, GeminiConsistentImageService)

    def test_dispatch_gemini_flash_still_returns_consistent(self):
        """'gemini_flash' argümanı da GeminiConsistentImageService döndürür."""
        service = get_image_provider_for_generation("gemini_flash")
        assert isinstance(service, GeminiConsistentImageService)

    def test_dispatch_is_singleton(self):
        """Aynı servis instance'ı döner (connection pool paylaşılır)."""
        s1 = get_image_provider_for_generation("gemini")
        s2 = get_image_provider_for_generation("gemini")
        assert s1 is s2, "get_image_provider_for_generation() singleton olmalı"


class TestProviderConstants:
    """Provider adı sabitleri doğru tanımlanmış."""

    def test_gemini_provider_values_contains_both(self):
        assert "gemini" in GEMINI_PROVIDER_VALUES
        assert "gemini_flash" in GEMINI_PROVIDER_VALUES

    def test_default_fallback_is_gemini(self):
        """Default fallback Imagen 3.0 (gemini) olmalı — Gemini Flash değil.

        OPTIMIZASYON NOTU: Şu an DEFAULT_PROVIDER_FALLBACK = 'gemini'
        Bu, referans foto olmayan durumda Imagen 3.0 kullanıldığı anlamına gelir.
        get_image_generator() factory'si ise default olarak GEMINI_FLASH kullanıyor.
        İkisi arasındaki tutarsızlık gözlemlenmiştir.
        """
        assert DEFAULT_PROVIDER_FALLBACK == "gemini", (
            f"DEFAULT_PROVIDER_FALLBACK 'gemini' (Imagen 3.0) olmalı, "
            f"şu an: '{DEFAULT_PROVIDER_FALLBACK}'"
        )


class TestGeminiConsistentImageService:
    """GeminiConsistentImageService konfigürasyonu."""

    def test_service_can_be_instantiated_with_mock_key(self, monkeypatch):
        """Servis API key ile başarıyla örneklenir."""
        monkeypatch.setattr(
            "app.services.ai.gemini_consistent_image.settings.gemini_api_key",
            "test-key-mock",
        )
        service = GeminiConsistentImageService(api_key="test-key-mock")
        assert service.api_key == "test-key-mock"

    def test_service_timeout_default(self, monkeypatch):
        """Varsayılan timeout 90 saniye."""
        monkeypatch.setattr(
            "app.services.ai.gemini_consistent_image.settings.gemini_api_key",
            "test-key-mock",
        )
        service = GeminiConsistentImageService(api_key="test-key-mock")
        assert service.timeout == 90.0

    def test_service_raises_without_api_key(self, monkeypatch):
        """API key olmadan ValueError fırlatır."""
        monkeypatch.setattr(
            "app.services.ai.gemini_consistent_image.settings.gemini_api_key",
            "",
        )
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiConsistentImageService(api_key="")
