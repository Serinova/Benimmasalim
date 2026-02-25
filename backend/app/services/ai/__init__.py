"""AI services module."""

from app.prompt_engine import FluxPromptBuilder, PromptContext
from app.services.ai.elevenlabs_service import ElevenLabsService
from app.services.ai.face_analyzer_service import FaceAnalyzerService, get_face_analyzer
from app.services.ai.face_service import FaceService
from app.services.ai.gemini_service import (
    GeminiService,
    PageContent,
    StoryResponse,
    get_gemini_service,
)

# Modüler Image Generator (Strategy Pattern)
from app.services.ai.image_generator import (
    BaseImageGenerator,
    GeminiFlashImageGenerator,
    GeminiImageGenerator,
    ImageProvider,
    ImageSize,
    default_generator,
    get_face_consistent_generator,
    get_image_generator,
)
from app.services.ai.image_provider_dispatch import (
    get_effective_ai_config,
    get_effective_image_provider_name,
    get_image_provider_for_generation,
)

__all__ = [
    # Story Generation
    "GeminiService",
    "PageContent",
    "StoryResponse",
    "get_gemini_service",
    # Face Analysis (Forensic Description for Likeness)
    "FaceAnalyzerService",
    "get_face_analyzer",
    "PromptContext",
    "FluxPromptBuilder",
    # Modular Image Generator (Recommended)
    "BaseImageGenerator",
    "GeminiImageGenerator",
    "GeminiFlashImageGenerator",
    "ImageProvider",
    "ImageSize",
    "get_image_generator",
    "get_face_consistent_generator",
    "default_generator",
    # Provider dispatch
    "get_image_provider_for_generation",
    "get_effective_ai_config",
    "get_effective_image_provider_name",
    # Other Services
    "FaceService",
    "ElevenLabsService",
]
