"""Add promo_codes table and order discount fields.

Revision ID: 038_promo_codes
Revises: 037_cover_effect
Create Date: 2026-02-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "038_promo_codes"
down_revision: str | None = "037_cover_effect"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- promo_codes table ---
    op.create_table(
        "promo_codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("usage_limit", sa.Integer, nullable=False, server_default="1"),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("min_order_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_discount_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        # Check constraints
        sa.CheckConstraint("used_count >= 0", name="promo_used_count_non_negative"),
        sa.CheckConstraint("usage_limit >= 1", name="promo_usage_limit_positive"),
        sa.CheckConstraint("discount_value > 0", name="promo_discount_value_positive"),
        sa.CheckConstraint(
            "discount_type IN ('PERCENT', 'AMOUNT')",
            name="promo_valid_discount_type",
        ),
        sa.CheckConstraint(
            "(discount_type != 'PERCENT') OR (discount_value >= 1 AND discount_value <= 100)",
            name="promo_percent_range",
        ),
    )

    op.create_index("idx_promo_codes_code", "promo_codes", ["code"])
    op.create_index("idx_promo_codes_active", "promo_codes", ["is_active", "valid_until"])

    # --- order promo snapshot columns ---
    op.add_column(
        "orders",
        sa.Column(
            "promo_code_id",
            UUID(as_uuid=True),
            sa.ForeignKey("promo_codes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("orders", sa.Column("promo_code_text", sa.String(50), nullable=True))
    op.add_column("orders", sa.Column("promo_discount_type", sa.String(20), nullable=True))
    op.add_column("orders", sa.Column("promo_discount_value", sa.Numeric(10, 2), nullable=True))
    op.add_column("orders", sa.Column("discount_applied_amount", sa.Numeric(10, 2), nullable=True))
    op.add_column("orders", sa.Column("subtotal_amount", sa.Numeric(10, 2), nullable=True))
    op.add_column("orders", sa.Column("final_amount", sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "final_amount")
    op.drop_column("orders", "subtotal_amount")
    op.drop_column("orders", "discount_applied_amount")
    op.drop_column("orders", "promo_discount_value")
    op.drop_column("orders", "promo_discount_type")
    op.drop_column("orders", "promo_code_text")
    op.drop_column("orders", "promo_code_id")

    op.drop_index("idx_promo_codes_active", table_name="promo_codes")
    op.drop_index("idx_promo_codes_code", table_name="promo_codes")
    op.drop_table("promo_codes")
