"""Pipeline observability — structured events for story generation pipeline.

Every order gets a single ``trace_id`` that flows through all stages:
    PASS-0 (blueprint) → PASS-1 (story) → Prompt Enhancement → Image Generation

Usage::

    from app.core.pipeline_events import PipelineTracer, mask_photo_url

    tracer = PipelineTracer.for_order(order_id=..., user_id=..., product_id=...)
    tracer.story_pass0_ok(page_count=16, blueprint_keys=[...])
    tracer.image_gen_requested(page=3, provider="fal", model="flux-pulid")
    tracer.image_gen_ok(page=3, latency_ms=4200, retry_count=1)

All events are emitted via structlog with consistent keys so they can be
queried in any log aggregator (Loki, CloudWatch, Datadog, etc.).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# PII helpers
# ---------------------------------------------------------------------------

def mask_photo_url(url: str | None) -> str:
    """Return a short SHA-256 hash prefix instead of the full URL.

    >>> mask_photo_url("https://storage.example.com/photos/abc123.jpg")
    'photo:sha256:a1b2c3d4'
    >>> mask_photo_url(None)
    'photo:none'
    """
    if not url:
        return "photo:none"
    digest = hashlib.sha256(url.encode()).hexdigest()[:8]
    return f"photo:sha256:{digest}"


def _short_id(full_uuid: str | uuid.UUID | None) -> str:
    """Shorten a UUID for log readability: first 8 hex chars."""
    if not full_uuid:
        return ""
    return str(full_uuid).replace("-", "")[:8]


# ---------------------------------------------------------------------------
# Structured event names (grep-friendly constants)
# ---------------------------------------------------------------------------

class EventName:
    STORY_PASS0_OK = "STORY_PASS0_OK"
    STORY_PASS0_FAIL = "STORY_PASS0_FAIL"
    STORY_PASS1_OK = "STORY_PASS1_OK"
    STORY_PASS1_FAIL = "STORY_PASS1_FAIL"
    PROMPT_ENHANCE_OK = "PROMPT_ENHANCE_OK"
    PROMPT_ENHANCE_FAIL = "PROMPT_ENHANCE_FAIL"
    IMAGE_GEN_REQUESTED = "IMAGE_GEN_REQUESTED"
    IMAGE_GEN_OK = "IMAGE_GEN_OK"
    IMAGE_GEN_FAIL = "IMAGE_GEN_FAIL"
    PIPELINE_START = "PIPELINE_START"
    PIPELINE_COMPLETE = "PIPELINE_COMPLETE"
    PIPELINE_FAIL = "PIPELINE_FAIL"
    VALIDATION_WARN = "VALIDATION_WARN"
    LEGACY_FALLBACK_USED = "LEGACY_FALLBACK_USED"


# ---------------------------------------------------------------------------
# Error codes (normalized, grep-friendly)
# ---------------------------------------------------------------------------

class PipelineErrorCode:
    V2_LABEL_BLOCKED = "V2_LABEL_BLOCKED"
    PAGE_COUNT_MISMATCH = "PAGE_COUNT_MISMATCH"
    ENHANCE_FAILED = "ENHANCE_FAILED"
    LEGACY_FALLBACK_USED = "LEGACY_FALLBACK_USED"
    PASS0_GEMINI_ERROR = "PASS0_GEMINI_ERROR"
    PASS1_GEMINI_ERROR = "PASS1_GEMINI_ERROR"
    PASS1_JSON_PARSE = "PASS1_JSON_PARSE"
    IMAGE_PROVIDER_ERROR = "IMAGE_PROVIDER_ERROR"
    IMAGE_TIMEOUT = "IMAGE_TIMEOUT"
    CONTENT_POLICY = "CONTENT_POLICY"
    LOCATION_CONTAMINATION = "LOCATION_CONTAMINATION"
    RATE_LIMIT = "RATE_LIMIT"
    FACE_ANALYSIS_FAIL = "FACE_ANALYSIS_FAIL"


# ---------------------------------------------------------------------------
# User-facing error messages (normalized Turkish)
# ---------------------------------------------------------------------------

USER_ERROR_MESSAGES: dict[str, str] = {
    PipelineErrorCode.RATE_LIMIT: "AI servisi şu an meşgul. Lütfen 1-2 dakika bekleyip tekrar deneyin.",
    PipelineErrorCode.CONTENT_POLICY: "Hikaye içerik politikasına uymuyor. Lütfen farklı bir senaryo deneyin.",
    PipelineErrorCode.ENHANCE_FAILED: "Hikaye oluşturuldu fakat görsel iyileştirme başarısız oldu. Tekrar deneyin.",
    PipelineErrorCode.IMAGE_PROVIDER_ERROR: "Görsel oluşturulamadı. Lütfen tekrar deneyin.",
    PipelineErrorCode.IMAGE_TIMEOUT: "Görsel oluşturma zaman aşımına uğradı. Lütfen tekrar deneyin.",
    PipelineErrorCode.V2_LABEL_BLOCKED: "Bu pipeline versiyonu desteklenmiyor.",
    PipelineErrorCode.PAGE_COUNT_MISMATCH: "Sayfa sayısı uyuşmazlığı. Lütfen tekrar deneyin.",
    PipelineErrorCode.PASS0_GEMINI_ERROR: "Hikaye planı oluşturulamadı. Lütfen tekrar deneyin.",
    PipelineErrorCode.PASS1_GEMINI_ERROR: "Hikaye oluşturulamadı. Lütfen tekrar deneyin.",
    PipelineErrorCode.PASS1_JSON_PARSE: "Hikaye formatı hatalı. Lütfen tekrar deneyin.",
    PipelineErrorCode.LOCATION_CONTAMINATION: "Hikaye konum tutarsızlığı tespit edildi. Tekrar deneyin.",
    PipelineErrorCode.FACE_ANALYSIS_FAIL: "Yüz analizi başarısız oldu ama hikaye oluşturulabilir.",
    PipelineErrorCode.LEGACY_FALLBACK_USED: "Hikaye alternatif yöntemle oluşturuldu.",
}

_FALLBACK_USER_MSG = "Hikaye oluşturulurken bir sorun oluştu. Lütfen tekrar deneyin."


def get_user_message(error_code: str) -> str:
    """Return a user-friendly Turkish message for the given error code."""
    return USER_ERROR_MESSAGES.get(error_code, _FALLBACK_USER_MSG)


# ---------------------------------------------------------------------------
# Manifest enrichment fields
# ---------------------------------------------------------------------------

@dataclass
class ManifestMeta:
    """Extra fields to append to PageManifest for traceability."""

    scenario_id: str = ""
    style_id: str = ""
    value_id: str = ""
    prompt_hash: str = ""
    seed: int | None = None
    provider: str = ""
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != ""}


def compute_prompt_hash(prompt: str) -> str:
    """SHA-256 prefix (12 hex chars) of the visual prompt for dedup / audit."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# PipelineTracer — one instance per order/generation request
