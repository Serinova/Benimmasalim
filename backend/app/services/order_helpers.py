"""Shared order helper functions.

Extracted from app.api.v1.orders to break circular dependencies:
- order_state_machine imports snapshot_billing_to_order
- trials / trial_generation_service import force_deterministic_title
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

from app.models.order import Order

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Deterministic title helper
# ---------------------------------------------------------------------------


def force_deterministic_title(
    child_name: str | None,
    scenario_name: str | None,
    original_title: str | None = None,
) -> str:
    """Always produce '{ChildName}'s {ScenarioName}' format title.

    Never rely on Gemini — guarantees consistent titles across all scenarios.
    """
    from app.services.ai.gemini_service import (
        _get_possessive_suffix,
        _normalize_title_turkish,
    )

    child = (child_name or "").strip()
    if child:
        child = child[0].upper() + child[1:].lower() if len(child) > 1 else child.upper()

    scenario = (scenario_name or "").strip()
    if not scenario:
        scenario = "Büyülü Macera"

    suffix = _get_possessive_suffix(child)
    forced = f"{child}'{suffix} {scenario}"

    original = (original_title or "").strip()
    if original.lower() != forced.lower():
        _logger.warning(
            "DETERMINISTIC_TITLE_OVERRIDE",
            original=original,
            forced=forced,
            child=child,
            scenario=scenario,
        )

    return _normalize_title_turkish(forced)


# ---------------------------------------------------------------------------
# Billing helpers
# ---------------------------------------------------------------------------


def validate_tax_id(tax_id: str) -> bool:
    """Basic VKN (10 digit) or TCKN (11 digit) format check."""
    cleaned = tax_id.strip()
    return cleaned.isdigit() and len(cleaned) in (10, 11)


def build_billing_summary(order: Order) -> dict[str, Any]:
    """Build a billing info dict for API responses."""
    return {
        "billing_type": order.billing_type,
        "billing_tc_no": getattr(order, "billing_tc_no", None),
        "billing_full_name": order.billing_full_name,
        "billing_email": order.billing_email,
        "billing_phone": order.billing_phone,
        "billing_company_name": order.billing_company_name,
        "billing_tax_id": order.billing_tax_id,
        "billing_tax_office": order.billing_tax_office,
        "billing_address": order.billing_address,
    }


def snapshot_billing_to_order(order: Order) -> None:
    """Snapshot billing address from shipping if not explicitly set.

    Called at PAID transition (by order_state_machine) to freeze billing data.
    """
    if not order.billing_type:
        order.billing_type = "individual"
    if not order.billing_full_name and order.shipping_address:
        order.billing_full_name = order.shipping_address.get("fullName", "")
    if not order.billing_email and order.shipping_address:
        order.billing_email = order.shipping_address.get("email", "")
    if not order.billing_phone and order.shipping_address:
        order.billing_phone = order.shipping_address.get("phone", "")
    if not order.billing_address and order.shipping_address:
        order.billing_address = {
            "address": order.shipping_address.get("address", ""),
            "city": order.shipping_address.get("city", ""),
            "district": order.shipping_address.get("district", ""),
            "postalCode": order.shipping_address.get("postalCode", ""),
        }


# ---------------------------------------------------------------------------
# Invoice helpers
# ---------------------------------------------------------------------------


async def build_invoice_summary(
    order_id: UUID, db: "AsyncSession",
) -> dict[str, Any] | None:
    """Build invoice summary for order detail response."""
    from sqlalchemy import select

    from app.models.invoice import Invoice, InvoiceStatus

    result = await db.execute(select(Invoice).where(Invoice.order_id == order_id))
    inv = result.scalar_one_or_none()
    if not inv:
        return None
    return {
        "invoice_number": inv.invoice_number,
        "invoice_status": inv.invoice_status,
        "pdf_ready": inv.invoice_status == InvoiceStatus.PDF_READY.value,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "needs_credit_note": inv.needs_credit_note,
        "email_sent": inv.email_sent_at is not None,
        "email_status": inv.email_status,
    }


# ---------------------------------------------------------------------------
# DB query helpers
# ---------------------------------------------------------------------------


async def load_order_pages(order_id: UUID, db: "AsyncSession") -> list[dict[str, Any]]:
    """Load page-level status for an order (separate query, only when requested)."""
    from sqlalchemy import select

    from app.models.order_page import OrderPage

    pages_result = await db.execute(
        select(
            OrderPage.page_number,
            OrderPage.status,
            OrderPage.is_cover,
            OrderPage.preview_image_url,
            OrderPage.image_url,
        )
        .where(OrderPage.order_id == order_id)
        .order_by(OrderPage.page_number)
    )
    return [
        {
            "page_number": r.page_number,
            "status": r.status if isinstance(r.status, str) else r.status.value,
            "is_cover": r.is_cover,
            "preview_image_url": r.preview_image_url,
            "image_url": r.image_url,
        }
        for r in pages_result.all()
    ]


async def load_timeline_events(order: Order, db: "AsyncSession") -> list[dict[str, Any]]:
    """Load timeline events from audit log (separate query, only when requested)."""
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    timeline_result = await db.execute(
        select(
            AuditLog.action,
            AuditLog.details,
            AuditLog.admin_id,
            AuditLog.user_id,
            AuditLog.created_at,
        )
        .where(AuditLog.order_id == order.id, AuditLog.action.like("ORDER_STATUS_%"))
        .order_by(AuditLog.created_at.asc())
    )
    audit_events = timeline_result.all()

    if audit_events:
        return [
            {
                "action": e.action,
                "status": (e.details or {}).get("to_status", e.action.replace("ORDER_STATUS_", "")),
                "from_status": (e.details or {}).get("from_status"),
                "actor": "admin" if e.admin_id else ("system" if not e.user_id else "user"),
                "timestamp": e.created_at.isoformat(),
            }
            for e in audit_events
        ]

    # Fallback for old orders without audit logs
    status_val = order.status.value if hasattr(order.status, "value") else str(order.status)
    events: list[dict[str, Any]] = [
        {
            "action": "ORDER_STATUS_DRAFT",
            "status": "DRAFT",
            "from_status": None,
            "actor": "system",
            "timestamp": order.created_at.isoformat(),
        }
    ]
    if status_val != "DRAFT":
        ts = order.updated_at.isoformat() if order.updated_at else order.created_at.isoformat()
        if order.delivered_at and status_val == "DELIVERED":
            ts = order.delivered_at.isoformat()
        events.append({
            "action": f"ORDER_STATUS_{status_val}",
            "status": status_val,
            "from_status": None,
            "actor": "system",
            "timestamp": ts,
        })
    return events
