"""Invoice PDF generation service using ReportLab.

Generates A4 invoice PDFs with Turkish character support (DejaVuSans).
Uploads to GCS and updates the Invoice record.

Supports two flows:
  - Legacy Order flow: Invoice.order_id → orders table
  - Trial / "Try Before You Buy" flow: Invoice.story_preview_id → story_previews table
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import os
import uuid as _uuid_mod
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import structlog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.invoice import Invoice, InvoiceStatus

logger = structlog.get_logger()


@dataclasses.dataclass
class _PreviewBillingAdapter:
    """Duck-typed wrapper around StoryPreview that exposes the same billing interface as Order."""

    id: UUID
    child_name: str
    billing_type: str | None
    billing_full_name: str | None
    billing_email: str | None
    billing_phone: str | None
    billing_company_name: str | None
    billing_tax_id: str | None
    billing_tax_office: str | None
    billing_tc_no: str | None
    billing_address: dict | None
    shipping_address: dict | None
    has_audio_book: bool
    is_coloring_book: bool
    subtotal_amount: Decimal | None
    final_amount: Decimal | None
    payment_amount: Decimal | None
    discount_applied_amount: Decimal | None
    promo_code_text: str | None
    scenario_id: UUID | None = None
    product_id: UUID | None = None

    @classmethod
    def from_preview(cls, preview: "StoryPreview") -> "_PreviewBillingAdapter":  # type: ignore[name-defined]
        bd: dict = preview.billing_data or {}
        raw_price = preview.product_price
        price = Decimal(str(raw_price)) if raw_price else Decimal("0")
        raw_disc = preview.discount_applied_amount
        discount = Decimal(str(raw_disc)) if raw_disc else None
        final = price - discount if discount else price
        return cls(
            id=preview.id,
            child_name=preview.child_name or "",
            billing_type=bd.get("billing_type") or "individual",
            billing_full_name=bd.get("billing_full_name") or preview.parent_name,
            billing_email=bd.get("billing_email") or preview.parent_email,
            billing_phone=bd.get("billing_phone") or preview.parent_phone,
            billing_company_name=bd.get("billing_company_name"),
            billing_tax_id=bd.get("billing_tax_id"),
            billing_tax_office=bd.get("billing_tax_office"),
            billing_tc_no=bd.get("billing_tc_no") or bd.get("tc_no") or bd.get("identityNumber"),
            billing_address=bd.get("billing_address") or bd.get("shipping_address"),
            shipping_address=bd.get("shipping_address") or bd.get("billing_address"),
            has_audio_book=bool(getattr(preview, "has_audio_book", False)),
            is_coloring_book=bool(getattr(preview, "has_coloring_book", False)),
            subtotal_amount=price,
            final_amount=final,
            payment_amount=price,
            discount_applied_amount=discount,
            promo_code_text=getattr(preview, "promo_code_text", None),
        )

_FONT_NAME = "DejaVuSans"
_RESOLVED_FONT: str | None = None


def _ensure_font() -> str:
    """Register DejaVuSans if not already registered. Returns usable font name."""
    global _RESOLVED_FONT
    if _RESOLVED_FONT is not None:
        return _RESOLVED_FONT

    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bundled = os.path.join(_root, "fonts", "DejaVuSans.ttf")

    paths = [
        bundled,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "DejaVuSans.ttf",
        "./fonts/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(_FONT_NAME, p))
                _RESOLVED_FONT = _FONT_NAME
                return _RESOLVED_FONT
            except Exception as exc:
                logger.warning("font_register_failed", path=p, error=str(exc))

    _RESOLVED_FONT = "Helvetica"
    return _RESOLVED_FONT


def _build_invoice_pdf(
    invoice: Invoice,
    order,
    *,
    scenario_name: str | None = None,
    product_base_price: "Decimal | None" = None,
    product_vat_rate: "Decimal | None" = None,
    company: dict[str, str] | None = None,
) -> bytes:
    """Render an A4 invoice PDF and return raw bytes."""
    font = _ensure_font()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Resolve company info: passed-in dict > env settings fallback
    co = company or {}
    co_name = co.get("name") or settings.invoice_company_name or "Benim Masalım"
    co_address = co.get("address") or settings.invoice_company_address
    co_tax_id = co.get("tax_id") or settings.invoice_company_tax_id
    co_tax_office = co.get("tax_office") or settings.invoice_company_tax_office
    co_phone = co.get("phone") or settings.invoice_company_phone
    co_email = co.get("email") or settings.invoice_company_email

    y = height - 30 * mm

    # ── Company header ────────────────────────────────────────
    c.setFont(font, 16)
    c.drawString(25 * mm, y, co_name)
    y -= 7 * mm
    c.setFont(font, 9)
    if co_address:
        c.drawString(25 * mm, y, co_address)
        y -= 5 * mm
    info_parts: list[str] = []
    if co_tax_office:
        info_parts.append(f"Vergi Dairesi: {co_tax_office}")
    if co_tax_id:
        info_parts.append(f"VKN: {co_tax_id}")
    if info_parts:
        c.drawString(25 * mm, y, "  |  ".join(info_parts))
        y -= 5 * mm
    contact_parts: list[str] = []
    if co_phone:
        contact_parts.append(f"Tel: {co_phone}")
    if co_email:
        contact_parts.append(f"E-posta: {co_email}")
    if contact_parts:
        c.drawString(25 * mm, y, "  |  ".join(contact_parts))
        y -= 5 * mm

    # Separator
    y -= 3 * mm
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.setLineWidth(0.5)
    c.line(25 * mm, y, width - 25 * mm, y)
    y -= 8 * mm

    # ── Invoice meta ──────────────────────────────────────────
    c.setFont(font, 12)
    c.drawString(25 * mm, y, "FATURA")
    c.setFont(font, 9)
    c.drawRightString(width - 25 * mm, y, f"Fatura No: {invoice.invoice_number}")
    y -= 6 * mm
    c.drawRightString(
        width - 25 * mm, y,
        f"Düzenlenme Tarihi: {invoice.issued_at.strftime('%d.%m.%Y')}",
    )
    y -= 6 * mm
    order_ref = str(order.id)[:8].upper()
    c.drawRightString(width - 25 * mm, y, f"Sipariş Ref: {order_ref}")
    y -= 10 * mm

    # ── Customer block ────────────────────────────────────────
    c.setFont(font, 10)
    c.drawString(25 * mm, y, "Müşteri Bilgileri")
    y -= 6 * mm
    c.setFont(font, 9)

    billing_type = getattr(order, "billing_type", None) or "individual"
    if billing_type == "corporate" and order.billing_company_name:
        c.drawString(25 * mm, y, f"Firma: {order.billing_company_name}")
        y -= 5 * mm
        if order.billing_tax_id:
            c.drawString(25 * mm, y, f"VKN/TCKN: {order.billing_tax_id}")
            y -= 5 * mm
        if order.billing_tax_office:
            c.drawString(25 * mm, y, f"Vergi Dairesi: {order.billing_tax_office}")
            y -= 5 * mm

    if order.billing_full_name:
        c.drawString(25 * mm, y, f"Ad Soyad: {order.billing_full_name}")
        y -= 5 * mm
    addr = getattr(order, "billing_address", None) or getattr(order, "shipping_address", None)
    billing_tc_no = getattr(order, "billing_tc_no", None)
    
    if not billing_tc_no and isinstance(addr, dict):
        billing_tc_no = addr.get("identityNumber") or addr.get("identity_number") or addr.get("tc_no") or addr.get("tcNo")

    if not billing_tc_no and billing_type == "individual":
        tax_id = getattr(order, "billing_tax_id", None)
        if tax_id and len(str(tax_id).strip()) == 11:
            billing_tc_no = str(tax_id).strip()

    if billing_type == "individual" and billing_tc_no:
        c.drawString(25 * mm, y, f"T.C. Kimlik No: {billing_tc_no}")
        y -= 5 * mm
    if order.billing_email:
        c.drawString(25 * mm, y, f"E-posta: {order.billing_email}")
        y -= 5 * mm
    if order.billing_phone:
        c.drawString(25 * mm, y, f"Telefon: {order.billing_phone}")
        y -= 5 * mm

    if addr:
        address_text = ""
        if isinstance(addr, dict):
            addr_line = addr.get("address_line") or addr.get("address", "")
            district = addr.get("district", "")
            city = addr.get("city", "")
            parts = [p for p in [addr_line, district, city] if p]
            if parts:
                address_text = ", ".join(parts)
        elif isinstance(addr, str):
            address_text = addr
            
        if address_text:
            from textwrap import wrap
            c.drawString(25 * mm, y, "Adres:")
            y -= 5 * mm
            for line in wrap(address_text, width=70):
                c.drawString(25 * mm, y, line)
                y -= 5 * mm

    y -= 5 * mm

    # ── Line items table ──────────────────────────────────────
    c.setStrokeColor(colors.HexColor("#333333"))
    c.setLineWidth(0.5)

    col_x = [25 * mm, 110 * mm, 135 * mm, 160 * mm]
    headers = ["Ürün", "Adet", "Birim Fiyat", "Tutar"]

    c.setFont(font, 9)
    c.setFillColor(colors.HexColor("#f5f5f5"))
    c.rect(25 * mm, y - 5 * mm, width - 50 * mm, 7 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)

    for i, h in enumerate(headers):
        if i == 0:
            c.drawString(col_x[i] + 2 * mm, y - 3.5 * mm, h)
        else:
            c.drawRightString(col_x[i] + 22 * mm, y - 3.5 * mm, h)

    y -= 12 * mm

    child_name = order.child_name or "Çocuk"
    subtotal = order.subtotal_amount or order.payment_amount or Decimal("0")
    final = order.final_amount or order.payment_amount or Decimal("0")

    # Compute per-line prices
    if product_base_price is not None and order.has_audio_book:
        base_price = product_base_price
        audio_price: Decimal | None = max(subtotal - product_base_price, Decimal("0"))
    elif product_base_price is not None:
        base_price = product_base_price
        audio_price = None
    else:
        base_price = subtotal
        audio_price = None

    # Build product description with scenario name if available
    if scenario_name:
        book_desc = f"Kişisel. Masal Kitabı ({scenario_name[:25]}) — {child_name}"
    else:
        book_desc = f"Kişiselleştirilmiş Masal Kitabı — {child_name}"

    c.setFont(font, 9)
    c.drawString(col_x[0] + 2 * mm, y, book_desc[:58])
    c.drawRightString(col_x[1] + 22 * mm, y, "1")
    c.drawRightString(col_x[2] + 22 * mm, y, f"{base_price:.2f} TL")
    c.drawRightString(col_x[3] + 22 * mm, y, f"{base_price:.2f} TL")
    y -= 6 * mm

    if order.has_audio_book:
        c.drawString(col_x[0] + 2 * mm, y, "  + Sesli Kitap Eklentisi")
        c.drawRightString(col_x[1] + 22 * mm, y, "1")
        if audio_price is not None:
            c.drawRightString(col_x[2] + 22 * mm, y, f"{audio_price:.2f} TL")
            c.drawRightString(col_x[3] + 22 * mm, y, f"{audio_price:.2f} TL")
        y -= 6 * mm

    if order.is_coloring_book:
        c.drawString(col_x[0] + 2 * mm, y, "  + Boyama Kitabı")
        y -= 6 * mm

    # Separator
    y -= 2 * mm
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(25 * mm, y, width - 25 * mm, y)
    y -= 8 * mm

    # ── Totals block ──────────────────────────────────────────
    c.setFont(font, 9)
    right_col = width - 25 * mm
    label_col = right_col - 55 * mm

    c.drawString(label_col, y, "Ara Toplam:")
    c.drawRightString(right_col, y, f"{subtotal:.2f} TL")
    y -= 6 * mm

    discount = order.discount_applied_amount
    if discount and discount > 0:
        c.drawString(label_col, y, f"İndirim ({order.promo_code_text or ''}):")
        c.drawRightString(right_col, y, f"-{discount:.2f} TL")
        y -= 6 * mm

    # KDV breakdown — ürün KDV oranını kullan, yoksa env'den al
    vat_rate = (
        product_vat_rate
        if product_vat_rate is not None
        else Decimal(str(settings.invoice_vat_rate))
    )
    vat_divisor = Decimal("100") + vat_rate
    kdv_amount = (final * vat_rate / vat_divisor).quantize(Decimal("0.01"))
    kdv_label = settings.invoice_vat_label or "KDV"
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(label_col, y, f"{kdv_label} (%{int(vat_rate)}) Dahil:")
    c.drawRightString(right_col, y, f"{kdv_amount:.2f} TL")
    c.setFillColor(colors.black)
    y -= 6 * mm

    c.setFont(font, 11)
    c.drawString(label_col, y, "TOPLAM:")
    c.drawRightString(right_col, y, f"{final:.2f} TL")
    y -= 12 * mm

    # ── Footer / disclaimer ───────────────────────────────────
    c.setFont(font, 7)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(
        25 * mm, 20 * mm,
        "Bu belge e-fatura / e-arşiv fatura yerine geçmez. Bilgilendirme amaçlıdır.",
    )
    c.drawString(
        25 * mm, 15 * mm,
        f"PDF Sürüm: {invoice.pdf_version}  |  Oluşturulma: {datetime.now(UTC).strftime('%d.%m.%Y %H:%M')}",
    )

    c.save()
    return buf.getvalue()


async def _load_invoice_company_settings(db: AsyncSession) -> dict[str, str]:
    """Load invoice company settings from DB, falling back to env config."""
    from app.models.app_setting import AppSetting

    keys = [
        "invoice_company_name",
        "invoice_company_address",
        "invoice_company_tax_id",
        "invoice_company_tax_office",
        "invoice_company_phone",
        "invoice_company_email",
    ]
    result = await db.execute(select(AppSetting).where(AppSetting.key.in_(keys)))
    rows = {r.key: (r.value or "") for r in result.scalars().all()}

    return {
        "name": rows.get("invoice_company_name") or settings.invoice_company_name or "Benim Masalım",
        "address": rows.get("invoice_company_address") or settings.invoice_company_address,
        "tax_id": rows.get("invoice_company_tax_id") or settings.invoice_company_tax_id,
        "tax_office": rows.get("invoice_company_tax_office") or settings.invoice_company_tax_office,
        "phone": rows.get("invoice_company_phone") or settings.invoice_company_phone,
        "email": rows.get("invoice_company_email") or settings.invoice_company_email,
    }


async def generate_invoice_pdf(ref_id: UUID, db: AsyncSession) -> None:
    """Generate (or regenerate) the invoice PDF for an order or trial preview.

    `ref_id` is either an Order.id (legacy flow) or StoryPreview.id (trial flow).
    The function looks up the invoice by trying both columns.

    Steps:
      1. Load invoice (by order_id or story_preview_id)
      2. Load billing entity (Order or StoryPreview via adapter)
      3. Set status ISSUED, render PDF, upload to GCS
      4. Set status PDF_READY + pdf_url + pdf_hash
      On error: FAILED + last_error + retry_count++
    """
    from app.models.order import Order
    from app.models.story_preview import StoryPreview
    from app.services.storage_service import storage_service

    try:
        result = await db.execute(
            select(Invoice)
            .where(
                or_(Invoice.order_id == ref_id, Invoice.story_preview_id == ref_id)
            )
            .with_for_update(skip_locked=True)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            logger.error("generate_invoice_pdf: no invoice found", ref_id=str(ref_id))
            return

        if invoice.invoice_status == InvoiceStatus.PDF_READY.value:
            logger.info("generate_invoice_pdf: already PDF_READY, skipping", ref_id=str(ref_id))
            return

        if invoice.invoice_status == InvoiceStatus.CANCELLED.value:
            logger.info("generate_invoice_pdf: invoice cancelled, skipping", ref_id=str(ref_id))
            return

        # Load billing entity — prefer Order (legacy), fall back to StoryPreview (trial)
        billing_entity = None
        is_preview_flow = False

        if invoice.order_id:
            ord_res = await db.execute(select(Order).where(Order.id == invoice.order_id))
            billing_entity = ord_res.scalar_one_or_none()

        if billing_entity is None and invoice.story_preview_id:
            prev_res = await db.execute(
                select(StoryPreview).where(StoryPreview.id == invoice.story_preview_id)
            )
            preview = prev_res.scalar_one_or_none()
            if preview:
                billing_entity = _PreviewBillingAdapter.from_preview(preview)
                is_preview_flow = True

        if billing_entity is None:
            logger.error(
                "generate_invoice_pdf: billing entity not found",
                ref_id=str(ref_id),
                order_id=str(invoice.order_id),
                story_preview_id=str(invoice.story_preview_id),
            )
            return

        # Load scenario name and product info for line-item breakdown
        from app.models.product import Product
        from app.models.scenario import Scenario as ScenarioModel

        scenario_name: str | None = None
        product_base_price: Decimal | None = None
        product_vat_rate: Decimal | None = None

        if not is_preview_flow:
            if billing_entity.scenario_id:
                sc_res = await db.execute(
                    select(ScenarioModel.name).where(ScenarioModel.id == billing_entity.scenario_id)
                )
                scenario_name = sc_res.scalar_one_or_none()

            if billing_entity.product_id:
                pr_res = await db.execute(
                    select(Product.base_price, Product.vat_rate).where(
                        Product.id == billing_entity.product_id
                    )
                )
                row = pr_res.one_or_none()
                if row:
                    product_base_price = row[0]
                    product_vat_rate = row[1]
        else:
            # For preview flow use scenario_name from StoryPreview directly
            scenario_name = getattr(invoice.story_preview, "scenario_name", None) if invoice.story_preview else None
            if invoice.story_preview and invoice.story_preview.product_id:
                pr_res = await db.execute(
                    select(Product.base_price, Product.vat_rate).where(
                        Product.id == invoice.story_preview.product_id
                    )
                )
                row = pr_res.one_or_none()
                if row:
                    product_base_price = row[0]
                    product_vat_rate = row[1]

        company = await _load_invoice_company_settings(db)

        invoice.invoice_status = InvoiceStatus.ISSUED.value
        await db.flush()

        pdf_bytes = _build_invoice_pdf(
            invoice,
            billing_entity,
            scenario_name=scenario_name,
            product_base_price=product_base_price,
            product_vat_rate=product_vat_rate,
            company=company,
        )
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()

        pdf_url = storage_service.upload_invoice_pdf(
            pdf_bytes, str(ref_id), invoice.invoice_number,
        )

        invoice.invoice_status = InvoiceStatus.PDF_READY.value
        invoice.pdf_url = pdf_url
        invoice.pdf_hash = pdf_hash
        invoice.pdf_generated_at = datetime.now(UTC)
        await db.commit()

        logger.info(
            "generate_invoice_pdf: success",
            ref_id=str(ref_id),
            invoice_number=invoice.invoice_number,
            pdf_version=invoice.pdf_version,
            is_preview_flow=is_preview_flow,
        )

        try:
            from app.services.invoice_email_service import send_invoice_email_for_order
            await send_invoice_email_for_order(ref_id, db)
        except Exception:
            logger.exception(
                "generate_invoice_pdf: invoice email failed (non-fatal)",
                ref_id=str(ref_id),
            )

    except Exception as exc:
        await db.rollback()

        try:
            result = await db.execute(
                select(Invoice).where(
                    or_(Invoice.order_id == ref_id, Invoice.story_preview_id == ref_id)
                )
            )
            invoice = result.scalar_one_or_none()
            if invoice:
                invoice.invoice_status = InvoiceStatus.FAILED.value
                invoice.last_error = str(exc)[:500]
                invoice.retry_count = (invoice.retry_count or 0) + 1
                await db.commit()
        except Exception:
            logger.exception("generate_invoice_pdf: failed to update invoice status")

        logger.exception(
            "generate_invoice_pdf: failed",
            ref_id=str(ref_id),
            error=str(exc),
        )


async def retry_failed_invoices(db: AsyncSession) -> int:
    """Retry all FAILED invoices with retry_count < 3. Returns count retried."""
    result = await db.execute(
        select(Invoice).where(
            Invoice.invoice_status == InvoiceStatus.FAILED.value,
            Invoice.retry_count < 3,
        )
    )
    invoices = result.scalars().all()
    count = 0
    for inv in invoices:
        ref_id = inv.order_id or inv.story_preview_id
        if not ref_id:
            continue
        try:
            await generate_invoice_pdf(ref_id, db)
            count += 1
        except Exception:
            logger.exception("retry_failed_invoices: retry failed", ref_id=str(ref_id))
    return count
