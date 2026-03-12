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
        story_pages: list[dict[str, Any]],  # kept for API compat, not embedded in email
        confirmation_url: str,
        product_price: float | None = None,
    ) -> bool:
        """Send book-ready notification email with confirmation button.

        Images are NOT embedded — the confirmation page on the website shows all images.
        This keeps email size small (<20KB) and deliverable by all providers.
        """
        actual_recipient = self._get_recipient(recipient_email)

        # Simple MIMEMultipart/alternative (no related/attachments needed)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = _sanitize_header(f"🎉 {child_name} için Kitabınız Hazır!")
        msg["From"] = f"Benim Masalım <{self.sender_email}>"
        msg["To"] = actual_recipient

        text_content = (
            f"Merhaba {recipient_name},\n\n"
            f'{child_name} için hazırlanan "{story_title}" kitabı hazır!\n\n'
            f"Tüm sayfaları incelemek ve siparişi onaylamak için aşağıdaki linke tıklayın:\n"
            f"{confirmation_url}\n\n"
            "Bu link 48 saat geçerlidir.\n\n---\nBenim Masalım\n"
        )
        msg.attach(MIMEText(text_content, "plain", "utf-8"))

        html_content = self._build_story_html_with_confirmation(
            recipient_name=recipient_name,
            child_name=child_name,
            story_title=story_title,
            confirmation_url=confirmation_url,
            product_price=product_price,
        )
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # No image attachments — website shows all images
        self._send_with_retry(actual_recipient, msg)

        logger.info(
            "Story confirmation email sent (no image attachments)",
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
        confirmation_url: str,
        product_price: float | None = None,
    ) -> str:
        """Build lightweight HTML email with confirmation button.

        No images embedded — website shows all images.
        All user-supplied strings are HTML-escaped to prevent injection.
        """
        safe_title = _esc(story_title)
        safe_child = _esc(child_name)
        safe_recipient = _esc(recipient_name)
        safe_confirm_url = _esc(confirmation_url)

        price_html = ""
        if product_price:
            _price_display = f"{product_price:,.0f}".replace(",", ".") if product_price == int(product_price) else f"{product_price:,.2f}".replace(",", ".")
            price_html = (
                '<p style="font-size: 15px; color: #374151; margin: 0 0 20px 0;">'
                f"Sipariş tutarı: <strong>{_esc(_price_display)} TL</strong></p>"
            )

        return (
            "<!DOCTYPE html><html><head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            "</head>"
            '<body style="font-family: \'Segoe UI\', Tahoma, Arial, sans-serif; '
            'background-color: #f3f4f6; margin: 0; padding: 30px 16px;">'
            # Wrapper
            '<div style="max-width: 580px; margin: 0 auto; background: #ffffff; '
            'border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">'
            # Header
            '<div style="background-color: #7c3aed; background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%); '
            'padding: 32px 24px; text-align: center;">'
            '<p style="color: rgba(255,255,255,0.85); font-size: 13px; margin: 0 0 6px 0; '
            'letter-spacing: 2px; text-transform: uppercase;">✨ Benim Masalım ✨</p>'
            f'<h1 style="color: #ffffff; font-size: 24px; margin: 0; line-height: 1.3;">'
            f'{safe_child} İçin Kitabınız Hazır! 🎉</h1>'
            '</div>'
            # Body
            '<div style="padding: 32px 24px;">'
            f'<p style="font-size: 16px; color: #111827; margin: 0 0 8px 0;">'
            f'Merhaba <strong>{safe_recipient}</strong>,</p>'
            f'<p style="font-size: 15px; color: #374151; margin: 0 0 24px 0;">'
            f'<strong>{safe_child}</strong> için özel olarak hazırlanan '
            f'<em>"{safe_title}"</em> kitabı tamamlandı!</p>'
            # Book card
            '<div style="background: #faf5ff; border: 2px solid #e9d5ff; border-radius: 12px; '
            'padding: 20px; margin-bottom: 24px; text-align: center;">'
            '<p style="font-size: 13px; color: #7c3aed; font-weight: 600; margin: 0 0 6px 0; '
            'text-transform: uppercase; letter-spacing: 1px;">📖 Kitap Adı</p>'
            f'<p style="font-size: 20px; font-weight: bold; color: #4c1d95; margin: 0;">'
            f'{safe_title}</p>'
            '</div>'
            # AI notice box
            '<div style="background: #fffbeb; border: 2px solid #f59e0b; border-radius: 12px; '
            'padding: 20px 24px; margin-bottom: 28px;">'
            '<p style="font-size: 16px; font-weight: 700; color: #92400e; margin: 0 0 12px 0;">'
            '⚠️ Lütfen Görselleri Onaylamadan Önce İnceleyin</p>'
            '<p style="font-size: 14px; color: #78350f; margin: 0 0 10px 0; line-height: 1.6;">'
            'Yapay zeka henüz çok yeni bir teknoloji; bazen istenmeyen veya beklediğinizden '
            'farklı görseller çizebilir. Bu tamamen normaldir.</p>'
            '<p style="font-size: 14px; color: #78350f; margin: 0 0 10px 0; line-height: 1.6;">'
            '👉 <strong>Aşağıdaki butona tıklayıp tüm resimleri dikkatlice inceleyin.</strong><br>'
            'Beğenmediğiniz bir resim varsa, resmin üzerine tıklayın ve '
            '<strong>"Tekrar Çiz"</strong> butonuna basın — yeni resim hemen görünecektir.<br>'
            '<strong>Toplam 4 resim için yeniden çizim hakkınız vardır.</strong></p>'
            '<p style="font-size: 14px; color: #78350f; margin: 0; line-height: 1.6;">'
            '✅ Onayınızın ardından sipariş baskıya alınacaktır.</p>'
            '</div>'
            # CTA
            '<div style="text-align: center; margin-bottom: 28px;">'
            f'{price_html}'
            # Button — solid bgcolor for email clients that strip gradients
            f'<a href="{safe_confirm_url}" '
            'style="display: inline-block; background-color: #16a34a; '
            'background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); '
            'color: #ffffff !important; padding: 18px 52px; border-radius: 10px; '
            'text-decoration: none; font-weight: 700; font-size: 18px; '
            'box-shadow: 0 4px 14px rgba(22,163,74,0.4); letter-spacing: 0.3px; '
            'border: none; mso-padding-alt: 0;">'
            '✓ KİTABI İNCELE ve ONAYLA'
            '</a>'
            '<p style="color: #9ca3af; font-size: 12px; margin-top: 14px;">'
            '🔒 Bu link 48 saat geçerlidir.</p>'
            '</div>'
            # Help note
            '<div style="background: #f9fafb; border-radius: 8px; padding: 14px 16px;">'
            '<p style="font-size: 13px; color: #6b7280; margin: 0; text-align: center;">'
            'Sorun yaşarsanız bize ulaşın: '
            '<a href="mailto:destek@benimmasalim.com" style="color: #7c3aed; font-weight: 600;">'
            'destek@benimmasalim.com</a>'
            '</p>'
            '</div>'
            '</div>'
            # Footer
            '<div style="background: #f9fafb; padding: 16px 24px; text-align: center; '
            'border-top: 1px solid #e5e7eb;">'
            '<p style="color: #9ca3af; font-size: 12px; margin: 0;">'
            '© 2026 Benim Masalım – Kişiselleştirilmiş Çocuk Kitapları</p>'
            '</div>'
            '</div>'
            '</body></html>'
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


    # ────────────────────────────────────────────────────────
    # Transactional emails (password reset, order status, etc.)
    # ────────────────────────────────────────────────────────

    async def send_password_reset_email_async(
        self, recipient_email: str, recipient_name: str, reset_url: str,
    ) -> bool:
        """Send password reset link email."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self._send_password_reset_email,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                reset_url=reset_url,
            ),
        )

    def _send_password_reset_email(
        self, recipient_email: str, recipient_name: str, reset_url: str,
    ) -> bool:
        actual_recipient = self._get_recipient(recipient_email)
        safe_name = _esc(recipient_name or "Kullanıcı")
        safe_url = _esc(reset_url)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = _sanitize_header("Benim Masalım — Şifre Sıfırlama")
        msg["From"] = f"{_sanitize_header(self.sender_name)} <{self.sender_email}>"
        msg["To"] = actual_recipient

        text_content = (
            f"Merhaba {safe_name},\n\n"
            "Şifre sıfırlama talebiniz alındı.\n"
            f"Şifrenizi sıfırlamak için bu linki kullanın: {reset_url}\n\n"
            "Bu link 15 dakika geçerlidir.\n"
            "Bu talebi siz yapmadıysanız bu emaili görmezden gelebilirsiniz.\n\n"
            "© 2026 Benim Masalım"
        )
        msg.attach(MIMEText(text_content, "plain", "utf-8"))

        html_content = (
            '<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, '
            "sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; "
            'background: #f8f9fa; color: #333;">'
            '<div style="background: white; border-radius: 12px; padding: 30px; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.08);">'
            f'<h2 style="color: #7c3aed; margin: 0 0 20px 0;">Merhaba {safe_name},</h2>'
            '<p style="font-size: 15px; line-height: 1.6;">Şifre sıfırlama talebiniz alındı. '
            "Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz.</p>"
            '<div style="text-align: center; margin: 30px 0;">'
            f'<a href="{safe_url}" style="display: inline-block; '
            "background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%); "
            "color: white; padding: 14px 36px; border-radius: 8px; "
            'text-decoration: none; font-weight: bold; font-size: 16px;">'
            "Şifremi Sıfırla</a></div>"
            '<p style="font-size: 13px; color: #888;">Bu link 15 dakika geçerlidir. '
            "Bu talebi siz yapmadıysanız bu emaili görmezden gelebilirsiniz.</p>"
            "</div>"
            '<p style="text-align: center; font-size: 12px; color: #999; margin-top: 20px;">'
            "© 2026 Benim Masalım</p></body></html>"
        )
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        self._send_with_retry(actual_recipient, msg)
        logger.info("Password reset email sent", recipient_domain=actual_recipient.rsplit("@", 1)[-1])
        return True

    async def send_order_status_email_async(
        self,
        recipient_email: str,
        recipient_name: str,
        child_name: str,
        order_id: str,
        status_key: str,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        """Send order status change notification email."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self._send_order_status_email,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                child_name=child_name,
                order_id=order_id,
                status_key=status_key,
                extra=extra or {},
            ),
        )

    def _send_order_status_email(
        self,
        recipient_email: str,
        recipient_name: str,
        child_name: str,
        order_id: str,
        status_key: str,
        extra: dict[str, Any],
    ) -> bool:
        safe_tracking = _esc(str(extra.get("tracking_number", "-")))

        _STATUS_MAP: dict[str, tuple[str, str, str]] = {
            "PAID": (
                "Ödemeniz Alındı",
                "Ödemeniz başarıyla alındı! Kitabınızın üretimi başlıyor.",
                "#22c55e",
            ),
            "PROCESSING": (
                "Kitabınız Üretiliyor",
                "Kitabınız yapay zeka ile üretilmeye başlandı. Tamamlandığında sizi bilgilendireceğiz.",
                "#3b82f6",
            ),
            "READY_FOR_PRINT": (
                "Baskıya Hazır",
                "Kitabınız başarıyla üretildi ve baskıya hazır! Kısa süre içinde kargoya verilecek.",
                "#8b5cf6",
            ),
            "SHIPPED": (
                "Kargoya Verildi",
                f"Kitabınız kargoya verildi! Takip numarası: {safe_tracking}",
                "#f59e0b",
            ),
            "DELIVERED": (
                "Teslim Edildi",
                "Kitabınız teslim edildi! Keyifli okumalar dileriz.",
                "#10b981",
            ),
            "CANCELLED": (
                "Sipariş İptal Edildi",
                "Siparişiniz iptal edilmiştir. Sorularınız için destek ekibimize ulaşabilirsiniz.",
                "#ef4444",
            ),
            "REFUNDED": (
                "İade Tamamlandı",
                "İade işleminiz tamamlanmıştır. Tutar ödeme yönteminize iade edilecektir.",
                "#f97316",
            ),
        }
        subject_suffix, body_text, color = _STATUS_MAP.get(
            status_key, ("Sipariş Güncellendi", "Siparişinizde bir güncelleme var.", "#6b7280")
        )

        actual_recipient = self._get_recipient(recipient_email)
        safe_name = _esc(recipient_name or "Değerli Müşterimiz")
        safe_child = _esc(child_name)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = _sanitize_header(f"Benim Masalım — {subject_suffix}")
        msg["From"] = f"{_sanitize_header(self.sender_name)} <{self.sender_email}>"
        msg["To"] = actual_recipient

        text_content = (
            f"Merhaba {safe_name},\n\n"
            f"{safe_child} için hazırlanan kitabınızla ilgili güncelleme:\n\n"
            f"{body_text}\n\n"
            f"Sipariş No: {order_id[:8]}...\n\n"
            "© 2026 Benim Masalım"
        )
        msg.attach(MIMEText(text_content, "plain", "utf-8"))

        html_content = (
            '<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, '
            "sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; "
            'background: #f8f9fa; color: #333;">'
            '<div style="background: white; border-radius: 12px; padding: 30px; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.08);">'
            f'<div style="background: {color}; color: white; padding: 16px; '
            f'border-radius: 8px; text-align: center; margin-bottom: 20px;">'
            f'<h2 style="margin: 0; font-size: 18px;">{_esc(subject_suffix)}</h2></div>'
            f'<p style="font-size: 15px;">Merhaba {safe_name},</p>'
            f'<p style="font-size: 15px; line-height: 1.6;">'
            f'<strong>{safe_child}</strong> için hazırlanan kitabınızla ilgili güncelleme:</p>'
            f'<p style="font-size: 15px; line-height: 1.6; background: #f0f9ff; '
            f'padding: 16px; border-radius: 8px; border-left: 4px solid {color};">'
            f"{_esc(body_text)}</p>"
            f'<p style="font-size: 13px; color: #888;">Sipariş No: {_esc(order_id[:8])}...</p>'
            "</div>"
            '<p style="text-align: center; font-size: 12px; color: #999; margin-top: 20px;">'
            "© 2026 Benim Masalım</p></body></html>"
        )
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        self._send_with_retry(actual_recipient, msg)
        logger.info("Order status email sent", status=status_key, order_id=order_id[:8])
        return True


    # ────────────────────────────────────────────────────────
    # Invoice email (PDF attached)
    # ────────────────────────────────────────────────────────

    async def send_invoice_email_async(
        self,
        recipient_email: str,
        recipient_name: str,
        invoice_number: str,
        order_ref: str,
        issued_date: str,
        total_amount: str,
        pdf_bytes: bytes,
        download_url: str | None = None,
    ) -> bool:
        """Send invoice PDF as email attachment + optional secure download link."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(
                self._send_invoice_email,
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                invoice_number=invoice_number,
                order_ref=order_ref,
                issued_date=issued_date,
                total_amount=total_amount,
                pdf_bytes=pdf_bytes,
                download_url=download_url,
            ),
        )

    def _send_invoice_email(
        self,
        recipient_email: str,
        recipient_name: str,
        invoice_number: str,
        order_ref: str,
        issued_date: str,
        total_amount: str,
        pdf_bytes: bytes,
        download_url: str | None = None,
    ) -> bool:
        from email.mime.application import MIMEApplication

        actual_recipient = self._get_recipient(recipient_email)
        safe_name = _esc(recipient_name or "Değerli Müşterimiz")
        safe_inv = _esc(invoice_number)
        safe_ref = _esc(order_ref)
        safe_date = _esc(issued_date)
        safe_total = _esc(total_amount)

        msg = MIMEMultipart("mixed")
        msg["Subject"] = _sanitize_header(f"Faturanız Hazır — Sipariş #{order_ref}")
        msg["From"] = f"{_sanitize_header(self.sender_name)} <{self.sender_email}>"
        msg["To"] = actual_recipient

        alt = MIMEMultipart("alternative")
        msg.attach(alt)

        dl_text = ""
        dl_html = ""
        if download_url:
            safe_dl_url = _esc(download_url)
            dl_text = (
                f"\nEk açılamıyorsa bu linkten indirebilirsiniz (48 saat geçerli, tek kullanımlık):\n"
                f"{download_url}\n"
            )
            dl_html = (
                '<div style="text-align: center; margin: 20px 0;">'
                f'<a href="{safe_dl_url}" style="display: inline-block; '
                "background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%); "
                "color: white; padding: 12px 28px; border-radius: 8px; "
                'text-decoration: none; font-weight: bold; font-size: 14px;">'
                "Faturayı İndir</a>"
                '<p style="font-size: 11px; color: #999; margin-top: 8px;">'
                "Bu link 48 saat geçerlidir ve tek kullanımlıktır.</p></div>"
            )

        text_content = (
            f"Merhaba {recipient_name or 'Değerli Müşterimiz'},\n\n"
            f"Faturanız hazırlanmıştır.\n\n"
            f"Fatura No: {invoice_number}\n"
            f"Sipariş Ref: {order_ref}\n"
            f"Tarih: {issued_date}\n"
            f"Toplam: {total_amount}\n\n"
            "Fatura PDF'i bu emailin ekinde yer almaktadır.\n"
            f"{dl_text}\n"
            "© 2026 Benim Masalım"
        )
        alt.attach(MIMEText(text_content, "plain", "utf-8"))

        html_content = (
            '<!DOCTYPE html><html><body style="font-family: -apple-system, BlinkMacSystemFont, '
            "sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; "
            'background: #f8f9fa; color: #333;">'
            '<div style="background: white; border-radius: 12px; padding: 30px; '
            'box-shadow: 0 2px 8px rgba(0,0,0,0.08);">'
            '<div style="text-align: center; margin-bottom: 20px;">'
            '<h2 style="color: #7c3aed; margin: 0;">Benim Masalım</h2></div>'
            f'<p style="font-size: 15px;">Merhaba <strong>{safe_name}</strong>,</p>'
            '<p style="font-size: 15px; line-height: 1.6;">Faturanız hazırlanmıştır. '
            "PDF dosyası bu emailin ekinde yer almaktadır.</p>"
            '<div style="background: #f0fdf4; border: 1px solid #bbf7d0; '
            'padding: 16px; border-radius: 8px; margin: 20px 0;">'
            '<table style="width: 100%; font-size: 14px; border-collapse: collapse;">'
            f'<tr><td style="padding: 6px 0; color: #666;">Fatura No:</td>'
            f'<td style="padding: 6px 0; text-align: right; font-weight: bold;">{safe_inv}</td></tr>'
            f'<tr><td style="padding: 6px 0; color: #666;">Sipariş Ref:</td>'
            f'<td style="padding: 6px 0; text-align: right;">{safe_ref}</td></tr>'
            f'<tr><td style="padding: 6px 0; color: #666;">Tarih:</td>'
            f'<td style="padding: 6px 0; text-align: right;">{safe_date}</td></tr>'
            '<tr style="border-top: 1px solid #d1fae5;">'
            f'<td style="padding: 8px 0; color: #166534; font-weight: bold;">Toplam:</td>'
            f'<td style="padding: 8px 0; text-align: right; font-weight: bold; '
            f'color: #166534; font-size: 16px;">{safe_total}</td></tr>'
            "</table></div>"
            f"{dl_html}"
            '<p style="font-size: 13px; color: #888;">Bu belge e-fatura / e-arşiv fatura '
            "yerine geçmez. Bilgilendirme amaçlıdır.</p>"
            "</div>"
            '<p style="text-align: center; font-size: 12px; color: #999; margin-top: 20px;">'
            "© 2026 Benim Masalım</p></body></html>"
        )
        alt.attach(MIMEText(html_content, "html", "utf-8"))

        pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        pdf_attachment.add_header(
            "Content-Disposition", "attachment",
            filename=f"fatura_{invoice_number}.pdf",
        )
        msg.attach(pdf_attachment)

        self._send_with_retry(actual_recipient, msg)
        logger.info(
            "Invoice email sent",
            invoice_number=invoice_number,
            recipient_domain=actual_recipient.rsplit("@", 1)[-1],
        )
        return True


class EmailSendError(Exception):
    """Raised when an email cannot be delivered after retries."""


# Singleton instance
email_service = EmailService()