# ---------------------------------------------------------------------------

@dataclass
class PipelineTracer:
    """Emits structured log events with a consistent ``trace_id``.

    Create via ``PipelineTracer.for_order(...)`` at the top of the pipeline,
    then call event methods as the pipeline progresses.
    """

    trace_id: str
    order_id: str = ""
    user_id: str = ""
    product_id: str = ""
    pipeline_version: str = "v3"
    _start_ts: float = field(default_factory=time.monotonic, repr=False)
    requested_page_count: int = 0
    used_page_count: int = 0

    @classmethod
    def for_order(
        cls,
        *,
        order_id: str | uuid.UUID | None = None,
        user_id: str | uuid.UUID | None = None,
        product_id: str | uuid.UUID | None = None,
        pipeline_version: str = "v3",
        requested_page_count: int = 0,
    ) -> PipelineTracer:
        trace_id = uuid.uuid4().hex[:16]
        return cls(
            trace_id=trace_id,
            order_id=_short_id(order_id) if order_id else "",
            user_id=_short_id(user_id) if user_id else "",
            product_id=_short_id(product_id) if product_id else "",
            pipeline_version=pipeline_version,
            requested_page_count=requested_page_count,
        )

    # ---- common context injected into every event ----

    def _ctx(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "pipeline_version": self.pipeline_version,
        }

    # ---- pipeline lifecycle ----

    def pipeline_start(
        self,
        *,
        scenario_id: str = "",
        style_id: str = "",
        child_photo_hash: str = "",
    ) -> None:
        logger.info(
            EventName.PIPELINE_START,
            **self._ctx(),
            scenario_id=_short_id(scenario_id),
            style_id=_short_id(style_id),
            requested_page_count=self.requested_page_count,
            child_photo_hash=child_photo_hash,
        )

    def pipeline_complete(
        self,
        *,
        page_count: int,
        enhancement_skipped: bool = False,
    ) -> None:
        elapsed = round((time.monotonic() - self._start_ts) * 1000, 1)
        self.used_page_count = page_count
        logger.info(
            EventName.PIPELINE_COMPLETE,
            **self._ctx(),
            requested_page_count=self.requested_page_count,
            used_page_count=page_count,
            elapsed_ms=elapsed,
            enhancement_skipped=enhancement_skipped,
        )

    def pipeline_fail(
        self,
        *,
        error_code: str,
        error: str,
        status_code: int = 500,
    ) -> None:
        elapsed = round((time.monotonic() - self._start_ts) * 1000, 1)
        logger.error(
            EventName.PIPELINE_FAIL,
            **self._ctx(),
            error_code=error_code,
            error=error[:300],
            status_code=status_code,
            requested_page_count=self.requested_page_count,
            used_page_count=self.used_page_count,
            elapsed_ms=elapsed,
        )

    # ---- PASS-0 (Blueprint) ----

    def story_pass0_ok(self, *, page_count: int, latency_ms: float = 0) -> None:
        logger.info(
            EventName.STORY_PASS0_OK,
            **self._ctx(),
            page_count=page_count,
            latency_ms=round(latency_ms, 1),
        )

    def story_pass0_fail(self, *, error: str, retry_count: int = 0) -> None:
        logger.error(
            EventName.STORY_PASS0_FAIL,
            **self._ctx(),
            error=error[:300],
            error_code=PipelineErrorCode.PASS0_GEMINI_ERROR,
            retry_count=retry_count,
        )

    # ---- PASS-1 (Story Pages) ----

    def story_pass1_ok(self, *, page_count: int, latency_ms: float = 0) -> None:
        logger.info(
            EventName.STORY_PASS1_OK,
            **self._ctx(),
            page_count=page_count,
            latency_ms=round(latency_ms, 1),
        )

    def story_pass1_fail(self, *, error: str, retry_count: int = 0) -> None:
        logger.error(
            EventName.STORY_PASS1_FAIL,
            **self._ctx(),
            error=error[:300],
            error_code=PipelineErrorCode.PASS1_GEMINI_ERROR,
            retry_count=retry_count,
        )

    # ---- Prompt Enhancement ----

    def prompt_enhance_ok(self, *, page_count: int, latency_ms: float = 0) -> None:
        logger.info(
            EventName.PROMPT_ENHANCE_OK,
            **self._ctx(),
            page_count=page_count,
            latency_ms=round(latency_ms, 1),
        )

    def prompt_enhance_fail(self, *, error: str) -> None:
        logger.error(
            EventName.PROMPT_ENHANCE_FAIL,
            **self._ctx(),
            error=error[:300],
            error_code=PipelineErrorCode.ENHANCE_FAILED,
        )

    # ---- Image Generation ----

    def image_gen_requested(
        self,
        *,
        page: int,
        provider: str,
        model: str = "",
    ) -> None:
        logger.info(
            EventName.IMAGE_GEN_REQUESTED,
            **self._ctx(),
            page=page,
            provider=provider,
            model=model,
        )

    def image_gen_ok(
        self,
        *,
        page: int,
        latency_ms: float,
        retry_count: int = 0,
        provider: str = "",
    ) -> None:
        logger.info(
            EventName.IMAGE_GEN_OK,
            **self._ctx(),
            page=page,
            latency_ms=round(latency_ms, 1),
            retry_count=retry_count,
            provider=provider,
        )

    def image_gen_fail(
        self,
        *,
        page: int,
        error: str,
        retry_count: int = 0,
        provider: str = "",
    ) -> None:
        logger.error(
            EventName.IMAGE_GEN_FAIL,
            **self._ctx(),
            page=page,
            error=error[:300],
            error_code=PipelineErrorCode.IMAGE_PROVIDER_ERROR,
            retry_count=retry_count,
            provider=provider,
        )

    # ---- Validation warnings ----

    def validation_warn(self, *, code: str, details: str = "") -> None:
        logger.warning(
            EventName.VALIDATION_WARN,
            **self._ctx(),
            validation_code=code,
            details=details[:200],
        )

    # ---- Legacy fallback ----

    def legacy_fallback(self, *, reason: str) -> None:
        logger.warning(
            EventName.LEGACY_FALLBACK_USED,
            **self._ctx(),
            error_code=PipelineErrorCode.LEGACY_FALLBACK_USED,
            reason=reason[:200],
        )

    # ---- Manifest enrichment ----

    def build_manifest_meta(
        self,
        *,
        scenario_id: str = "",
        style_id: str = "",
        value_id: str = "",
        prompt_hash: str = "",
        seed: int | None = None,
        provider: str = "",
    ) -> ManifestMeta:
        return ManifestMeta(
            scenario_id=_short_id(scenario_id),
            style_id=_short_id(style_id),
            value_id=_short_id(value_id),
            prompt_hash=prompt_hash,
            seed=seed,
            provider=provider,
            trace_id=self.trace_id,
        )


# ---------------------------------------------------------------------------
# Normalized error response builder
# ---------------------------------------------------------------------------

def build_error_response(
    *,
    error_code: str,
    trace_id: str,
    request_id: str = "",
    retry_after: int | None = None,
) -> dict[str, Any]:
    """Build a normalized error dict to return from API endpoints.

    Returns two layers:
      - ``error``: short user-friendly Turkish message
      - ``error_code`` + ``trace_id``: for admin/debug correlation
    """
    resp: dict[str, Any] = {
        "success": False,
        "error": get_user_message(error_code),
        "error_code": error_code,
        "trace_id": trace_id,
    }
    if request_id:
        resp["request_id"] = request_id
    if retry_after is not None:
        resp["retry_after"] = retry_after
    return resp
