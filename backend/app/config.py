"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Proje kök .env — cwd'den bağımsız, restart sonrası da aynı kaynak kullanılır
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ROOT_ENV = _PROJECT_ROOT / ".env"
_ROOT_ENV_LOCAL = _PROJECT_ROOT / ".env.local"

# Dosya sırası: pydantic-settings'de listedeki son dosya öncelikli (dict.update)
# .env.local varsa en sona koy → lokal geliştirme değerleri .env'yi override eder
_env_files: list[str] = [".env", str(_ROOT_ENV)]
if _ROOT_ENV_LOCAL.exists():
    _env_files.append(str(_ROOT_ENV_LOCAL))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Sıra: cwd .env < kök .env < .env.local — son dosya override eder
        env_file=_env_files,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: Literal["development", "staging", "production", "testing"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)

    # Security
    webhook_secret: str = ""  # Shared secret for webhook signature verification
    behind_proxy: bool = False  # True when behind a trusted reverse proxy (Cloud Run, nginx)

    # Frontend URL (for email confirmation links etc.)
    frontend_url: str = "http://localhost:3000"

    # Database (str to support Cloud SQL Unix socket URLs with empty host)
    database_url: str
    # Connection pool sizing — tuned for multi-worker deployment:
    #   4 Gunicorn workers × (5 + 3) = 32 backend connections
    #   + ARQ workers × (5 + 3) = ~8-40 connections
    #   Total ≤ 72 (well under Cloud SQL 100 limit)
    db_pool_size: int = 5
    db_max_overflow: int = 3
    db_echo: bool = False

    # Redis
    redis_url: RedisDsn = "redis://localhost:6379/0"  # type: ignore

    # Storage driver: "gcs" for Google Cloud Storage, "local" for local filesystem (dev)
    storage_driver: str = "gcs"
    local_storage_path: str = "/app/media"

    # Google Cloud
    gcp_project_id: str = ""
    gcs_bucket_raw: str = "benimmasalim-raw-uploads"
    gcs_bucket_generated: str = "benimmasalim-generated-books"
    gcs_bucket_audio: str = "benimmasalim-audio-files"
    gcs_bucket_images: str = "benimmasalim-images"
    gcs_credentials_json: str = ""  # JSON string of service account credentials
    google_application_credentials: str = ""  # Path to service account JSON file

    # AI APIs
    gemini_api_key: str = ""
    # Comma-separated extra keys for round-robin rotation under load
    gemini_api_keys_extra: str = ""  # e.g. "key2,key3"
    fal_api_keys_extra: str = ""  # e.g. "key2,key3"
    # TWO-PASS GENERATION: Different models for different tasks
    # gemini-2.5-flash: default model, equipped to handle reasoning tokens
    gemini_story_model: str = "gemini-2.5-flash"  # PASS 0+1: Blueprint + Pages (JSON output)
    gemini_technical_model: str = "gemini-2.5-flash"  # PASS 2: Technical Director (JSON output)
    gemini_model: str = "gemini-2.5-flash"  # Default/legacy
    gemini_story_temperature: float = 0.92  # Higher = more creative, emotional stories
    gemini_scene_temperature: float = 0.7  # For scene descriptions
    # Book pipeline: V3 only (single source of truth).
    book_pipeline_version: Literal["3"] = "3"
    use_blueprint_pipeline: bool = False  # Ignored when book_pipeline_version=3 (V3 always on)
    fal_api_key: str = ""
    elevenlabs_api_key: str = ""
    replicate_api_key: str = ""  # For Real-ESRGAN upscaling via Replicate
    upscale_enabled: bool = True  # Set False to skip upscale (fallback to LANCZOS)

    # Payment (Iyzico)
    iyzico_api_key: str = ""
    iyzico_secret_key: str = ""
    iyzico_base_url: str = "https://sandbox-api.iyzipay.com"

    # JWT Auth
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 120  # 2 saat — kısa ömür, refresh token ile uzatılır
    jwt_refresh_token_expire_days: int = 7

    # OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # KVKK
    kvkk_retention_days: int = 30
    auto_delete_enabled: bool = True

    # Rate Limiting (Application Level)
    rate_limit_draft: int = 50  # hikaye oluşturma / saat / IP (misafir); admin/editor muaf
    rate_limit_order: int = 10  # per hour per user
    rate_limit_login: int = 5  # per 15 min per IP
    rate_limit_trial_create: int = 15  # trials/create per hour per IP
    rate_limit_trial_preview: int = 20  # trials/generate-preview per hour per IP
    rate_limit_generate_story_cover: int = 30  # generate-story and generate-cover per hour per IP

    # External API Rate Limits (Requests Per Minute)
    gemini_rpm_limit: int = 600  # Gemini API RPM limit - artırıldı (50+ kullanıcı için)
    fal_rpm_limit: int = 100  # Fal.ai API RPM limit
    elevenlabs_rpm_limit: int = 50  # ElevenLabs API RPM limit

    # Image Generation Concurrency (scaled for 100 concurrent users)
    image_concurrency: int = 5  # Max parallel image generations per job
    trial_concurrency_slots: int = 8  # Semaphore slots for trial background tasks
    order_concurrency_slots: int = 4  # Semaphore slots for order background tasks

    # Rate Limit Retry Configuration
    rate_limit_backoff_min: int = 5  # Min backoff seconds for 429
    rate_limit_backoff_max: int = 60  # Max backoff seconds for 429
    rate_limit_circuit_threshold: int = 8  # Consecutive 429s to trip circuit
    rate_limit_circuit_reset: int = 120  # Circuit breaker reset time (seconds)

    # Invoice company info (used in PDF template)
    invoice_company_name: str = "Benim Masalım"
    invoice_company_address: str = ""
    invoice_company_tax_id: str = ""
    invoice_company_tax_office: str = ""
    invoice_company_phone: str = ""
    invoice_company_email: str = ""
    invoice_token_salt: str = ""  # falls back to secret_key[:32] if empty
    invoice_vat_rate: float = 10.0   # KDV oranı (%) — Türkiye'de fiziksel kitap: %10
    invoice_vat_label: str = "KDV"   # Faturada gösterilecek vergi etiketi

    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Benim Masalim"
    # Development: Override ALL emails to go to this address (leave empty in production)
    dev_email_override: str = ""

    # Monitoring
    sentry_dsn: str = ""
    log_level: str = "INFO"

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure async driver is used."""
        if v and "postgresql://" in v and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    @field_validator("jwt_secret_key", mode="after")
    @classmethod
    def validate_jwt_secret_strength(cls, v: str) -> str:
        """Reject weak/predictable JWT secrets in production."""
        weak_patterns = ["dev-", "test-", "secret", "change-me", "minimum", "example"]
        import os
        if os.getenv("APP_ENV", "development") == "production":
            if any(p in v.lower() for p in weak_patterns):
                raise ValueError(
                    "JWT_SECRET_KEY is too weak for production! "
                    "Generate with: openssl rand -hex 64"
                )
            if len(v) < 64:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 64 characters in production"
                )
        return v

    @field_validator("secret_key", mode="after")
    @classmethod
    def validate_secret_key_strength(cls, v: str) -> str:
        """Reject weak SECRET_KEY in production."""
        import os
        weak = ["dev-", "test-", "secret", "change-me", "example"]
        if os.getenv("APP_ENV", "development") == "production":
            if any(p in v.lower() for p in weak):
                raise ValueError(
                    "SECRET_KEY is too weak for production! "
                    "Generate with: openssl rand -hex 64"
                )
            if len(v) < 64:
                raise ValueError("SECRET_KEY must be at least 64 characters in production")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self.app_env == "testing"

    def validate_prod_readiness(self) -> tuple[list[str], list[str]]:
        """Return (fatal_errors, warnings) for production configuration.

        Call this at startup when ``is_production`` is True.
        Fatal errors should block startup; warnings are logged but non-blocking.
        """
        fatal: list[str] = []
        warn: list[str] = []

        # ── Debug flags (FATAL) ──────────────────────────────────
        if self.debug:
            fatal.append(
                "DEBUG is True — Swagger docs exposed, "
                "AI prompts saved to DB, error details may leak"
            )
        if self.db_echo:
            fatal.append("DB_ECHO is True — all SQL queries logged (performance + leak risk)")

        # ── Email override (FATAL) ────────────────────────────────
        if self.dev_email_override:
            fatal.append(
                f"DEV_EMAIL_OVERRIDE is set ({self.dev_email_override}) — "
                "ALL customer emails will go to this address!"
            )

        # ── Frontend URL (FATAL) ──────────────────────────────────
        if "localhost" in self.frontend_url or "127.0.0.1" in self.frontend_url:
            fatal.append(
                f"FRONTEND_URL is localhost ({self.frontend_url}) — "
                "confirmation emails and payment callbacks will break"
            )

        # ── Storage (FATAL) ───────────────────────────────────────
        if self.storage_driver == "local":
            fatal.append("STORAGE_DRIVER is 'local' — files stored on ephemeral disk, not GCS")

        # ── Secrets (WARNING) ─────────────────────────────────────
        if not self.webhook_secret:
            warn.append("WEBHOOK_SECRET is empty — webhook signature verification will fail")

        # ── Payment (WARNING) ─────────────────────────────────────
        if "sandbox" in self.iyzico_base_url:
            warn.append(
                f"IYZICO_BASE_URL is sandbox ({self.iyzico_base_url}) — "
                "real payments will NOT be collected!"
            )
        if not self.iyzico_api_key or not self.iyzico_secret_key:
            warn.append("IYZICO_API_KEY / IYZICO_SECRET_KEY is empty — payments disabled")

        # ── AI API Keys (WARNING) ─────────────────────────────────
        if not self.gemini_api_key:
            warn.append("GEMINI_API_KEY is empty — story generation will fail")
        if not self.fal_api_key:
            warn.append("FAL_API_KEY is empty — image generation will fail")

        # ── Email (WARNING) ───────────────────────────────────────
        if not self.smtp_user or not self.smtp_password:
            warn.append("SMTP_USER / SMTP_PASSWORD is empty — emails will fail")

        # ── Proxy / Infra (WARNING) ───────────────────────────────
        if not self.behind_proxy:
            warn.append(
                "BEHIND_PROXY is False — rate limiter will use wrong client IP "
                "behind Cloud Run / nginx"
            )

        # ── Monitoring (WARNING) ──────────────────────────────────
        if not self.sentry_dsn:
            warn.append("SENTRY_DSN is empty — unhandled errors will go unnoticed")

        return fatal, warn


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore


settings = get_settings()
