"""Add app_settings table and products.vat_rate column.

- app_settings: admin-configurable key-value store (invoice company info, etc.)
- products.vat_rate: per-product VAT rate (KDV oranı)

Revision ID: 112_app_settings_and_product_vat
Revises: 111_add_billing_tc_no
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "112_app_settings_and_product_vat"
down_revision = "111_add_billing_tc_no"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "vat_rate",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="10.00",
            comment="KDV oranı (%) — fiziksel kitap için varsayılan %10",
        ),
    )


def downgrade() -> None:
    op.drop_column("products", "vat_rate")
    op.drop_table("app_settings")
