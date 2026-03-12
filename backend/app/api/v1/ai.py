"""AI service endpoints - story and image generation."""

from __future__ import annotations

import base64
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import Response
from sqlalchemy import select

from app.api.v1.deps import AdminUser, DbSession
from app.core.exceptions import (
    ValidationError,
)
from app.models.order import Order
from app.schemas.ai import (
    _ALLOWED_IMAGE_FORMATS,
    CloneVoiceDirectRequest,
    CloneVoiceRequest,
    CloneVoiceResponse,
    PreviewVoiceRequest,
    SuggestOutfitsRequest,
    SuggestOutfitsResponse,
    SystemVoiceInfo,
    TempImageUploadRequest,
    TestFaceAnalysisRequest,
    TestFalImageRequest,
    TestImageRequest,
    TestMultiViewFaceAnalysisRequest,
    TestStoryRequest,
    TestStructuredStoryRequest,
    VoiceSampleUploadRequest,
    VoiceSampleUploadResponse,
)
from app.services.ai import (
    ImageProvider,
    get_image_generator,
)
from app.services.ai.admin_story_service import (
    FALLBACK_OUTFITS_BOY,
    FALLBACK_OUTFITS_GIRL,
    FALLBACK_OUTFITS_NEUTRAL,
    run_structured_story_generation,
)

router = APIRouter()
_V3_BLOCK_MSG = "V2_LABEL_BLOCKED: expected v3"
_GENERATE_STORY_ROUTE = "/api/v1/ai/generate-story"


# =============================================================================
# FAL.AI IMAGE GENERATION ENDPOINTS
# =============================================================================


@router.post("/test-image-fal")
async def test_fal_image_generation(request: TestFalImageRequest, admin: AdminUser):
    """
    Test Fal.ai Flux image generation with optional PuLID face consistency.

    If face_photo_url is provided:
    - Uses PuLID for face identity preservation
    - id_weight controls face likeness strength (0.5-1.0)

    If clothing is provided:
    - Appends to prompt for outfit consistency

    Returns: JSON with image_url (frontend fetches image separately)
    """
    import structlog

    from app.core.database import async_session_factory
    from app.services.ai.image_provider_dispatch import (
        get_effective_ai_config,
        get_image_provider_for_generation,
    )

    logger = structlog.get_logger()

    logger.info(
        "Testing image generation (effective provider from config)",
        has_face_ref=bool(request.face_photo_url),
        has_clothing=bool(request.clothing),
        id_weight=request.id_weight,
    )

    try:
        async with async_session_factory() as db:
            ai_config = await get_effective_ai_config(db, product_id=None)
            provider_name = (
                (ai_config.image_provider or "gemini").strip().lower() if ai_config else "gemini"
            )
            if not request.face_photo_url and provider_name in ("gemini", "gemini_flash"):
                provider_name = "fal"
            service = get_image_provider_for_generation(provider_name)

        provider_label = (
            "Gemini" if provider_name in ("gemini", "gemini_flash") else "Fal.ai Flux PuLID"
        )
        _is_cover = request.is_cover or (request.page_number == 0)

        from app.services.ai.face_service import resolve_face_reference
        from app.services.storage_service import storage_service as _ss_ai
        _effective_face_url, _original_photo_url_ai, _face_embedding = await resolve_face_reference(
            request.face_photo_url or "", _ss_ai
        )

        result = await service.generate_consistent_image(
            prompt=request.prompt,
            child_face_url=_effective_face_url,
            clothing_prompt=request.clothing or "",
            style_modifier=request.style,
            width=request.width,
            height=request.height,
            id_weight=request.id_weight,
            is_cover=_is_cover,
            page_number=request.page_number,
            reference_embedding=_face_embedding,
            original_photo_url=_original_photo_url_ai,
        )
        image_url = result[0] if isinstance(result, tuple) else result
        logger.info(
            "Image generated successfully",
            image_url=(image_url[:80] + "...") if image_url else "",
            has_face_ref=bool(request.face_photo_url),
            provider=provider_name,
        )

        return {
            "success": True,
            "image_url": image_url,
            "provider": provider_label,
            "face_consistency": "enabled" if request.face_photo_url else "disabled",
        }

    except Exception as e:
        logger.exception("Image test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "provider": "Fal.ai / Gemini",
        }


