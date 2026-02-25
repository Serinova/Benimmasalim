"""Email service for sending story previews.

Production checklist:
- SMTP_USER + SMTP_PASSWORD must be set
- DEV_EMAIL_OVERRIDE must be empty
- Gmail 25MB limit — prefer GCS URLs over CID/base64 attachments
- Runs in thread-pool to avoid blocking the async event loop
"""

import asyncio
import re
import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial
from html import escape as _esc
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger()

# Gmail hard limit is 25 MB; we stay under 20 MB to leave headroom for headers.
_MAX_EMAIL_BYTES = 20 * 1024 * 1024
# SMTP timeouts (seconds)
_SMTP_CONNECT_TIMEOUT = 15
# Max retry attempts for transient SMTP errors
_MAX_RETRIES = 2
_RETRY_DELAY_SECONDS = 2

# Characters that could enable SMTP header injection in Subject / From / To
_HEADER_INJECTION_RE = re.compile(r"[\r\n]")


def _sanitize_header(value: str) -> str:
    """Strip CR/LF to prevent SMTP header injection."""
    return _HEADER_INJECTION_RE.sub("", value)


class EmailService:
    """Service for sending emails via Gmail SMTP."""

    def __init__(self) -> None:
        self.smtp_server: str = settings.smtp_host
        self.smtp_port: int = settings.smtp_port
        self.sender_email: str = settings.smtp_user
        self.sender_password: str = settings.smtp_password
        self.sender_name: str = settings.smtp_from_name

    # ────────────────────────────────────────────────────────
    # Recipient resolution + prod safety guard
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _get_recipient(original_email: str) -> str:
        """Get the actual recipient email.

        In production ``dev_email_override`` is blocked at two levels:
        1. ``validate_prod_readiness()`` prevents the app from starting
        2. This runtime guard catches any hot-reload / env drift
        """
        override = settings.dev_email_override
        if override:
            if settings.is_production:
                logger.critical(
                    "BLOCKED: dev_email_override active in production — sending to real recipient",
                    override_value=override,
                )
                return original_email
            logger.info(
                "Email override active",
                original_suffix=original_email.rsplit("@", 1)[-1] if "@" in original_email else "***",
                actual_recipient=override,
            )
            return override
        return original_email

    # ────────────────────────────────────────────────────────
    # Public async API  (runs SMTP in thread-pool)
    # ────────────────────────────────────────────────────────

    async def send_story_email_async(
        self,
        recipient_email: str,
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
    ) -> bool:
        """Non-blocking wrapper — delegates to thread-pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self.send_story_email,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                child_name=child_name,
                story_title=story_title,
                story_pages=story_pages,
            ),
        )

    async def send_story_email_with_confirmation_async(
        self,
        recipient_email: str,
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
        confirmation_url: str,
        product_price: float | None = None,
    ) -> bool:
        """Non-blocking wrapper — delegates to thread-pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self.send_story_email_with_confirmation,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                child_name=child_name,
                story_title=story_title,
                story_pages=story_pages,
                confirmation_url=confirmation_url,
                product_price=product_price,
            ),
        )

    # ────────────────────────────────────────────────────────
    # Sync send methods (called inside thread-pool or directly)
    # ────────────────────────────────────────────────────────

    def send_story_email(
        self,
        recipient_email: str,
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
    ) -> bool:
        """Send story preview email to parent with embedded images."""
        actual_recipient = self._get_recipient(recipient_email)

        msg = MIMEMultipart("related")
        msg["Subject"] = _sanitize_header(f"{child_name} icin Ozel Hikaye: {story_title}")
        msg["From"] = f"{_sanitize_header(self.sender_name)} <{self.sender_email}>"
        msg["To"] = actual_recipient

        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        text_content = self._build_story_text(
            recipient_name=recipient_name,
            child_name=child_name,
            story_title=story_title,
            story_pages=story_pages,
        )
        msg_alternative.attach(MIMEText(text_content, "plain", "utf-8"))

        html_content = self._build_story_html_with_images(
            recipient_name=recipient_name,
            child_name=child_name,
            story_title=story_title,
            story_pages=story_pages,
        )
        msg_alternative.attach(MIMEText(html_content, "html", "utf-8"))

        self._attach_images(msg, story_pages)
        self._send_with_retry(actual_recipient, msg)

        logger.info(
            "Story email sent successfully",
            recipient_domain=actual_recipient.rsplit("@", 1)[-1] if "@" in actual_recipient else "***",
            pages_with_images=sum(1 for p in story_pages if p.get("image_base64") or p.get("image_url")),
        )
        return True

    def send_story_email_with_confirmation(
        self,
        recipient_email: str,
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
        confirmation_url: str,
        product_price: float | None = None,
    ) -> bool:
        """Send story preview email with confirmation button."""
        actual_recipient = self._get_recipient(recipient_email)

        msg = MIMEMultipart("related")
        msg["Subject"] = _sanitize_header(f"🎉 {child_name} için Özel Hikaye: {story_title}")
        msg["From"] = f"Benim Masalım <{self.sender_email}>"
        msg["To"] = actual_recipient

        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        text_content = (
            f"Merhaba {recipient_name},\n\n"
            f'{child_name} için hazırlanan "{story_title}" hikayesi hazır!\n\n'
            f"Hikayeyi onaylamak ve siparişi tamamlamak için aşağıdaki linke tıklayın:\n"
            f"{confirmation_url}\n\n"
            "Bu link 48 saat geçerlidir.\n\n---\nBenim Masalım\n"
        )
        msg_alternative.attach(MIMEText(text_content, "plain", "utf-8"))

        html_content = self._build_story_html_with_confirmation(
            recipient_name=recipient_name,
            child_name=child_name,
            story_title=story_title,
            story_pages=story_pages,
            confirmation_url=confirmation_url,
            product_price=product_price,
        )
        msg_alternative.attach(MIMEText(html_content, "html", "utf-8"))

        self._attach_images(msg, story_pages)
        self._send_with_retry(actual_recipient, msg)

        logger.info(
            "Story email with confirmation sent",
            recipient_domain=actual_recipient.rsplit("@", 1)[-1] if "@" in actual_recipient else "***",
        )
        return True

    # ────────────────────────────────────────────────────────
    # SMTP transport — timeout, TLS, retry
    # ────────────────────────────────────────────────────────

    def _send_with_retry(self, recipient: str, msg: MIMEMultipart) -> None:
        """Send with retry for transient SMTP errors (421, 451, temp network)."""
        import time

        # Size guard — Gmail rejects >25MB
        raw = msg.as_string()
        size_bytes = len(raw.encode("utf-8", errors="replace"))
        if size_bytes > _MAX_EMAIL_BYTES:
            logger.error(
                "Email too large — stripping CID attachments",
                size_mb=round(size_bytes / 1024 / 1024, 1),
            )
            self._strip_cid_attachments(msg)
            raw = msg.as_string()
            size_bytes = len(raw.encode("utf-8", errors="replace"))
            if size_bytes > _MAX_EMAIL_BYTES:
                raise EmailSendError(
                    f"E-posta boyutu çok büyük ({size_bytes // 1024 // 1024}MB > 20MB limiti)"
                )

        last_err: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                ctx = ssl.create_default_context()
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                with smtplib.SMTP(
                    self.smtp_server, self.smtp_port, timeout=_SMTP_CONNECT_TIMEOUT
                ) as server:
                    server.starttls(context=ctx)
                    server.login(self.sender_email, self.sender_password)
                    server.sendmail(self.sender_email, recipient, raw)
                return
            except smtplib.SMTPAuthenticationError as e:
                logger.error("SMTP authentication failed — not retrying", error=str(e))
                raise EmailSendError("E-posta gönderimi başarısız: Kimlik doğrulama hatası") from e
            except (
                smtplib.SMTPServerDisconnected,
                smtplib.SMTPResponseException,
                OSError,
            ) as e:
                last_err = e
                logger.warning(
                    "SMTP transient error",
                    attempt=attempt,
                    max_retries=_MAX_RETRIES,
                    error=str(e),
                )
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY_SECONDS * attempt)

        raise EmailSendError(f"E-posta gönderimi {_MAX_RETRIES} deneme sonrası başarısız") from last_err

    # ────────────────────────────────────────────────────────
    # Image attachment helpers
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _attach_images(msg: MIMEMultipart, story_pages: list[dict[str, Any]]) -> None:
        """Attach base64 images as CID inline parts.

        Skips pages that already have ``image_url`` — the HTML template
        uses ``<img src>`` for those, so CID attachment is unnecessary.
        """
        import base64

        for page in story_pages:
            if page.get("image_url"):
                continue
            image_b64 = page.get("image_base64")
            if not image_b64:
                continue
            page_num = page.get("page_number", 0)
            try:
                data_part = image_b64.split(",", 1)[-1] if "," in image_b64 else image_b64
                image_data = base64.b64decode(data_part)
                img = MIMEImage(image_data)
                img.add_header("Content-ID", f"<page{page_num}>")
                img.add_header("Content-Disposition", "inline", filename=f"sayfa_{page_num}.png")
                msg.attach(img)
            except Exception as img_err:
                logger.warning("Failed to attach image for page", page=page_num, error=str(img_err))

    @staticmethod
    def _strip_cid_attachments(msg: MIMEMultipart) -> None:
        """Remove CID image parts to bring email under size limit."""
        payloads = msg.get_payload()
        if isinstance(payloads, list):
            msg.set_payload([p for p in payloads if not isinstance(p, MIMEImage)])

    # ────────────────────────────────────────────────────────
    # HTML builders (all user strings escaped)
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _build_story_html_with_images(
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
    ) -> str:
        """Build HTML email content with embedded images or URLs.

        All user-supplied strings are HTML-escaped to prevent injection.
        """
        safe_title = _esc(story_title)
        safe_child = _esc(child_name)
        safe_recipient = _esc(recipient_name)

        pages_html = ""
        for page in story_pages:
            page_num = page.get("page_number", 0)
            text = _esc(page.get("text", ""))
            image_url = page.get("image_url")
            has_base64 = page.get("image_base64") is not None

            image_html = ""
            if image_url:
                safe_url = _esc(image_url)
                image_html = (
                    '<div style="text-align: center; margin-bottom: 15px;">'
                    f'<img src="{safe_url}" alt="Sayfa {page_num}" '
                    'style="max-width: 100%; height: auto; border-radius: 8px; '
                    'box-shadow: 0 4px 12px rgba(0,0,0,0.15);">'
                    "</div>"
                )
            elif has_base64:
                image_html = (
                    '<div style="text-align: center; margin-bottom: 15px;">'
                    f'<img src="cid:page{page_num}" alt="Sayfa {page_num}" '
                    'style="max-width: 100%; height: auto; border-radius: 8px; '
                    'box-shadow: 0 4px 12px rgba(0,0,0,0.15);">'
                    "</div>"
                )

            if page_num == 0:
                pages_html += (
                    '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                    'color: white; padding: 30px; text-align: center; '
                    'border-radius: 12px; margin-bottom: 20px;">'
                    f'<h1 style="font-size: 24px; margin: 0 0 15px 0;">{safe_title}</h1>'
                    '<p style="font-size: 14px; margin: 0; opacity: 0.9;">'
                    f"{safe_child} için özel olarak hazırlandı"
                    "</p></div>"
                    f"{image_html}"
                )
            else:
                pages_html += (
                    '<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; '
                    'margin-bottom: 20px; border-left: 4px solid #667eea;">'
                    '<p style="color: #667eea; font-size: 12px; font-weight: bold; '
                    f'margin: 0 0 15px 0;">SAYFA {page_num}</p>'
                    f"{image_html}"
                    '<p style="color: #333; font-size: 15px; line-height: 1.7; margin: 0;">'
                    f"{text}</p></div>"
                )

        return (
            "<!DOCTYPE html><html><head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            "</head>"
            '<body style="font-family: \'Segoe UI\', Arial, sans-serif; '
            'max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">'
            '<div style="text-align: center; margin-bottom: 30px;">'
            '<h2 style="color: #667eea; margin: 0;">✨ Benim Masalım ✨</h2></div>'
            f'<p style="font-size: 16px; color: #333;">Merhaba <strong>{safe_recipient}</strong>,</p>'
            f'<p style="font-size: 16px; color: #333;"><strong>{safe_child}</strong> için '
            "hazırlanan özel hikaye aşağıdadır. İyi okumalar! 📚</p>"
            '<hr style="border: none; border-top: 2px solid #eee; margin: 30px 0;">'
            f"{pages_html}"
            '<hr style="border: none; border-top: 2px solid #eee; margin: 30px 0;">'
            '<div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px;">'
            '<p style="color: #666; font-size: 14px; margin: 0;">'
            "Bu hikaye <strong>Benim Masalım</strong> tarafından yapay zeka ile oluşturulmuştur.</p>"
            '<p style="color: #999; font-size: 12px; margin-top: 10px;">'
            "© 2026 Benim Masalım - Kişiselleştirilmiş Çocuk Hikayeleri</p></div>"
            "</body></html>"
        )

    @staticmethod
    def _build_story_html_with_confirmation(
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
        confirmation_url: str,
        product_price: float | None = None,
    ) -> str:
        """Build HTML email with confirmation button.

        All user-supplied strings are HTML-escaped to prevent injection.
        """
        safe_title = _esc(story_title)
        safe_child = _esc(child_name)
        safe_recipient = _esc(recipient_name)
        safe_confirm_url = _esc(confirmation_url)

        pages_html = ""
        for page in story_pages:
            page_num = page.get("page_number", 0)
            image_url = page.get("image_url")
            has_base64 = page.get("image_base64") is not None

            image_html = ""
            if image_url:
                safe_url = _esc(image_url)
                alt_text = "Karşılama Sayfası" if page_num == "dedication" else f"Sayfa {page_num}"
                image_html = (
                    '<div style="text-align: center; margin-bottom: 10px;">'
                    f'<img src="{safe_url}" alt="{_esc(str(alt_text))}" '
                    'style="max-width: 100%; height: auto; border-radius: 8px;"></div>'
                )
            elif has_base64:
                image_html = (
                    '<div style="text-align: center; margin-bottom: 10px;">'
                    f'<img src="cid:page{page_num}" alt="Sayfa {page_num}" '
                    'style="max-width: 100%; height: auto; border-radius: 8px;"></div>'
                )

            if page_num == "dedication":
                pages_html += (
                    '<div style="margin-bottom: 15px; padding: 15px; background: #fff5e6; '
                    'border-radius: 8px; border: 2px solid #fbbf24;">'
                    '<p style="color: #92400e; font-size: 12px; font-weight: bold; margin: 0 0 8px 0;">'
                    f"💝 KARŞILAMA SAYFASI</p>{image_html}</div>"
                )
                continue

            page_label = "KAPAK" if page_num == 0 else f"SAYFA {page_num}"
            pages_html += (
                '<div style="margin-bottom: 15px; padding: 10px; background: #f9f9f9; border-radius: 8px;">'
                '<p style="color: #667eea; font-size: 11px; font-weight: bold; '
                f'margin: 0 0 8px 0;">{page_label}</p>'
                f"{image_html}</div>"
            )

        price_html = ""
        if product_price:
            price_html = (
                '<p style="font-size: 18px; margin: 10px 0;">'
                f"<strong>Toplam: {_esc(str(product_price))} TL</strong></p>"
            )

        return (
            "<!DOCTYPE html><html><head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            "</head>"
            '<body style="font-family: \'Segoe UI\', Arial, sans-serif; '
            'max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">'
            '<div style="text-align: center; margin-bottom: 20px;">'
            '<h2 style="color: #667eea; margin: 0;">✨ Benim Masalım ✨</h2></div>'
            f'<p style="font-size: 16px; color: #333;">Merhaba <strong>{safe_recipient}</strong>,</p>'
            '<p style="font-size: 16px; color: #333;">'
            f"<strong>{safe_child}</strong> için hazırlanan özel hikaye hazır!</p>"
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'color: white; padding: 20px; text-align: center; border-radius: 12px; margin: 20px 0;">'
            f'<h1 style="font-size: 22px; margin: 0 0 10px 0;">{safe_title}</h1>'
            '<p style="font-size: 13px; margin: 0; opacity: 0.9;">'
            f"{safe_child} için özel olarak hazırlandı</p></div>"
            f"{pages_html}"
            '<div style="background: #f0fdf4; border: 2px solid #22c55e; padding: 25px; '
            'border-radius: 12px; margin: 25px 0; text-align: center;">'
            '<h3 style="color: #166534; margin: 0 0 15px 0;">Hikayeyi Beğendiniz mi?</h3>'
            '<p style="color: #166534; font-size: 14px; margin: 0 0 15px 0;">'
            "Siparişi onaylamak için aşağıdaki butona tıklayın.</p>"
            f"{price_html}"
            f'<a href="{safe_confirm_url}" '
            'style="display: inline-block; background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); '
            "color: white; padding: 15px 40px; border-radius: 8px; "
            'text-decoration: none; font-weight: bold; font-size: 16px; '
            'box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);">'
            "✓ SİPARİŞİ ONAYLA</a>"
            '<p style="color: #666; font-size: 12px; margin-top: 15px;">'
            "Bu link 48 saat geçerlidir.</p></div>"
            '<hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">'
            '<div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">'
            '<p style="color: #666; font-size: 13px; margin: 0;">'
            "© 2026 Benim Masalım - Kişiselleştirilmiş Çocuk Hikayeleri</p></div>"
            "</body></html>"
        )

    @staticmethod
    def _build_story_text(
        recipient_name: str,
        child_name: str,
        story_title: str,
        story_pages: list[dict[str, Any]],
    ) -> str:
        """Build plain text email content."""
        pages_text = ""
        for page in story_pages:
            page_num = page.get("page_number", 0)
            text = page.get("text", "")
            if page_num == 0:
                sep = "=" * 50
                pages_text += f"\n{sep}\n{story_title}\n{child_name} için özel olarak hazırlandı\n{sep}\n\n"
            else:
                pages_text += f"[SAYFA {page_num}]\n{text}\n\n"

        return (
            f"Merhaba {recipient_name},\n\n"
            f"{child_name} için hazırlanan özel hikaye aşağıdadır.\n\n"
            f"{pages_text}\n---\n"
            "Bu hikaye Benim Masalım tarafından yapay zeka ile oluşturulmuştur.\n"
            "© 2026 Benim Masalım - Kişiselleştirilmiş Çocuk Hikayeleri\n"
        )


class EmailSendError(Exception):
    """Raised when an email cannot be delivered after retries."""


# Singleton instance
email_service = EmailService()
