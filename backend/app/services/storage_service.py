"""
Storage service — unified facade over StorageProvider backends.

All callers keep using ``storage_service.<method>(...)`` as before.
Internally the work is delegated to either GCSStorageProvider or
LocalStorageProvider depending on ``STORAGE_DRIVER`` env var.
"""

from __future__ import annotations

import asyncio
import time
import uuid

import structlog

from app.config import settings
from app.services.storage_provider import (
    _DEFAULT_CT,
    GCSStorageProvider,
    LocalStorageProvider,
    StorageProvider,
)

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------
_MAX_RETRIES = 3
_BACKOFF_BASE = 2  # seconds: 2, 4, 8


def _retry_upload(fn, *args, **kwargs):
    """Call *fn* up to _MAX_RETRIES times with exponential backoff."""
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            wait = _BACKOFF_BASE ** attempt
            logger.warning(
                "Upload attempt failed, retrying",
                attempt=attempt,
                max_retries=_MAX_RETRIES,
                wait_seconds=wait,
                error=str(exc),
            )
            if attempt < _MAX_RETRIES:
                time.sleep(wait)
    raise last_exc  # type: ignore[misc]


async def _retry_upload_async(fn, *args, **kwargs):
    """Async wrapper: call *fn* with retry + async-safe sleep."""
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            wait = _BACKOFF_BASE ** attempt
            logger.warning(
                "Upload attempt failed (async), retrying",
                attempt=attempt,
                max_retries=_MAX_RETRIES,
                wait_seconds=wait,
                error=str(exc),
            )
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(wait)
    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class StorageService:
    """
    High-level storage API used throughout the application.

    Delegates all I/O to the configured ``StorageProvider``.
    """

    def __init__(self) -> None:
        self._provider: StorageProvider = self._build_provider()

    @staticmethod
    def _build_provider() -> StorageProvider:
        driver = settings.storage_driver.lower()
        if driver == "local":
            logger.info("StorageService: using LOCAL provider", path=settings.local_storage_path)
            return LocalStorageProvider(
                storage_root=settings.local_storage_path,
                base_url="http://localhost:8000",
            )
        # default: GCS
        logger.info("StorageService: using GCS provider", bucket=settings.gcs_bucket_generated)
        return GCSStorageProvider(
            project_id=settings.gcp_project_id,
            bucket_name=settings.gcs_bucket_generated,
            credentials_json=settings.gcs_credentials_json,
            credentials_path=settings.google_application_credentials,
        )

    @property
    def provider(self) -> StorageProvider:
        return self._provider

    # ------------------------------------------------------------------
    # Public API (backward-compatible signatures)
    # ------------------------------------------------------------------
    def upload_base64_image(
        self,
        base64_data: str,
        folder: str = "stories",
        filename: str | None = None,
    ) -> str:
        """Upload a base64 encoded image. Returns public URL."""
        if not filename:
            # detect extension from header
            if "," in base64_data:
                header = base64_data.split(",", 1)[0]
                ct = header.split(":")[1].split(";")[0] if ":" in header else _DEFAULT_CT
            else:
                ct = _DEFAULT_CT
            ext = ct.split("/")[1] if "/" in ct else "png"
            filename = f"{uuid.uuid4()}.{ext}"

        blob_path = f"{folder}/{filename}"
        return _retry_upload(self._provider.upload_base64, base64_data, blob_path)

    def upload_multiple_images(
        self,
        images: dict[int | str, str],
        story_id: str,
    ) -> dict[int | str, str]:
        """Upload multiple page images (base64). Returns {page_key: url}."""
        uploaded: dict[int | str, str] = {}
        for page_num, b64 in images.items():
            if not b64:
                continue
            try:
                blob_path = f"stories/{story_id}/page_{page_num}.png"
                url = _retry_upload(self._provider.upload_base64, b64, blob_path)
                uploaded[page_num] = url
            except Exception as e:
                logger.error(
                    "Failed to upload page after retries",
                    page=page_num,
                    error=str(e),
                )
                raise  # bubble up — caller must NOT fall back to base64
        return uploaded

    def delete_story_images(self, story_id: str) -> bool:
        return self._provider.delete_prefix(f"stories/{story_id}/")

    def upload_audio(
        self,
        audio_bytes: bytes,
        order_id: str,
        filename: str | None = None,
    ) -> str:
        if not filename:
            filename = f"{uuid.uuid4()}.mp3"
        blob_path = f"audio/{order_id}/{filename}"
        return _retry_upload(self._provider.upload_bytes, audio_bytes, blob_path, "audio/mpeg")

    def upload_voice_sample(
        self,
        audio_base64: str,
        order_id: str,
    ) -> tuple[str, bytes]:
        data, ct = StorageProvider._parse_base64(audio_base64)
        ext = "webm" if "webm" in ct else "mp3"
        filename = f"voice_sample_{uuid.uuid4()}.{ext}"

        # Voice samples use audio bucket — for GCS use specific bucket
        if isinstance(self._provider, GCSStorageProvider):
            blob_path = f"voice_samples/{order_id}/{filename}"
            bucket = self._provider.get_bucket_for(settings.gcs_bucket_audio)
            blob = bucket.blob(blob_path)
            blob.upload_from_string(data, content_type=ct)
            blob.make_public()
            url = blob.public_url
        else:
            blob_path = f"voice_samples/{order_id}/{filename}"
            url = self._provider.upload_bytes(data, blob_path, ct)

        return url, data

    def get_signed_url(self, blob_url: str, expiration_hours: int = 168) -> str:
        if isinstance(self._provider, GCSStorageProvider):
            return self._provider.get_signed_url(blob_url, expiration_hours)
        return blob_url  # local provider: URL is already accessible

    def delete_audio_files(self, order_id: str) -> bool:
        ok1 = self._provider.delete_prefix(f"audio/{order_id}/")
        ok2 = self._provider.delete_prefix(f"voice_samples/{order_id}/")
        return ok1 and ok2

    def upload_invoice_pdf(self, pdf_bytes: bytes, order_id: str, invoice_number: str) -> str:
        blob_path = f"invoices/{order_id}/invoice_{invoice_number}.pdf"
        return _retry_upload(self._provider.upload_bytes, pdf_bytes, blob_path, "application/pdf")

    def download_bytes(self, blob_url: str) -> bytes | None:
        """Download file bytes from storage. Returns None on failure."""
        blob_path = self._url_to_blob_path(blob_url)
        if not blob_path:
            logger.warning("download_bytes: could not extract blob path", url=blob_url[:120])
            return None
        try:
            if isinstance(self._provider, GCSStorageProvider):
                bucket = self._provider._get_bucket()
                blob = bucket.blob(blob_path)
                return blob.download_as_bytes()
            else:
                from pathlib import Path as _Path
                local_path = _Path(self._provider._root) / blob_path
                if local_path.exists():
                    return local_path.read_bytes()
                return None
        except Exception as e:
            logger.error("download_bytes: failed", blob_path=blob_path, error=str(e))
            return None

    def upload_pdf(self, pdf_bytes: bytes, order_id: str) -> str:
        filename = f"book_{order_id}.pdf"
        blob_path = f"books/{order_id}/{filename}"
        return _retry_upload(self._provider.upload_bytes, pdf_bytes, blob_path, "application/pdf")

    async def upload_generated_image(
        self,
        image_bytes: bytes,
        order_id: str,
        page_number: int,
    ) -> str:
        blob_path = f"books/{order_id}/pages/page_{page_number}.png"
        return await _retry_upload_async(
            self._provider.upload_bytes, image_bytes, blob_path, "image/png"
        )

    @staticmethod
    def _strip_exif(image_bytes: bytes) -> bytes:
        """Remove EXIF metadata (GPS, camera info) from JPEG/PNG for privacy (KVKK)."""
        try:
            import io

            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            # Create a clean copy without EXIF
            clean = Image.new(img.mode, img.size)
            clean.putdata(list(img.getdata()))
            buf = io.BytesIO()
            fmt = img.format or "JPEG"
            clean.save(buf, format=fmt, quality=95)
            return buf.getvalue()
        except Exception as exc:
            # If stripping fails, return original (don't block upload)
            logger.warning("exif_strip_failed", error=str(exc))
            return image_bytes

    def delete_file(self, file_url: str) -> bool:
        """Delete a file by its public URL (GCS or local).

        Extracts blob path from the URL and delegates to provider.delete().
        Used by KVKK cleanup to delete photos/audio from their stored URLs.
        """
        if not file_url:
            return False
        blob_path = self._url_to_blob_path(file_url)
        if not blob_path:
            logger.warning("delete_file: could not extract blob path", url=file_url[:120])
            return False
        ok = self._provider.delete(blob_path)
        if ok:
            logger.info("delete_file: deleted", blob_path=blob_path)
        return ok

    def _url_to_blob_path(self, url: str) -> str | None:
        """Convert a public URL back to a blob path.

        Handles:
          - https://storage.googleapis.com/BUCKET/path/file.ext  ->  path/file.ext
          - http://localhost:8000/api/v1/media/path/file.ext      ->  path/file.ext
        """
        if not url:
            return None

        # GCS URL pattern
        gcs_prefix = f"https://storage.googleapis.com/{settings.gcs_bucket_generated}/"
        if url.startswith(gcs_prefix):
            return url[len(gcs_prefix):]

        # Audio bucket
        gcs_audio_prefix = f"https://storage.googleapis.com/{settings.gcs_bucket_audio}/"
        if url.startswith(gcs_audio_prefix):
            return url[len(gcs_audio_prefix):]

        # Images bucket
        gcs_images_prefix = f"https://storage.googleapis.com/{settings.gcs_bucket_images}/"
        if url.startswith(gcs_images_prefix):
            return url[len(gcs_images_prefix):]

        # Generic GCS (any bucket): https://storage.googleapis.com/bucket/path
        generic_gcs = "https://storage.googleapis.com/"
        if url.startswith(generic_gcs):
            after = url[len(generic_gcs):]
            parts = after.split("/", 1)
            return parts[1] if len(parts) == 2 else None

        # Local dev URL: http://localhost:PORT/api/v1/media/path
        if "/api/v1/media/" in url:
            return url.split("/api/v1/media/", 1)[1]

        return None

    def delete_order_files(self, order_id: str) -> dict[str, bool]:
        """Delete ALL GCS files for an order (book images, PDF, audio, voice samples)."""
        results: dict[str, bool] = {}
        results["book_pages"] = self._provider.delete_prefix(f"books/{order_id}/")
        results["audio"] = self._provider.delete_prefix(f"audio/{order_id}/")
        results["voice_samples"] = self._provider.delete_prefix(f"voice_samples/{order_id}/")
        logger.info("delete_order_files: completed", order_id=order_id, results=results)
        return results

    def upload_temp_image(
        self,
        image_bytes: bytes,
        temp_id: str,
    ) -> str:
        import time as _time

        # Strip EXIF metadata before storing (KVKK privacy)
        clean_bytes = self._strip_exif(image_bytes)

        ts = int(_time.time())
        blob_path = f"temp/pulid-faces/{temp_id}_{ts}.jpg"
        return _retry_upload(self._provider.upload_bytes, clean_bytes, blob_path, "image/jpeg")


# ---------------------------------------------------------------------------
# Singleton — keeps import compatibility: ``from app.services.storage_service import storage_service``
# ---------------------------------------------------------------------------
storage_service = StorageService()
