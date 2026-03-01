"""Gap-free invoice numbering via a counter table.

PostgreSQL sequences do NOT roll back on transaction failure, which means
invoice numbers can be skipped.  Turkish tax law requires gap-free numbering.

This module uses an ``invoice_serial_counters`` table with one row per year.
The row is locked with SELECT … FOR UPDATE inside the caller's transaction,
so if the transaction rolls back the counter is never incremented → no gaps.

Usage::

    from app.services.invoice_number_service import next_invoice_number
    invoice_number = await next_invoice_number(db)   # "BM-2026-000001"
"""

from datetime import UTC, datetime

import sqlalchemy as sa
import structlog
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

logger = structlog.get_logger()


class InvoiceSerialCounter(Base):
    """One row per year — stores the last used serial for that year.

    The row is locked with ``FOR UPDATE`` so concurrent transactions queue up
    and each gets a unique, gap-free serial.
    """

    __tablename__ = "invoice_serial_counters"

    year = Column(Integer, primary_key=True, autoincrement=False)
    last_serial = Column(Integer, nullable=False, default=0)
    prefix = Column(String(10), nullable=False, default="BM")


async def next_invoice_number(
    db: AsyncSession,
    *,
    prefix: str = "BM",
) -> str:
    """Generate the next gap-free invoice number within the caller's transaction.

    Steps:
    1. SELECT … FOR UPDATE the counter row for the current year.
       This blocks concurrent callers until our transaction commits/rolls back.
    2. Increment ``last_serial`` by 1.
    3. Return the formatted invoice number.

    If the year row doesn't exist yet, INSERT it with ``last_serial = 0``
    first (with ON CONFLICT DO NOTHING for race-safety), then retry the lock.

    IMPORTANT: The caller must NOT commit between calling this function and
    inserting the Invoice row — both must be in the same transaction so that
    a rollback also rolls back the counter increment.
    """
    year = datetime.now(UTC).year

    # Ensure the year row exists (idempotent)
    await db.execute(
        sa.text(
            "INSERT INTO invoice_serial_counters (year, last_serial, prefix) "
            "VALUES (:year, 0, :prefix) "
            "ON CONFLICT (year) DO NOTHING"
        ),
        {"year": year, "prefix": prefix},
    )
    # Flush so the row is visible to the FOR UPDATE below
    await db.flush()

    # Lock the row and increment atomically
    result = await db.execute(
        sa.text(
            "UPDATE invoice_serial_counters "
            "SET last_serial = last_serial + 1 "
            "WHERE year = :year "
            "RETURNING last_serial"
        ),
        {"year": year},
    )
    serial = result.scalar_one()

    invoice_number = f"{prefix}-{year}-{serial:06d}"
    logger.info(
        "invoice_number_generated",
        invoice_number=invoice_number,
        year=year,
        serial=serial,
    )
    return invoice_number
