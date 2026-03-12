"""Google Cloud Text-to-Speech service for natural Turkish narration.

Uses SSML markup to create expressive, storytelling-style narration
with pauses, emphasis, and prosody adjustments.
"""

import re

import structlog
from google.cloud import texttospeech

from app.core.rate_limit import rate_limit_retry

logger = structlog.get_logger()

# Google TTS byte limit per request (official limit: 5000 bytes)
# SSML markup adds overhead, so we use a smaller text budget
_MAX_TEXT_BYTES_PER_CHUNK = 3800  # leaves ~1200 bytes for SSML tags

# Turkish WaveNet voices — warm, natural storytelling tone
TURKISH_VOICES = {
    "female": texttospeech.VoiceSelectionParams(
        language_code="tr-TR",
        name="tr-TR-Wavenet-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    ),
    "male": texttospeech.VoiceSelectionParams(
        language_code="tr-TR",
        name="tr-TR-Wavenet-B",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
    ),
}


# ---------------------------------------------------------------------------
# SSML Conversion — turns plain text into expressive storytelling markup
# ---------------------------------------------------------------------------


def _text_to_storytelling_ssml(text: str) -> str:
    """Convert plain Turkish text to SSML with storytelling prosody.

    Adds:
    - Pauses after sentences (longer for paragraph breaks)
    - Emphasis on exclamations and questions
    - Slower pace for dramatic sentences
    - Breathing pauses at commas
    """
    # Start with the SSML wrapper + base prosody (warm, slightly slow storytelling)
    lines: list[str] = []
    lines.append("<speak>")
    lines.append('<prosody rate="0.98" pitch="-1st">')  # warm deep tone, natural pace

    paragraphs = text.split("\n\n")
    for p_idx, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue

        # Split paragraph into sentences
        sentences = _split_into_sentences(para)

        for s_idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue

            # Detect sentence type and apply appropriate prosody
            ssml_sentence = _apply_sentence_prosody(sentence)
            lines.append(ssml_sentence)

            # Add inter-sentence pause
            if s_idx < len(sentences) - 1:
                lines.append('<break time="400ms"/>')

        # Add longer pause between paragraphs (like a breath between scenes)
        if p_idx < len(paragraphs) - 1:
            lines.append('<break time="800ms"/>')

    lines.append("</prosody>")
    lines.append("</speak>")

    return "\n".join(lines)


def _apply_sentence_prosody(sentence: str) -> str:
    """Apply SSML prosody to a single sentence based on its content/punctuation."""

    # Escape XML special characters in the text content
    escaped = _xml_escape(sentence)

    # --- Exclamation → excited, slightly faster, higher pitch ---
    if sentence.rstrip().endswith("!"):
        return (
            f'<prosody rate="1.0" pitch="+1st">'
            f'<emphasis level="moderate">{escaped}</emphasis>'
            f"</prosody>"
        )

    # --- Question → curious, rising intonation (pitch naturally rises) ---
    if sentence.rstrip().endswith("?"):
        return f'<prosody rate="0.98" pitch="+0.5st">{escaped}</prosody>'

    # --- Ellipsis/dramatic pause → slower, softer ---
    if "..." in sentence or "…" in sentence:
        return f'<prosody rate="0.94" pitch="-1.5st">{escaped}</prosody>'

    # --- Dialogue (quoted text) → slightly different voice ---
    if '"' in sentence or '"' in sentence or "«" in sentence:
        # Add subtle emphasis to quoted parts
        escaped = _emphasize_dialogue(escaped)
        return escaped

    # --- Long sentence → add breathing pauses at commas ---
    if sentence.count(",") >= 2:
        escaped = _add_comma_pauses(escaped)

    # Default: use base prosody (inherited from parent <prosody> tag)
    return escaped


def _emphasize_dialogue(text: str) -> str:
    """Add emphasis to dialogue (quoted text) within a sentence."""
    # Handle Turkish quote styles: "...", «...», "..."
    patterns = [
        (r'(".*?")', r'<prosody rate="0.93" pitch="+0.5st">\1</prosody>'),
        (r"(\u201c.*?\u201d)", r'<prosody rate="0.93" pitch="+0.5st">\1</prosody>'),
        (r"(\u00ab.*?\u00bb)", r'<prosody rate="0.93" pitch="+0.5st">\1</prosody>'),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def _add_comma_pauses(text: str) -> str:
    """Add subtle pauses after commas for natural breathing rhythm."""
    return text.replace(",", ',<break time="200ms"/>')


def _xml_escape(text: str) -> str:
    """Escape XML special characters for safe SSML embedding."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Don't escape quotes — they're part of dialogue
    return text


# ---------------------------------------------------------------------------
# Text splitting
# ---------------------------------------------------------------------------


def _split_text_into_chunks(text: str, max_bytes: int = _MAX_TEXT_BYTES_PER_CHUNK) -> list[str]:
    """Split text into chunks that fit within the TTS byte limit.

    Splits on paragraph boundaries (double newline) first, then on sentence
    boundaries (period/question mark/exclamation mark + space), and finally
    on word boundaries as a last resort.

    Returns plain text chunks — SSML conversion happens per-chunk later.
    """
    # If text already fits, return as-is
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks: list[str] = []

    # First split into paragraphs
    paragraphs = text.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        candidate = (current_chunk + "\n\n" + para).strip() if current_chunk else para

        if len(candidate.encode("utf-8")) <= max_bytes:
            current_chunk = candidate
        else:
            # The candidate is too big
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Check if this single paragraph fits
            if len(para.encode("utf-8")) <= max_bytes:
                current_chunk = para
            else:
                # Need to split this paragraph into sentences
                sentences = _split_into_sentences(para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    if not current_chunk:
                        # Check if single sentence fits
                        if len(sentence.encode("utf-8")) <= max_bytes:
                            current_chunk = sentence
                        else:
                            # Extreme case: single sentence too long, split on words
                            word_chunks = _split_on_words(sentence, max_bytes)
                            chunks.extend(word_chunks[:-1])
                            current_chunk = word_chunks[-1] if word_chunks else ""
                    else:
                        candidate = current_chunk + " " + sentence
                        if len(candidate.encode("utf-8")) <= max_bytes:
                            current_chunk = candidate
                        else:
                            chunks.append(current_chunk)
                            current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using common Turkish/English punctuation."""
    # Split on sentence-ending punctuation followed by space or EOL
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p for p in parts if p.strip()]


def _split_on_words(text: str, max_bytes: int) -> list[str]:
    """Last resort: split text on word boundaries."""
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip() if current else word
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class GoogleTTSService:
    """Text-to-speech using Google Cloud TTS WaveNet (Turkish).

    Uses Application Default Credentials (ADC) — works automatically
    on Cloud Run with the service account, and locally via
    ``GOOGLE_APPLICATION_CREDENTIALS`` env var.

    Automatically splits long texts into chunks, converts each to SSML
    with storytelling prosody, synthesizes, and concatenates the audio.
    """

    def __init__(self) -> None:
        # Client is lightweight; instantiation is cheap.
        self._client = texttospeech.TextToSpeechClient()
        self._audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            # Base speaking_rate and pitch are controlled via SSML <prosody>
            # These serve as absolute fallbacks only
            speaking_rate=0.98,  # Natural narration pace
            pitch=-1.0,  # Deeper, warmer tone (fixes shrill/tiz issue)
            effects_profile_id=["headphone-class-device"],
        )

    @rate_limit_retry(service="google_tts", max_attempts=3, timeout_attempts=2)
    async def _synthesize_chunk(
        self,
        ssml: str,
        voice_params: texttospeech.VoiceSelectionParams,
    ) -> bytes:
        """Synthesize a single SSML chunk."""
        import asyncio

        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        response = await asyncio.to_thread(
            self._client.synthesize_speech,
            input=synthesis_input,
            voice=voice_params,
            audio_config=self._audio_config,
        )
        return response.audio_content

    async def text_to_speech(
        self,
        text: str,
        voice_type: str = "female",
    ) -> bytes:
        """Convert text to speech using Google Cloud TTS with storytelling SSML.

        Automatically splits long texts into chunks, wraps each in SSML
        with expressive prosody, synthesizes, and concatenates the MP3 audio.

        Args:
            text: Text to convert (Turkish).
            voice_type: ``"female"`` or ``"male"``.

        Returns:
            Audio bytes (MP3).

        Raises:
            AIServiceError: If TTS fails.
        """
        from app.core.exceptions import AIServiceError

        voice_params = TURKISH_VOICES.get(voice_type, TURKISH_VOICES["female"])

        try:
            # Split plain text into manageable chunks
            chunks = _split_text_into_chunks(text)
            logger.info(
                "Google TTS: splitting text for SSML narration",
                text_length=len(text),
                text_bytes=len(text.encode("utf-8")),
                chunk_count=len(chunks),
                voice=voice_params.name,
                chunk_sizes=[len(c.encode("utf-8")) for c in chunks],
            )

            audio_parts: list[bytes] = []
            for i, chunk in enumerate(chunks):
                # Convert plain text chunk to storytelling SSML
                ssml = _text_to_storytelling_ssml(chunk)

                # Verify SSML is within byte limits
                ssml_bytes = len(ssml.encode("utf-8"))
                if ssml_bytes > 5000:
                    logger.warning(
                        "SSML chunk exceeds 5000 bytes, falling back to plain text",
                        chunk_index=i,
                        ssml_bytes=ssml_bytes,
                    )
                    # Fallback: use plain text wrapped in minimal SSML
                    ssml = f'<speak><prosody rate="0.98" pitch="-1st">{_xml_escape(chunk)}</prosody></speak>'

                chunk_audio = await self._synthesize_chunk(ssml, voice_params)
                audio_parts.append(chunk_audio)
                logger.info(
                    "Google TTS chunk synthesized",
                    chunk_index=i + 1,
                    total_chunks=len(chunks),
                    chunk_text_bytes=len(chunk.encode("utf-8")),
                    ssml_bytes=ssml_bytes,
                    audio_bytes=len(chunk_audio),
                )

            # Concatenate all MP3 chunks (MP3 is a streaming format, simple
            # concatenation produces valid output)
            combined = b"".join(audio_parts)

            logger.info(
                "Google TTS narration generated",
                voice=voice_params.name,
                text_length=len(text),
                chunk_count=len(chunks),
                audio_size=len(combined),
                mode="ssml_storytelling",
            )

            return combined

        except AIServiceError:
            raise
        except Exception as e:
            logger.exception("Google TTS error", error=str(e))
            raise AIServiceError(
                "GoogleTTS",
                "Ses oluşturulurken bir hata oluştu.",
            )
