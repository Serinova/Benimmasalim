"""
Storage provider abstraction for file uploads.

Supports GCS (production) and local filesystem (development).
Configured via STORAGE_DRIVER env var: "gcs" | "local"
"""

from __future__ import annotations

import base64
import os
import shutil
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

_DEFAULT_CT = "image/png"


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class StorageProvider(ABC):
    """Interface for all storage backends."""

    @abstractmethod
    def upload_bytes(
        self,
        data: bytes,
        blob_path: str,
        content_type: str = _DEFAULT_CT,
    ) -> str:
        """Upload raw bytes. Returns public/accessible URL."""
        ...

    @abstractmethod
    def upload_base64(
        self,
        base64_data: str,
        blob_path: str,
    ) -> str:
        """Upload base64 encoded data. Returns public/accessible URL."""
        ...

    @abstractmethod
    def delete(self, blob_path: str) -> bool:
        """Delete a single object. Returns True on success."""
        ...

    @abstractmethod
    def delete_prefix(self, prefix: str) -> bool:
        """Delete all objects under *prefix*. Returns True on success."""
        ...

    @abstractmethod
    def get_url(self, blob_path: str) -> str:
        """Return the public/accessible URL for *blob_path*."""
        ...

    # ---- helpers (shared) ------------------------------------------------
    @staticmethod
    def _parse_base64(raw: str) -> tuple[bytes, str]:
        """Strip optional data-URL header, return (bytes, content_type)."""
        if "," in raw:
            header, data = raw.split(",", 1)
            ct = header.split(":")[1].split(";")[0] if ":" in header else "application/octet-stream"
        else:
            data = raw
            ct = "application/octet-stream"
        return base64.b64decode(data), ct


