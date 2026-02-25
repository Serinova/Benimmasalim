"""Public audio endpoints for QR code playback."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select

from app.api.v1.deps import DbSession
from app.models.story_preview import StoryPreview
from app.services.ai.elevenlabs_service import ElevenLabsService

router = APIRouter()


@router.get("/preview/{preview_id}")
async def get_preview_audio(
    preview_id: UUID,
    db: DbSession,
) -> Response:
    """
    Generate and stream audio for a preview.
    This is a public endpoint for QR code playback.
    """
    import structlog

    logger = structlog.get_logger()

    # Get preview
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        raise HTTPException(status_code=404, detail="Önizleme bulunamadı")

    # Check if audio is enabled
    has_audio = getattr(preview, "has_audio_book", False)
    if not has_audio:
        raise HTTPException(status_code=404, detail="Bu kitap için sesli okuma aktif değil")

    # Get audio settings
    audio_type = getattr(preview, "audio_type", "system")
    audio_voice_id = getattr(preview, "audio_voice_id", None)

    # Combine all page texts
    full_story_text = ""
    if preview.story_pages:
        for page in preview.story_pages:
            if isinstance(page, dict) and page.get("text"):
                full_story_text += page["text"] + "\n\n"

    if not full_story_text.strip():
        raise HTTPException(status_code=404, detail="Hikaye metni bulunamadı")

    try:
        elevenlabs = ElevenLabsService()

        # Generate audio
        if audio_type == "cloned" and audio_voice_id:
            logger.info(
                "Generating audio with cloned voice",
                preview_id=str(preview_id),
                voice_id=audio_voice_id,
            )
            audio_bytes = await elevenlabs.text_to_speech(
                text=full_story_text,
                voice_id=audio_voice_id,
            )
        else:
            logger.info("Generating audio with system voice", preview_id=str(preview_id))
            audio_bytes = await elevenlabs.text_to_speech(
                text=full_story_text,
                voice_type="female",
            )

        # Return audio as MP3
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'inline; filename="masal_{preview.child_name}.mp3"',
                "Cache-Control": "public, max-age=86400",  # Cache for 1 day
            },
        )

    except Exception as e:
        logger.error("Audio generation failed", preview_id=str(preview_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Ses oluşturma hatası: {str(e)}")


@router.get("/preview/{preview_id}/player")
async def get_audio_player(
    preview_id: UUID,
    db: DbSession,
) -> HTMLResponse:
    """
    Return a simple HTML audio player page.
    This is useful when QR code is scanned on a phone.
    """
    # Get preview to verify it exists and get child name
    result = await db.execute(select(StoryPreview).where(StoryPreview.id == preview_id))
    preview = result.scalar_one_or_none()

    if not preview:
        return HTMLResponse(
            content="<html><body><h1>Kitap bulunamadı</h1></body></html>", status_code=404
        )

    has_audio = getattr(preview, "has_audio_book", False)
    if not has_audio:
        return HTMLResponse(
            content="<html><body><h1>Bu kitap için sesli okuma aktif değil</h1></body></html>",
            status_code=404,
        )

    # Return HTML player
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Benim Masalım - {preview.child_name}</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                max-width: 400px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 24px;
            }}
            .child-name {{
                color: #667eea;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 30px;
            }}
            .book-icon {{
                font-size: 80px;
                margin-bottom: 20px;
            }}
            audio {{
                width: 100%;
                margin: 20px 0;
            }}
            .loading {{
                color: #666;
                font-size: 14px;
            }}
            .play-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 18px;
                border-radius: 30px;
                cursor: pointer;
                margin-top: 20px;
            }}
            .play-btn:hover {{
                opacity: 0.9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="book-icon">📖</div>
            <h1>Benim Masalım</h1>
            <div class="child-name">{preview.child_name}'ın Hikayesi</div>
            <p class="loading" id="loading">Ses yükleniyor...</p>
            <audio id="audio" controls style="display: none;">
                <source src="/api/v1/audio/preview/{preview_id}" type="audio/mpeg">
                Tarayıcınız ses oynatmayı desteklemiyor.
            </audio>
            <button class="play-btn" id="playBtn" style="display: none;" onclick="playAudio()">
                ▶️ Dinle
            </button>
        </div>
        <script>
            const audio = document.getElementById('audio');
            const loading = document.getElementById('loading');
            const playBtn = document.getElementById('playBtn');
            
            audio.addEventListener('canplay', function() {{
                loading.style.display = 'none';
                audio.style.display = 'block';
                playBtn.style.display = 'inline-block';
            }});
            
            audio.addEventListener('error', function() {{
                loading.textContent = 'Ses yüklenirken hata oluştu. Lütfen tekrar deneyin.';
                loading.style.color = 'red';
            }});
            
            function playAudio() {{
                audio.play();
                playBtn.style.display = 'none';
            }}
            
            // Start loading
            audio.load();
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
