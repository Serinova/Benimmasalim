"""URL validation utilities to prevent SSRF attacks.

Validates external URLs before they are passed to AI services or stored.
Blocks access to internal networks, cloud metadata endpoints, and non-HTTPS schemes.
"""

import ipaddress
import socket
from urllib.parse import urlparse

import structlog

from app.core.exceptions import ValidationError

logger = structlog.get_logger()

_BLOCKED_HOSTS: frozenset[str] = frozenset({
    "localhost",
    "metadata.google.internal",
    "metadata.goog",
    "169.254.169.254",
    "0.0.0.0",
    "[::1]",
})

_ALLOWED_SCHEMES: frozenset[str] = frozenset({"https"})

_TRUSTED_DOMAINS: frozenset[str] = frozenset({
    "storage.googleapis.com",
    "storage.cloud.google.com",
    "benimmasalim-raw-uploads.storage.googleapis.com",
    "benimmasalim-generated-books.storage.googleapis.com",
    "benimmasalim-images.storage.googleapis.com",
    "benimmasalim-audio-files.storage.googleapis.com",
})


def _is_private_ip(hostname: str) -> bool:
    """Check if hostname resolves to a private/reserved IP."""
    try:
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        )
    except ValueError:
        pass

    try:
        resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _family, _, _, _, sockaddr in resolved:
            addr = sockaddr[0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
    except OSError:
        pass

    return False


def validate_image_url(url: str | None, field_name: str = "image_url") -> str | None:
    """Validate an image URL for safe external usage.

    Args:
        url: The URL to validate (None passes through).
        field_name: Field name for error messages.

    Returns:
        The validated URL or None.

    Raises:
        ValidationError: If URL is unsafe.
    """
    if not url or not url.strip():
        return None

    url = url.strip()

    parsed = urlparse(url)

    if parsed.scheme not in _ALLOWED_SCHEMES:
        logger.warning("SSRF_BLOCKED: invalid scheme", field=field_name, scheme=parsed.scheme)
        raise ValidationError(f"{field_name}: Sadece HTTPS URL kabul edilir")

    hostname = (parsed.hostname or "").lower()

    if not hostname:
        raise ValidationError(f"{field_name}: Geçersiz URL")

    if hostname in _BLOCKED_HOSTS:
        logger.warning("SSRF_BLOCKED: blocked host", field=field_name, host=hostname)
        raise ValidationError(f"{field_name}: Bu adres kabul edilmez")

    if _is_private_ip(hostname):
        logger.warning("SSRF_BLOCKED: private IP", field=field_name, host=hostname)
        raise ValidationError(f"{field_name}: Dahili ağ adreslerine erişim engellendi")

    if parsed.port and parsed.port != 443:
        logger.warning("SSRF_BLOCKED: non-standard port", field=field_name, port=parsed.port)
        raise ValidationError(f"{field_name}: Standart dışı port kabul edilmez")

    return url


def is_trusted_storage_url(url: str) -> bool:
    """Check if URL belongs to our trusted GCS buckets."""
    if not url:
        return False
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return hostname in _TRUSTED_DOMAINS or hostname.endswith(".storage.googleapis.com")
