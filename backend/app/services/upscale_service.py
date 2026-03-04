"""Görsel upscale servisi — Replicate Real-ESRGAN.

Akış:
  AI üretim (~1024px) → upscale (2x/4x) → resize_to_target (3508px) → PDF

Replicate model: nightmareai/real-esrgan
  - 2x: ~$0.0012/image
  - 4x: ~$0.0023/image
  - Ortalama süre: 5-15 saniye

Fallback: replicate_api_key yoksa veya upscale_enabled=False ise
  PIL LANCZOS ile direkt resize (eski davranış).
"""

from __future__ import annotations

import asyncio
import base64
import io
import time
from typing import TYPE_CHECKING

import httpx
import structlog

from app.config import settings

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

# Replicate model version — Real-ESRGAN 4x+
_REPLICATE_ESRGAN_VERSION = "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
_REPLICATE_API_BASE = "https://api.replicate.com/v1"

# Max time to wait for upscale result (seconds)
_UPSCALE_TIMEOUT_S = 120
_POLL_INTERVAL_S = 2.0


async def upscale_image_bytes(
    image_bytes: bytes,
    upscale_factor: int = 4,
    *,
    face_enhance: bool = False,
) -> bytes:
    """Görsel byte'larını Real-ESRGAN ile upscale eder.

    Args:
        image_bytes: Upscale edilecek görsel (JPEG/PNG)
        upscale_factor: 2 veya 4 (default 4)
        face_enhance: Yüz iyileştirme (çocuk kitabı için False önerilir — aşırı işleme)

    Returns:
        Upscale edilmiş görsel byte'ları (PNG)

    Raises:
        UpscaleError: Replicate API hatası veya timeout
    """
    if not settings.upscale_enabled:
        logger.debug("Upscale disabled via config — skipping")
        return image_bytes

    if not settings.replicate_api_key:
        logger.warning("UPSCALE_SKIPPED: replicate_api_key not set — using original image")
        return image_bytes

    _start = time.monotonic()

    # Görseli base64 data URI'ye çevir
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")
    # MIME type tespiti
    _mime = "image/jpeg"
    if image_bytes[:4] == b"\x89PNG":
        _mime = "image/png"
    elif image_bytes[:4] == b"RIFF" or image_bytes[:4] == b"WEBP":
        _mime = "image/webp"
    data_uri = f"data:{_mime};base64,{img_b64}"

    headers = {
        "Authorization": f"Token {settings.replicate_api_key}",
        "Content-Type": "application/json",
    }

    # Replicate prediction oluştur
    payload = {
        "version": _REPLICATE_ESRGAN_VERSION,
        "input": {
            "image": data_uri,
            "scale": upscale_factor,
            "face_enhance": face_enhance,
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{_REPLICATE_API_BASE}/predictions",
            json=payload,
            headers=headers,
        )
        if resp.status_code not in (200, 201):
            raise UpscaleError(
                f"Replicate prediction create failed: {resp.status_code} — {resp.text[:200]}"
            )
        prediction = resp.json()

    prediction_id = prediction.get("id")
    if not prediction_id:
        raise UpscaleError("Replicate returned no prediction ID")

    logger.info(
        "UPSCALE_STARTED",
        prediction_id=prediction_id,
        upscale_factor=upscale_factor,
    )

    # Sonucu poll et
    poll_url = f"{_REPLICATE_API_BASE}/predictions/{prediction_id}"
    deadline = time.monotonic() + _UPSCALE_TIMEOUT_S

    async with httpx.AsyncClient(timeout=30.0) as client:
        while time.monotonic() < deadline:
            await asyncio.sleep(_POLL_INTERVAL_S)
            poll_resp = await client.get(poll_url, headers=headers)
            if poll_resp.status_code != 200:
                raise UpscaleError(
                    f"Replicate poll failed: {poll_resp.status_code} — {poll_resp.text[:200]}"
                )
            data = poll_resp.json()
            status = data.get("status")

            if status == "succeeded":
                output = data.get("output")
                if not output:
                    raise UpscaleError("Replicate succeeded but no output URL")
                output_url = output if isinstance(output, str) else output[0]

                # Upscale edilmiş görseli indir
                img_resp = await client.get(output_url, timeout=60.0)
                img_resp.raise_for_status()
                result_bytes = img_resp.content

                elapsed = round(time.monotonic() - _start, 2)
                logger.info(
                    "UPSCALE_DONE",
                    prediction_id=prediction_id,
                    upscale_factor=upscale_factor,
                    input_kb=len(image_bytes) // 1024,
                    output_kb=len(result_bytes) // 1024,
                    elapsed_s=elapsed,
                )
                return result_bytes

            elif status == "failed":
                error = data.get("error", "unknown error")
                raise UpscaleError(f"Replicate upscale failed: {error}")

            elif status in ("starting", "processing"):
                logger.debug("UPSCALE_POLLING", status=status, prediction_id=prediction_id)
            else:
                logger.warning("UPSCALE_UNKNOWN_STATUS", status=status)

    raise UpscaleError(f"Upscale timed out after {_UPSCALE_TIMEOUT_S}s")


async def upscale_image_bytes_safe(
    image_bytes: bytes,
    upscale_factor: int = 4,
    *,
    face_enhance: bool = False,
) -> bytes:
    """upscale_image_bytes'ın güvenli versiyonu — Replicate hata verince PIL fallback.

    Önce Replicate Real-ESRGAN dener. Başarısız olursa PIL LANCZOS ile upscale yapar
    (boyut korunur, kalite AI'dan düşük ama 1024px'te bırakmaktan iyidir).
    """
    try:
        return await upscale_image_bytes(
            image_bytes,
            upscale_factor=upscale_factor,
            face_enhance=face_enhance,
        )
    except UpscaleError as e:
        logger.warning(
            "UPSCALE_REPLICATE_FAILED_PIL_FALLBACK",
            error=str(e),
            upscale_factor=upscale_factor,
        )
        return upscale_with_pil(image_bytes, upscale_factor)
    except Exception as e:
        logger.error(
            "UPSCALE_UNEXPECTED_ERROR_PIL_FALLBACK",
            error=str(e),
            upscale_factor=upscale_factor,
        )
        return upscale_with_pil(image_bytes, upscale_factor)


def upscale_with_pil(image_bytes: bytes, upscale_factor: int) -> bytes:
    """PIL LANCZOS ile upscale — AI upscale mümkün değilse fallback.

    Kalite AI upscale'den düşüktür ama hiç upscale'den iyidir.
    """
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes))
    new_w = img.width * upscale_factor
    new_h = img.height * upscale_factor
    upscaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    upscaled.save(out, format="PNG", optimize=False)
    return out.getvalue()


class UpscaleError(Exception):
    """Upscale işlemi başarısız."""
