"""Admin Accounting / Revenue Module.

Provides detailed financial reporting across both payment flows:
  - Trial / "Try Before You Buy" flow: story_previews table
  - Legacy Order flow: orders table

All monetary values are in TL (Turkish Lira).
VAT is computed as KDV-dahil (inclusive): vat = final * rate / (100 + rate)
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import case, func, literal, select, union_all

from app.api.v1.deps import AdminUser, DbSession
from app.models.order import Order, OrderStatus
from app.models.story_preview import PreviewStatus, StoryPreview

router = APIRouter()
logger = structlog.get_logger()

# ── Helpers ──────────────────────────────────────────────────────────────────

_PAID_ORDER_STATUSES = (
    OrderStatus.PAID.value,
    OrderStatus.PROCESSING.value,
    OrderStatus.READY_FOR_PRINT.value,
    OrderStatus.SHIPPED.value,
    OrderStatus.DELIVERED.value,
    OrderStatus.REFUNDED.value,
)

_PAID_PREVIEW_STATUSES = (
    PreviewStatus.COMPLETING.value,
    PreviewStatus.COMPLETED.value,
    PreviewStatus.CONFIRMED.value,
)

_DEFAULT_VAT_RATE = Decimal("10")  # %10 KDV (dahil)


def _to_date(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


def _to_date_end(d: date | None) -> datetime | None:
    if d is None:
        return None
    return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=UTC)


def _vat(amount: Decimal, rate: Decimal = _DEFAULT_VAT_RATE) -> Decimal:
    if not amount:
        return Decimal("0")
    return (amount * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"))


def _safe_decimal(v: Any) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


# ── /summary ─────────────────────────────────────────────────────────────────


@router.get("/summary")
async def accounting_summary(
    db: DbSession,
    admin: AdminUser,
    from_date: date | None = Query(None, alias="from_date"),
    to_date: date | None = Query(None, alias="to_date"),
) -> dict[str, Any]:
    """Overall financial summary for the given date range."""

    # ── Story Preview (trial flow) ──
    preview_q = select(
        func.count(StoryPreview.id).label("cnt"),
        func.coalesce(func.sum(StoryPreview.product_price), 0).label("gross"),
        func.coalesce(func.sum(StoryPreview.discount_applied_amount), 0).label("discount"),
        func.count(StoryPreview.promo_code_text).label("promo_cnt"),
        func.sum(
            case((StoryPreview.has_audio_book == True, 1), else_=0)  # noqa: E712
        ).label("audio_cnt"),
        func.sum(
            case((StoryPreview.has_coloring_book == True, 1), else_=0)  # noqa: E712
        ).label("coloring_cnt"),
    ).where(StoryPreview.status.in_(_PAID_PREVIEW_STATUSES))

    if from_date:
        preview_q = preview_q.where(StoryPreview.payment_completed_at >= _to_date(from_date))
    if to_date:
        preview_q = preview_q.where(StoryPreview.payment_completed_at <= _to_date_end(to_date))

    prev_row = (await db.execute(preview_q)).one()

    # ── Order (legacy flow) ──
    order_q = select(
        func.count(Order.id).label("cnt"),
        func.coalesce(func.sum(Order.subtotal_amount), 0).label("gross"),
        func.coalesce(func.sum(Order.discount_applied_amount), 0).label("discount"),
        func.count(Order.promo_code_text).label("promo_cnt"),
        func.sum(case((Order.has_audio_book == True, 1), else_=0)).label("audio_cnt"),  # noqa: E712
        func.sum(case((Order.is_coloring_book == True, 1), else_=0)).label("coloring_cnt"),  # noqa: E712
        func.coalesce(
            func.sum(
                case(
                    (Order.status == OrderStatus.REFUNDED.value, Order.final_amount),
                    else_=0,
                )
            ),
            0,
        ).label("refund_total"),
    ).where(Order.status.in_(_PAID_ORDER_STATUSES))

    if from_date:
        order_q = order_q.where(Order.updated_at >= _to_date(from_date))
    if to_date:
        order_q = order_q.where(Order.updated_at <= _to_date_end(to_date))

    ord_row = (await db.execute(order_q)).one()

    # ── Aggregate ──
    gross = _safe_decimal(prev_row.gross) + _safe_decimal(ord_row.gross)
    discount = _safe_decimal(prev_row.discount) + _safe_decimal(ord_row.discount)
    net = gross - discount
    vat = _vat(net)
    order_count = int(prev_row.cnt or 0) + int(ord_row.cnt or 0)
    promo_cnt = int(prev_row.promo_cnt or 0) + int(ord_row.promo_cnt or 0)
    audio_cnt = int(prev_row.audio_cnt or 0) + int(ord_row.audio_cnt or 0)
    coloring_cnt = int(prev_row.coloring_cnt or 0) + int(ord_row.coloring_cnt or 0)
    refund_total = _safe_decimal(ord_row.refund_total)

    return {
        "gross_revenue": float(gross),
        "total_discount": float(discount),
        "net_revenue": float(net),
        "vat_amount": float(vat),
        "revenue_ex_vat": float(net - vat),
        "refund_total": float(refund_total),
        "promo_savings": float(discount),
        "order_count": order_count,
        "promo_used_count": promo_cnt,
        "audio_book_count": audio_cnt,
        "coloring_book_count": coloring_cnt,
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
    }


# ── /revenue-over-time ───────────────────────────────────────────────────────


@router.get("/revenue-over-time")
async def revenue_over_time(
    db: DbSession,
    admin: AdminUser,
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    from_date: date | None = Query(None, alias="from_date"),
    to_date: date | None = Query(None, alias="to_date"),
) -> list[dict[str, Any]]:
    """Time-series revenue grouped by day / week / month."""

    trunc_map = {"daily": "day", "weekly": "week", "monthly": "month"}
    trunc = trunc_map[period]

    # Preview flow subquery
    prev_date_col = func.date_trunc(trunc, StoryPreview.payment_completed_at).label("period")
    preview_sq = (
        select(
            prev_date_col,
            func.coalesce(func.sum(StoryPreview.product_price), 0).label("gross"),
            func.coalesce(func.sum(StoryPreview.discount_applied_amount), 0).label("discount"),
            func.count(StoryPreview.id).label("cnt"),
        )
        .where(
            StoryPreview.status.in_(_PAID_PREVIEW_STATUSES),
            StoryPreview.payment_completed_at.isnot(None),
        )
        .group_by(prev_date_col)
    )
    if from_date:
        preview_sq = preview_sq.where(StoryPreview.payment_completed_at >= _to_date(from_date))
    if to_date:
        preview_sq = preview_sq.where(StoryPreview.payment_completed_at <= _to_date_end(to_date))

    # Order flow subquery
    ord_date_col = func.date_trunc(trunc, Order.updated_at).label("period")
    order_sq = (
        select(
            ord_date_col,
            func.coalesce(func.sum(Order.subtotal_amount), 0).label("gross"),
            func.coalesce(func.sum(Order.discount_applied_amount), 0).label("discount"),
            func.count(Order.id).label("cnt"),
        )
        .where(Order.status.in_(_PAID_ORDER_STATUSES))
        .group_by(ord_date_col)
    )
    if from_date:
        order_sq = order_sq.where(Order.updated_at >= _to_date(from_date))
    if to_date:
        order_sq = order_sq.where(Order.updated_at <= _to_date_end(to_date))

    # UNION and aggregate
    combined = union_all(preview_sq, order_sq).subquery("combined")

    agg = (
        select(
            combined.c.period,
            func.sum(combined.c.gross).label("gross"),
            func.sum(combined.c.discount).label("discount"),
            func.sum(combined.c.cnt).label("cnt"),
        )
        .group_by(combined.c.period)
        .order_by(combined.c.period)
    )

    rows = (await db.execute(agg)).all()

    result: list[dict[str, Any]] = []
    for row in rows:
        if row.period is None:
            continue
        g = _safe_decimal(row.gross)
        d = _safe_decimal(row.discount)
        net = g - d
        result.append(
            {
                "period": row.period.strftime("%Y-%m-%d"),
                "gross": float(g),
                "discount": float(d),
                "net": float(net),
                "count": int(row.cnt or 0),
            }
        )
    return result


# ── /by-product ──────────────────────────────────────────────────────────────


@router.get("/by-product")
async def revenue_by_product(
    db: DbSession,
    admin: AdminUser,
    from_date: date | None = Query(None, alias="from_date"),
    to_date: date | None = Query(None, alias="to_date"),
) -> list[dict[str, Any]]:
    """Revenue breakdown by product name (both trial and legacy order flows)."""
    from app.models.product import Product

    # Preview flow
    prev_q = select(
        func.coalesce(StoryPreview.product_name, literal("Bilinmeyen Ürün")).label("product_name"),
        func.count(StoryPreview.id).label("cnt"),
        func.coalesce(func.sum(StoryPreview.product_price), 0).label("gross"),
        func.coalesce(func.sum(StoryPreview.discount_applied_amount), 0).label("discount"),
    ).where(StoryPreview.status.in_(_PAID_PREVIEW_STATUSES))
    if from_date:
        prev_q = prev_q.where(StoryPreview.payment_completed_at >= _to_date(from_date))
    if to_date:
        prev_q = prev_q.where(StoryPreview.payment_completed_at <= _to_date_end(to_date))
    prev_q = prev_q.group_by(StoryPreview.product_name)

    # Legacy order flow — JOIN products to get name
    ord_q = (
        select(
            func.coalesce(Product.name, literal("Bilinmeyen Ürün")).label("product_name"),
            func.count(Order.id).label("cnt"),
            func.coalesce(func.sum(Order.subtotal_amount), 0).label("gross"),
            func.coalesce(func.sum(Order.discount_applied_amount), 0).label("discount"),
        )
        .outerjoin(Product, Product.id == Order.product_id)
        .where(Order.status.in_(_PAID_ORDER_STATUSES))
    )
    if from_date:
        ord_q = ord_q.where(Order.updated_at >= _to_date(from_date))
    if to_date:
        ord_q = ord_q.where(Order.updated_at <= _to_date_end(to_date))
    ord_q = ord_q.group_by(Product.name)

    prev_rows = (await db.execute(prev_q)).all()
    ord_rows = (await db.execute(ord_q)).all()

    # Merge by product_name
    merged: dict[str, dict] = {}
    for r in list(prev_rows) + list(ord_rows):
        name = r.product_name or "Bilinmeyen Ürün"
        if name not in merged:
            merged[name] = {"count": 0, "gross": Decimal("0"), "discount": Decimal("0")}
        merged[name]["count"] += int(r.cnt or 0)
        merged[name]["gross"] += _safe_decimal(r.gross)
        merged[name]["discount"] += _safe_decimal(r.discount)

    result: list[dict[str, Any]] = []
    for name, m in merged.items():
        g = m["gross"]
        d = m["discount"]
        net = g - d
        result.append(
            {
                "product_name": name,
                "count": m["count"],
                "gross": float(g),
                "discount": float(d),
                "net": float(net),
            }
        )

    result.sort(key=lambda x: x["net"], reverse=True)
    return result


# ── /promo-analysis ──────────────────────────────────────────────────────────


@router.get("/promo-analysis")
async def promo_analysis(
    db: DbSession,
    admin: AdminUser,
    from_date: date | None = Query(None, alias="from_date"),
    to_date: date | None = Query(None, alias="to_date"),
) -> list[dict[str, Any]]:
    """Promo code usage and discount impact."""
    from app.models.promo_code import PromoCode

    # Preview flow promo stats
    prev_q = select(
        StoryPreview.promo_code_text.label("code"),
        func.count(StoryPreview.id).label("uses"),
        func.coalesce(func.sum(StoryPreview.discount_applied_amount), 0).label("total_discount"),
        func.coalesce(func.sum(StoryPreview.product_price), 0).label("gross_before_discount"),
    ).where(
        StoryPreview.status.in_(_PAID_PREVIEW_STATUSES),
        StoryPreview.promo_code_text.isnot(None),
    )
    if from_date:
        prev_q = prev_q.where(StoryPreview.payment_completed_at >= _to_date(from_date))
    if to_date:
        prev_q = prev_q.where(StoryPreview.payment_completed_at <= _to_date_end(to_date))
    prev_q = prev_q.group_by(StoryPreview.promo_code_text)

    prev_rows = (await db.execute(prev_q)).all()

    # Order flow promo stats
    ord_q = select(
        Order.promo_code_text.label("code"),
        func.count(Order.id).label("uses"),
        func.coalesce(func.sum(Order.discount_applied_amount), 0).label("total_discount"),
        func.coalesce(func.sum(Order.subtotal_amount), 0).label("gross_before_discount"),
    ).where(
        Order.status.in_(_PAID_ORDER_STATUSES),
        Order.promo_code_text.isnot(None),
    )
    if from_date:
        ord_q = ord_q.where(Order.updated_at >= _to_date(from_date))
    if to_date:
        ord_q = ord_q.where(Order.updated_at <= _to_date_end(to_date))
    ord_q = ord_q.group_by(Order.promo_code_text)

    ord_rows = (await db.execute(ord_q)).all()

    # Merge by code
    merged: dict[str, dict] = {}
    for r in list(prev_rows) + list(ord_rows):
        code = (r.code or "").upper()
        if not code:
            continue
        if code not in merged:
            merged[code] = {"code": code, "uses": 0, "total_discount": Decimal("0"), "gross": Decimal("0")}
        merged[code]["uses"] += int(r.uses or 0)
        merged[code]["total_discount"] += _safe_decimal(r.total_discount)
        merged[code]["gross"] += _safe_decimal(r.gross_before_discount)

    # Enrich with PromoCode metadata
    if merged:
        pc_rows = (
            await db.execute(
                select(PromoCode.code, PromoCode.discount_type, PromoCode.discount_value, PromoCode.is_active)
                .where(PromoCode.code.in_(list(merged.keys())))
            )
        ).all()
        pc_map = {r.code: r for r in pc_rows}
    else:
        pc_map = {}

    result: list[dict[str, Any]] = []
    for code, m in merged.items():
        pc = pc_map.get(code)
        gross = m["gross"]
        disc = m["total_discount"]
        discount_pct = float(disc / gross * 100) if gross else 0.0
        result.append(
            {
                "code": code,
                "uses": m["uses"],
                "total_discount": float(disc),
                "gross_before_discount": float(gross),
                "discount_pct": round(discount_pct, 1),
                "discount_type": pc.discount_type if pc else None,
                "discount_value": float(pc.discount_value) if pc else None,
                "is_active": pc.is_active if pc else None,
            }
        )

    result.sort(key=lambda x: x["total_discount"], reverse=True)
    return result


# ── /transactions ────────────────────────────────────────────────────────────


@router.get("/transactions")
async def transactions(
    db: DbSession,
    admin: AdminUser,
    from_date: date | None = Query(None, alias="from_date"),
    to_date: date | None = Query(None, alias="to_date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = Query(None),
) -> dict[str, Any]:
    """Detailed transaction ledger — all paid orders paginated."""

    offset = (page - 1) * limit

    # Preview flow
    prev_q = select(
        StoryPreview.id.label("id"),
        StoryPreview.parent_name.label("customer_name"),
        StoryPreview.parent_email.label("customer_email"),
        StoryPreview.child_name.label("child_name"),
        StoryPreview.product_name.label("product_name"),
        StoryPreview.product_price.label("gross"),
        StoryPreview.discount_applied_amount.label("discount"),
        StoryPreview.promo_code_text.label("promo_code"),
        StoryPreview.payment_completed_at.label("paid_at"),
        StoryPreview.payment_reference.label("payment_ref"),
        StoryPreview.status.label("status"),
        literal("preview").label("source"),
        StoryPreview.has_audio_book.label("has_audio"),
        StoryPreview.has_coloring_book.label("has_coloring"),
    ).where(StoryPreview.status.in_(_PAID_PREVIEW_STATUSES))

    if from_date:
        prev_q = prev_q.where(StoryPreview.payment_completed_at >= _to_date(from_date))
    if to_date:
        prev_q = prev_q.where(StoryPreview.payment_completed_at <= _to_date_end(to_date))
    if search:
        like = f"%{search}%"
        prev_q = prev_q.where(
            StoryPreview.parent_email.ilike(like)
            | StoryPreview.parent_name.ilike(like)
            | StoryPreview.child_name.ilike(like)
        )

    # Order flow
    ord_q = select(
        Order.id.label("id"),
        Order.billing_full_name.label("customer_name"),
        Order.billing_email.label("customer_email"),
        Order.child_name.label("child_name"),
        literal("Sipariş").label("product_name"),
        Order.subtotal_amount.label("gross"),
        Order.discount_applied_amount.label("discount"),
        Order.promo_code_text.label("promo_code"),
        Order.updated_at.label("paid_at"),
        Order.payment_id.label("payment_ref"),
        Order.status.label("status"),
        literal("order").label("source"),
        Order.has_audio_book.label("has_audio"),
        Order.is_coloring_book.label("has_coloring"),
    ).where(Order.status.in_(_PAID_ORDER_STATUSES))

    if from_date:
        ord_q = ord_q.where(Order.updated_at >= _to_date(from_date))
    if to_date:
        ord_q = ord_q.where(Order.updated_at <= _to_date_end(to_date))
    if search:
        like = f"%{search}%"
        ord_q = ord_q.where(
            Order.billing_email.ilike(like)
            | Order.billing_full_name.ilike(like)
            | Order.child_name.ilike(like)
        )

    combined = union_all(prev_q, ord_q).subquery("txn")

    # Count total
    count_q = select(func.count()).select_from(combined)
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    data_q = (
        select(combined)
        .order_by(combined.c.paid_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(data_q)).all()

    items: list[dict[str, Any]] = []
    for r in rows:
        gross = _safe_decimal(r.gross)
        disc = _safe_decimal(r.discount)
        net = gross - disc
        items.append(
            {
                "id": str(r.id),
                "customer_name": r.customer_name or "-",
                "customer_email": r.customer_email or "-",
                "child_name": r.child_name or "-",
                "product_name": r.product_name or "-",
                "gross": float(gross),
                "discount": float(disc),
                "net": float(net),
                "vat": float(_vat(net)),
                "promo_code": r.promo_code,
                "paid_at": r.paid_at.isoformat() if r.paid_at else None,
                "payment_ref": r.payment_ref,
                "status": r.status,
                "source": r.source,
                "has_audio": bool(r.has_audio),
                "has_coloring": bool(r.has_coloring),
            }
        )

    return {"items": items, "total": total, "page": page, "limit": limit}


# ── /export-csv ───────────────────────────────────────────────────────────────


@router.get("/export-csv")
async def export_transactions_csv(
    db: DbSession,
    admin: AdminUser,
    from_date: date | None = Query(None, alias="from_date"),
    to_date: date | None = Query(None, alias="to_date"),
) -> Any:
    """Download all transactions as CSV (no pagination, admin-only)."""
    import csv
    import io

    from fastapi.responses import StreamingResponse

    # Reuse transactions logic with max limit
    result = await transactions(
        db=db,
        admin=admin,
        from_date=from_date,
        to_date=to_date,
        page=1,
        limit=10000,
        search=None,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Tarih", "Müşteri Adı", "E-posta", "Çocuk", "Ürün",
        "Brüt (TL)", "İndirim (TL)", "Net (TL)", "KDV (TL)",
        "Kupon Kodu", "Ödeme Ref", "Durum", "Kaynak",
    ])
    for txn in result["items"]:
        writer.writerow([
            txn["paid_at"] or "",
            txn["customer_name"],
            txn["customer_email"],
            txn["child_name"],
            txn["product_name"],
            f"{txn['gross']:.2f}",
            f"{txn['discount']:.2f}",
            f"{txn['net']:.2f}",
            f"{txn['vat']:.2f}",
            txn["promo_code"] or "",
            txn["payment_ref"] or "",
            txn["status"],
            txn["source"],
        ])

    output.seek(0)
    filename = f"islem_defteri_{(from_date or date.today()).isoformat()}__{(to_date or date.today()).isoformat()}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),  # utf-8-sig for Excel compatibility
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