# =============================================================================
# TEMP IMAGE UPLOAD
# =============================================================================


@router.post("/upload/temp-image")
async def upload_temp_image(request: TempImageUploadRequest) -> dict:
    """
    Upload a temporary image to GCS and return a public URL.

    Security:
    - Max ~15 MB (base64)
    - PIL validates actual image content (magic bytes)
    - Only JPEG/PNG/WEBP/GIF accepted
    """
    import io
    from uuid import uuid4

    import structlog
    from PIL import Image, UnidentifiedImageError

    from app.services.storage_service import StorageService

    logger = structlog.get_logger()

    try:
        image_data = request.image_base64
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        image_bytes = base64.b64decode(image_data)

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
            img_format = img.format
        except (UnidentifiedImageError, Exception):
            return {
                "success": False,
                "error": "Geçersiz görsel dosyası. Lütfen JPEG, PNG veya WEBP yükleyin.",
                "url": "",
            }

        if img_format not in _ALLOWED_IMAGE_FORMATS:
            return {
                "success": False,
                "error": f"Desteklenmeyen format: {img_format}. İzin verilen: JPEG, PNG, WEBP, GIF.",
                "url": "",
            }

        temp_id = str(uuid4())[:8]

        storage = StorageService()
        url = storage.upload_temp_image(
            image_bytes=image_bytes,
            temp_id=temp_id,
        )

        logger.info("Temp image uploaded for PuLID", temp_id=temp_id, size_kb=len(image_bytes) // 1024)

        face_quality: dict = {"detected": False, "score": 0.0, "warning": None}
        try:
            from app.services.ai.face_service import FaceService
            _face_svc = FaceService()
            _face_svc.SCORE_THRESHOLD = 0.3
            _face_svc.MIN_IMAGE_SIZE = 64
            _score, _, _ = await _face_svc.detect_and_extract(image_bytes)
            face_quality["detected"] = True
            face_quality["score"] = round(float(_score), 2)
            if _score < 0.6:
                face_quality["warning"] = "Yüz kalitesi düşük. Daha net bir fotoğraf daha iyi sonuç verir."
        except Exception:
            face_quality["warning"] = "Yüz tespit edilemedi. Yüzün net göründüğü bir fotoğraf seçin."

        return {
            "success": True,
            "url": url,
            "temp_id": temp_id,
            "face_quality": face_quality,
        }

    except Exception as e:
        logger.error("Temp image upload failed", error=str(e))
        return {
            "success": False,
            "error": "Görsel yüklenirken bir hata oluştu.",
            "url": "",
        }


# =============================================================================
# LEGACY TEST ENDPOINTS (Gemini-based)
# =============================================================================


@router.post("/test-story")
async def test_story_generation(request: TestStoryRequest, admin: AdminUser) -> dict:
    """
    Test Gemini story generation without database.
    Just to verify API is working.
    """
    import httpx

    from app.config import settings

    prompt = f"""
    Sen çocuk hikayesi yazarısın. {request.child_name} adında {request.child_age} yaşında 
    bir çocuk için "{request.scenario}" temalı kısa bir hikaye yaz.
    Hikaye 2-3 paragraf olsun, eğlenceli ve eğitici olsun.
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.gemini_api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 1024,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            story = data["candidates"][0]["content"]["parts"][0]["text"]

            return {
                "success": True,
                "child_name": request.child_name,
                "scenario": request.scenario,
                "story": story,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/test-story-structured")
async def test_structured_story_generation(
    request: TestStructuredStoryRequest, db: DbSession,
) -> dict:
    """
    Generate STRUCTURED story with visual prompts using TWO-PASS GENERATION.
    Public create flow uses this; rate-limited in middleware. Auth optional.

    TWO-PASS STRATEGY:
    ========================
    PASS 1 - "Pure Author" (gemini-1.5-pro): 100% creative focus
    PASS 2 - "Technical Director" (gemini-2.5-flash): structured JSON output

    Returns JSON with title + pages (each with text and visual_prompt).
    """
    return await run_structured_story_generation(request, db)


# =============================================================================
# FACE ANALYSIS ENDPOINTS
# =============================================================================


@router.post("/test-face-analysis")
async def test_face_analysis(request: TestFaceAnalysisRequest, admin: AdminUser) -> dict:
    """
    Test the Forensic Face Analysis Service.

    Returns:
        - basic_description: Simple description (old method)
        - forensic_description: Detailed forensic analysis (new method)
        - enhanced_description: Combined description for prompts
    """
    import structlog

    from app.services.ai.face_analyzer_service import get_face_analyzer

    logger = structlog.get_logger()

    gender_word = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )
    basic_description = f"a {request.child_age} year old {gender_word} named {request.child_name}"

    try:
        logger.info("Testing face analysis", photo_url=request.photo_url[:100])

        face_analyzer = get_face_analyzer()

        forensic_description = await face_analyzer.analyze_face(
            image_source=request.photo_url,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        enhanced_description = await face_analyzer.get_enhanced_child_description(
            image_source=request.photo_url,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        return {
            "success": True,
            "basic_description": basic_description,
            "basic_word_count": len(basic_description.split()),
            "forensic_description": forensic_description,
            "forensic_word_count": len(forensic_description.split()),
            "enhanced_description": enhanced_description,
            "enhanced_word_count": len(enhanced_description.split()),
            "improvement_factor": f"{len(enhanced_description.split()) / len(basic_description.split()):.1f}x more detail",
        }

    except Exception as e:
        logger.exception("Face analysis test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "basic_description": basic_description,
        }


@router.post("/test-face-analysis-multi")
async def test_multi_view_face_analysis(request: TestMultiViewFaceAnalysisRequest, admin: AdminUser) -> dict:
    """
    Test Multi-View Face Analysis (IMPROVED ACCURACY).

    Analyzes MULTIPLE photos of the same child for higher consistency.
    """
    import structlog

    from app.services.ai.face_analyzer_service import get_face_analyzer

    logger = structlog.get_logger()

    gender_word = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )
    basic_description = f"a {request.child_age} year old {gender_word} named {request.child_name}"

    try:
        logger.info(
            "Testing multi-view face analysis",
            photo_count=len(request.photo_urls),
        )

        face_analyzer = get_face_analyzer()

        single_description = await face_analyzer.analyze_face(
            image_source=request.photo_urls[0],
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        multi_description = await face_analyzer.analyze_multiple_photos(
            image_sources=request.photo_urls,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        enhanced_multi = await face_analyzer.get_enhanced_child_description_multi(
            image_sources=request.photo_urls,
            child_name=request.child_name,
            child_age=request.child_age,
            child_gender=request.child_gender,
        )

        return {
            "success": True,
            "photo_count": len(request.photo_urls),
            "basic_description": basic_description,
            "single_photo_description": single_description,
            "single_photo_word_count": len(single_description.split()),
            "multi_view_description": multi_description,
            "multi_view_word_count": len(multi_description.split()),
            "enhanced_multi_description": enhanced_multi,
            "enhanced_word_count": len(enhanced_multi.split()),
            "improvement": f"Multi-view provides {len(multi_description.split()) - len(single_description.split())} more words of detail",
        }

    except Exception as e:
        logger.exception("Multi-view face analysis test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "photo_count": len(request.photo_urls),
        }


# =============================================================================
# LEGACY GEMINI IMAGE ENDPOINTS
# =============================================================================


@router.post("/test-image")
async def test_image_generation(request: TestImageRequest, admin: AdminUser):
    """
    Test Gemini Imagen generation.
    Returns the generated image directly.
    """
    import httpx

    from app.config import settings
    from app.prompt_engine import compose_visual_prompt

    full_prompt, _ = compose_visual_prompt(
        f"{request.prompt}, {request.style}",
        template_vars=None,
        is_cover=False,
        style_text="",
        style_negative="",
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={settings.gemini_api_key}",
                json={
                    "instances": [{"prompt": full_prompt}],
                    "parameters": {
                        "sampleCount": 1,
                        "aspectRatio": "1:1",
                        "safetyFilterLevel": "block_some",
                    },
                },
            )

            if response.status_code == 200:
                data = response.json()
                if "predictions" in data and len(data["predictions"]) > 0:
                    image_b64 = data["predictions"][0].get("bytesBase64Encoded")
                    if image_b64:
                        image_bytes = base64.b64decode(image_b64)
                        return Response(
                            content=image_bytes,
                            media_type="image/png",
                            headers={"Content-Disposition": "inline; filename=generated.png"},
                        )

            return {
                "success": False,
                "error": f"Imagen API returned {response.status_code}",
                "details": response.text[:500],
                "note": "Imagen 3 requires billing enabled on Google Cloud. Try Gemini 2.0 Flash instead.",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/test-image-flash")
async def test_image_generation_flash(request: TestImageRequest, db: DbSession, admin: AdminUser):
    """
    Test image generation with Gemini 2.0 Flash.

    Supports dynamic resolution from product template or explicit mm dimensions.
    """

    from app.models.book_template import PageTemplate
    from app.models.product import Product
    from app.utils.resolution_calc import (
        DEFAULT_GENERATION_A4_LANDSCAPE,
        calculate_generation_params_from_mm,
        resize_image_bytes_to_target,
    )

    width, height = DEFAULT_GENERATION_A4_LANDSCAPE
    target_width = None
    target_height = None

    try:
        if request.product_id:
            import structlog

            logger = structlog.get_logger()
            logger.info(f"Looking up product: {request.product_id}")

            product = await db.get(Product, UUID(request.product_id))
            if product:
                logger.info(
                    f"Found product: {product.name}, inner_template_id={product.inner_template_id}"
                )
                if product.inner_template_id:
                    template = await db.get(PageTemplate, product.inner_template_id)
                    if template:
                        logger.info(
                            f"Found template: {template.page_width_mm}x{template.page_height_mm}mm, bleed={template.bleed_mm}mm"
                        )
                        from app.utils.resolution_calc import get_effective_generation_params
                        params = get_effective_generation_params(template)
                        width = params["generation_width"]
                        height = params["generation_height"]
                        target_width = params["target_width"]
                        target_height = params["target_height"]
                    else:
                        logger.warning(f"Template not found for id: {product.inner_template_id}")
                else:
                    logger.warning("Product has no inner_template_id")
            else:
                logger.warning(f"Product not found: {request.product_id}")

        elif request.page_width_mm and request.page_height_mm:
            from app.utils.resolution_calc import A4_LANDSCAPE_HEIGHT_MM, A4_LANDSCAPE_WIDTH_MM
            _pw = request.page_width_mm
            _ph = request.page_height_mm
            if _pw < _ph:
                _pw, _ph = A4_LANDSCAPE_WIDTH_MM, A4_LANDSCAPE_HEIGHT_MM
            params = calculate_generation_params_from_mm(
                _pw,
                _ph,
                request.bleed_mm,
            )
            width = params["generation_width"]
            height = params["generation_height"]
            target_width = params["target_width"]
            target_height = params["target_height"]

        generator = get_image_generator(ImageProvider.GEMINI_FLASH)

        image_bytes = await generator.generate(
            prompt=request.prompt,
            style_prompt=request.style,
            width=width,
            height=height,
        )

        if target_width and target_height:
            image_bytes = resize_image_bytes_to_target(
                image_bytes,
                target_width,
                target_height,
            )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=generated.png",
                "X-Provider": generator.provider_name,
                "X-Target-Width": str(target_width or width),
                "X-Target-Height": str(target_height or height),
            },
        )

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": "Gemini Flash (Modular Generator)",
        }


@router.post("/test-image-modular")
async def test_image_modular(
    request: TestImageRequest,
    admin: AdminUser,
    provider: str = "gemini_flash",
):
    """
    Test image generation with MODULAR GENERATOR.

    Supports: gemini_flash (default), gemini (Imagen 3), fal (Fal.ai Flux).
    """
    try:
        generator = get_image_generator(provider, with_face_consistency=False)

        from app.utils.resolution_calc import DEFAULT_GENERATION_A4_LANDSCAPE
        _w, _h = DEFAULT_GENERATION_A4_LANDSCAPE
        image_bytes = await generator.generate(
            prompt=request.prompt,
            style_prompt=request.style,
            width=_w,
            height=_h,
        )

        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": "inline; filename=generated.png",
                "X-Provider": generator.provider_name,
            },
        )

    except NotImplementedError as e:
        return {
            "success": False,
            "error": str(e),
            "note": "Bu provider henüz aktif değil",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": provider,
        }


# =============================================================================
# AUDIO / VOICE ENDPOINTS
# =============================================================================


@router.get("/system-voices", response_model=list[SystemVoiceInfo])
async def get_system_voices() -> list[SystemVoiceInfo]:
    """Get available system voices for audio book."""
    return [
        SystemVoiceInfo(
            id="female",
            name="Kadin Sesi",
            gender="female",
            description="Sicak ve yumusak bir kadin sesi",
        ),
        SystemVoiceInfo(
            id="male",
            name="Erkek Sesi",
            gender="male",
            description="Guvenilir ve sakin bir erkek sesi",
        ),
    ]


@router.post("/upload-voice-sample", response_model=VoiceSampleUploadResponse)
async def upload_voice_sample(request: VoiceSampleUploadRequest) -> VoiceSampleUploadResponse:
    """
    Upload a voice sample for cloning.
    Accepts base64 encoded audio (webm from browser recording or mp3).
    """
    import structlog

    from app.services.storage_service import storage_service

    logger = structlog.get_logger()

    try:
        order_id = request.order_id or "temp"
        sample_url, audio_bytes = storage_service.upload_voice_sample(
            audio_base64=request.audio_base64,
            order_id=order_id,
        )

        duration_estimate = len(audio_bytes) / 16000

        logger.info(
            "Voice sample uploaded",
            sample_url=sample_url,
            size_bytes=len(audio_bytes),
            duration_estimate=duration_estimate,
        )

        return VoiceSampleUploadResponse(
            sample_url=sample_url,
            duration_seconds=duration_estimate,
            message="Ses ornegi basariyla yuklendi",
        )

    except Exception as e:
        logger.error("Voice sample upload failed", error=str(e))
        raise ValidationError(f"Ses ornegi yuklenemedi: {str(e)}")


@router.post("/clone-voice", response_model=CloneVoiceResponse)
async def clone_voice(request: CloneVoiceRequest, db: DbSession) -> CloneVoiceResponse:
    """Clone a voice from uploaded sample using ElevenLabs."""
    import httpx
    import structlog

    from app.services.ai.elevenlabs_service import ElevenLabsService

    logger = structlog.get_logger()
    elevenlabs = ElevenLabsService()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(request.sample_url)
            response.raise_for_status()
            audio_bytes = response.content

        voice_id = await elevenlabs.clone_voice(
            name=request.voice_name,
            audio_samples=[audio_bytes],
            description=f"Cloned voice for Benim Masalim - {request.voice_name}",
        )

        if request.order_id:
            result = await db.execute(select(Order).where(Order.id == request.order_id))
            order = result.scalar_one_or_none()
            if order:
                order.audio_voice_id = voice_id
                order.audio_type = "cloned"
                await db.commit()

        logger.info(
            "Voice cloned successfully",
            voice_id=voice_id,
            voice_name=request.voice_name,
        )

        return CloneVoiceResponse(voice_id=voice_id, message="Ses basariyla klonlandi")

    except Exception as e:
        logger.error("Voice cloning failed", error=str(e))
        raise ValidationError(f"Ses klonlama basarisiz: {str(e)}")


@router.post("/clone-voice-direct", response_model=CloneVoiceResponse)
async def clone_voice_direct(request: CloneVoiceDirectRequest, db: DbSession) -> CloneVoiceResponse:
    """Clone a voice directly from base64 audio (without GCS upload)."""
    import base64 as _b64

    import structlog

    from app.services.ai.elevenlabs_service import ElevenLabsService

    logger = structlog.get_logger()
    elevenlabs = ElevenLabsService()

    try:
        audio_base64 = request.audio_base64
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",", 1)[1]

        audio_bytes = _b64.b64decode(audio_base64)

        logger.info(
            "Starting direct voice cloning",
            voice_name=request.voice_name,
            audio_size=len(audio_bytes),
        )

        voice_id = await elevenlabs.clone_voice(
            name=request.voice_name,
            audio_samples=[audio_bytes],
            description=f"Cloned voice for Benim Masalim - {request.voice_name}",
        )

        if request.order_id:
            result = await db.execute(select(Order).where(Order.id == request.order_id))
            order = result.scalar_one_or_none()
            if order:
                order.audio_voice_id = voice_id
                order.audio_type = "cloned"
                await db.commit()

        logger.info(
            "Voice cloned successfully (direct)",
            voice_id=voice_id,
            voice_name=request.voice_name,
        )

        return CloneVoiceResponse(voice_id=voice_id, message="Ses basariyla klonlandi")

    except Exception as e:
        logger.error("Direct voice cloning failed", error=str(e))
        raise ValidationError(f"Ses klonlama basarisiz: {str(e)}")


@router.post("/preview-system-voice")
async def preview_system_voice(request: PreviewVoiceRequest) -> Response:
    """Preview a system voice with sample text. Returns audio/mpeg (MP3) directly."""
    import structlog

    from app.services.ai.elevenlabs_service import ElevenLabsService

    logger = structlog.get_logger()
    elevenlabs = ElevenLabsService()

    try:
        preview_text = request.text[:200] if len(request.text) > 200 else request.text

        if request.voice_type in ("female", "male"):
            audio_bytes = await elevenlabs.text_to_speech(
                text=preview_text,
                voice_type=request.voice_type,
            )
        else:
            audio_bytes = await elevenlabs.text_to_speech(
                text=preview_text,
                voice_id=request.voice_type,
            )

        logger.info(
            "Voice preview generated",
            voice_type=request.voice_type,
            text_length=len(preview_text),
            audio_size=len(audio_bytes),
        )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=preview.mp3"},
        )

    except Exception as e:
        logger.error("Voice preview failed", error=str(e))
        raise ValidationError(f"Ses onizleme basarisiz: {str(e)}")


# =============================================================================
# OUTFIT SUGGESTION ENDPOINT
# =============================================================================


@router.post("/suggest-outfits", response_model=SuggestOutfitsResponse)
async def suggest_outfits(
    request: SuggestOutfitsRequest,
    db: DbSession,
) -> SuggestOutfitsResponse:
    """
    Generate 6 AI-powered outfit suggestions based on child info, scenario & style.
    Falls back to pre-defined outfits if Gemini call fails.
    """
    import structlog

    from app.config import settings
    from app.models.scenario import Scenario

    logger = structlog.get_logger()

    scenario_name = "macera"
    if request.scenario_id:
        try:
            scenario_obj = await db.get(Scenario, UUID(request.scenario_id))
            if scenario_obj:
                scenario_name = scenario_obj.name or "macera"
        except Exception:
            pass

    style_hint = ""
    if request.visual_style_id:
        try:
            from app.models.scenario import VisualStyle

            vs = await db.get(VisualStyle, UUID(request.visual_style_id))
            if vs:
                style_hint = f" Görsel stil: {vs.name or ''}."
        except Exception:
            pass

    gender_en = (
        "boy"
        if request.child_gender == "erkek"
        else "girl"
        if request.child_gender == "kiz"
        else "child"
    )

    prompt = (
        f"You are a children's book illustrator. "
        f"Suggest outfit options for a {request.child_age}-year-old {gender_en} "
        f"in a '{scenario_name}' themed storybook.{style_hint}\n\n"
        f"RULES:\n"
        f"- Return exactly 6 different outfit suggestions.\n"
        f"- Each suggestion must include: top, bottom, footwear.\n"
        f"- Outfits must match the story theme.\n"
        f"- Child-appropriate clothing ONLY.\n"
        f"- Each suggestion in ENGLISH, short and clear.\n"
        f"- Return ONLY a JSON array, no other text.\n\n"
        f'Example: ["red jacket, blue pants, white sneakers", ...]\n\n'
        f"Generate 6 suggestions now:"
    )

    try:
        import json

        import httpx

        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 1024,
            },
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{api_url}?key={settings.gemini_api_key}",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()

        outfits = json.loads(text)

        if isinstance(outfits, list) and len(outfits) >= 6:
            from app.prompt_engine import normalize_clothing_description

            clean: list[str] = [
                normalize_clothing_description(str(o)) for o in outfits[:6] if str(o).strip()
            ]
            if len(clean) >= 6:
                logger.info("AI outfit suggestions generated", count=len(clean))
                return SuggestOutfitsResponse(outfits=clean[:6])

    except Exception as e:
        logger.warning("AI outfit suggestion failed, using fallbacks", error=str(e))

    if request.child_gender == "erkek":
        fallback = FALLBACK_OUTFITS_BOY
    elif request.child_gender == "kiz":
        fallback = FALLBACK_OUTFITS_GIRL
    else:
        fallback = FALLBACK_OUTFITS_NEUTRAL

    return SuggestOutfitsResponse(outfits=fallback)