# ---------------------------------------------------------------------------
# GCS implementation
# ---------------------------------------------------------------------------
class GCSStorageProvider(StorageProvider):
    """Google Cloud Storage backend."""

    def __init__(
        self,
        project_id: str,
        bucket_name: str,
        credentials_json: str = "",
        credentials_path: str = "",
    ) -> None:
        self._project_id = project_id
        self._bucket_name = bucket_name
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path
        self._client = None
        self._bucket = None

    # -- lazy init ---------------------------------------------------------
    def _get_client(self):
        if self._client is not None:
            return self._client

        import json as _json

        from google.cloud import storage as _storage
        from google.oauth2 import service_account as _sa

        creds = None

        if self._credentials_json:
            info = _json.loads(self._credentials_json)
            creds = _sa.Credentials.from_service_account_info(info)
            logger.info("GCS: credentials from JSON string")
        elif self._credentials_path:
            p = self._credentials_path
            if not os.path.isabs(p):
                base = Path(__file__).resolve().parent.parent.parent
                p = str(base / p)
            if os.path.exists(p):
                creds = _sa.Credentials.from_service_account_file(p)
                logger.info("GCS: credentials from file", path=p)
            else:
                logger.warning("GCS: credentials file not found", path=p)

        if creds:
            self._client = _storage.Client(project=self._project_id, credentials=creds)
        else:
            logger.info("GCS: using default credentials")
            self._client = _storage.Client(project=self._project_id)

        return self._client

    def _get_bucket(self):
        if self._bucket is not None:
            return self._bucket

        client = self._get_client()
        self._bucket = client.bucket(self._bucket_name)

        if not self._bucket.exists():
            logger.info("GCS: creating bucket", name=self._bucket_name)
            self._bucket = client.create_bucket(self._bucket_name, location="europe-west1")
            # Bucket-level IAM (allUsers → objectViewer) should be configured
            # via Terraform/gcloud, NOT via make_public() in code.

        return self._bucket

    # -- interface ---------------------------------------------------------
    def upload_bytes(self, data: bytes, blob_path: str, content_type: str = _DEFAULT_CT) -> str:
        bucket = self._get_bucket()
        blob = bucket.blob(blob_path)
        blob.upload_from_string(data, content_type=content_type)
        # Public access is provided by bucket-level IAM policy, not per-object ACL.
        url = f"https://storage.googleapis.com/{self._bucket_name}/{blob_path}"
        logger.info("GCS: uploaded", path=blob_path, size=len(data))
        return url

    def upload_base64(self, base64_data: str, blob_path: str) -> str:
        data, ct = self._parse_base64(base64_data)
        return self.upload_bytes(data, blob_path, content_type=ct)

    def delete(self, blob_path: str) -> bool:
        try:
            bucket = self._get_bucket()
            blob = bucket.blob(blob_path)
            blob.delete()
            return True
        except Exception as e:
            logger.error("GCS: delete failed", path=blob_path, error=str(e))
            return False

    def delete_prefix(self, prefix: str) -> bool:
        try:
            bucket = self._get_bucket()
            blobs = list(bucket.list_blobs(prefix=prefix))
            for b in blobs:
                b.delete()
            logger.info("GCS: deleted prefix", prefix=prefix, count=len(blobs))
            return True
        except Exception as e:
            logger.error("GCS: delete_prefix failed", prefix=prefix, error=str(e))
            return False

    def get_url(self, blob_path: str) -> str:
        return f"https://storage.googleapis.com/{self._bucket_name}/{blob_path}"

    # -- GCS specific extras -----------------------------------------------
    def get_signed_url(self, blob_url: str, expiration_hours: int = 168) -> str:
        """Generate a signed URL from an existing public URL."""
        try:
            parts = blob_url.replace("https://storage.googleapis.com/", "").split("/", 1)
            if len(parts) != 2:
                return blob_url
            bucket_name, blob_path = parts
            client = self._get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            return blob.generate_signed_url(expiration=timedelta(hours=expiration_hours), method="GET")
        except Exception as e:
            logger.error("GCS: signed URL failed", error=str(e))
            return blob_url

    def get_bucket_for(self, bucket_name: str):
        """Return a bucket reference for a specific bucket name (e.g. audio bucket)."""
        client = self._get_client()
        bucket = client.bucket(bucket_name)
        if not bucket.exists():
            bucket = client.create_bucket(bucket_name, location="europe-west1")
        return bucket


# ---------------------------------------------------------------------------
# Local filesystem implementation (dev / test)
# ---------------------------------------------------------------------------
class LocalStorageProvider(StorageProvider):
    """
    Writes files to local disk and returns URLs served by FastAPI StaticFiles.

    URL pattern: {base_url}/api/v1/media/{blob_path}
    """

    def __init__(self, storage_root: str = "/app/media", base_url: str = "http://localhost:8000") -> None:
        self._root = Path(storage_root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._base_url = base_url.rstrip("/")

    def upload_bytes(self, data: bytes, blob_path: str, content_type: str = _DEFAULT_CT) -> str:
        dest = self._root / blob_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        url = f"{self._base_url}/api/v1/media/{blob_path}"
        logger.info("Local: uploaded", path=str(dest), size=len(data))
        return url

    def upload_base64(self, base64_data: str, blob_path: str) -> str:
        data, _ = self._parse_base64(base64_data)
        return self.upload_bytes(data, blob_path)

    def delete(self, blob_path: str) -> bool:
        try:
            target = self._root / blob_path
            if target.exists():
                target.unlink()
            return True
        except Exception as e:
            logger.error("Local: delete failed", path=blob_path, error=str(e))
            return False

    def delete_prefix(self, prefix: str) -> bool:
        try:
            target = self._root / prefix
            if target.exists() and target.is_dir():
                shutil.rmtree(target)
            return True
        except Exception as e:
            logger.error("Local: delete_prefix failed", prefix=prefix, error=str(e))
            return False

    def get_url(self, blob_path: str) -> str:
        return f"{self._base_url}/api/v1/media/{blob_path}"
