"""ElevenLabs service for text-to-speech and voice cloning."""

import httpx
import structlog

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.rate_limit import rate_limit_retry

logger = structlog.get_logger()

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

# Default Turkish system voices
SYSTEM_VOICES = {
    "female": "21m00Tcm4TlvDq8ikWAM",  # Rachel (female)
    "male": "AZnzlk1XvdvUeBnXmlld",  # Domi (male)
}


class ElevenLabsService:
    """Service for text-to-speech using ElevenLabs."""

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.timeout = 60.0

    @rate_limit_retry(service="elevenlabs", max_attempts=2, timeout_attempts=1)
    async def text_to_speech(
        self,
        text: str,
        voice_id: str | None = None,
        voice_type: str = "female",
    ) -> bytes:
        """
        Convert text to speech.

        Args:
            text: Text to convert
            voice_id: Custom voice ID (for cloned voices)
            voice_type: "female" or "male" (for system voices)

        Returns:
            Audio bytes (MP3)

        Raises:
            AIServiceError: If TTS fails
        """
        # Use custom voice or system voice
        voice = voice_id or SYSTEM_VOICES.get(voice_type, SYSTEM_VOICES["female"])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{ELEVENLABS_API_URL}/text-to-speech/{voice}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                        },
                    },
                )
                response.raise_for_status()

                logger.info(
                    "Text-to-speech generated",
                    voice_id=voice,
                    text_length=len(text),
                )

                return response.content

        except httpx.TimeoutException:
            logger.error("ElevenLabs API timeout")
            raise AIServiceError(
                "ElevenLabs",
                "Ses oluşturma zaman aşımına uğradı. Lütfen tekrar deneyin.",
            )
        except httpx.HTTPStatusError as e:
            logger.error("ElevenLabs API error", status=e.response.status_code)
            raise AIServiceError("ElevenLabs", "Ses oluşturulurken bir hata oluştu.")
        except Exception as e:
            logger.exception("Unexpected ElevenLabs error", error=str(e))
            raise AIServiceError("ElevenLabs", "Beklenmeyen bir hata oluştu.")

    @rate_limit_retry(service="elevenlabs", max_attempts=3, timeout_attempts=2)
    async def clone_voice(
        self,
        name: str,
        audio_samples: list[bytes],
        description: str | None = None,
    ) -> str:
        """
        Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            audio_samples: List of audio file bytes (minimum 30s total)
            description: Optional description

        Returns:
            Voice ID of the cloned voice

        Raises:
            AIServiceError: If cloning fails
        """
        try:
            # Prepare multipart form data
            files = [
                ("files", (f"sample_{i}.mp3", sample, "audio/mpeg"))
                for i, sample in enumerate(audio_samples)
            ]

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{ELEVENLABS_API_URL}/voices/add",
                    headers={"xi-api-key": self.api_key},
                    data={
                        "name": name,
                        "description": description or "Cloned voice for Benim Masalım",
                    },
                    files=files,
                )
                response.raise_for_status()

                data = response.json()
                voice_id = data["voice_id"]

                logger.info("Voice cloned successfully", voice_id=voice_id, name=name)

                return voice_id

        except httpx.HTTPStatusError as e:
            logger.error("Voice cloning failed", status=e.response.status_code)
            raise AIServiceError(
                "ElevenLabs",
                "Ses klonlama başarısız oldu. Lütfen daha net bir kayıt deneyin.",
            )
        except Exception as e:
            logger.exception("Voice cloning error", error=str(e))
            raise AIServiceError("ElevenLabs", "Ses klonlama sırasında bir hata oluştu.")

    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{ELEVENLABS_API_URL}/voices/{voice_id}",
                    headers={"xi-api-key": self.api_key},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("Failed to delete voice", voice_id=voice_id, error=str(e))
            return False
