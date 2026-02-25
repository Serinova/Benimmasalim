"""Add product override fields to scenarios table.

Revision ID: 086_add_scenario_product_overrides
Revises: 085_add_scenario_marketing_fields
Create Date: 2026-02-25

Adds scenario-level overrides for product pricing and templates.
Priority chain: scenario override > product default > system fallback.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "086_add_scenario_product_overrides"
down_revision: str | None = "085_add_scenario_marketing_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Price overrides
    op.add_column(
        "scenarios",
        sa.Column("price_override_base", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("price_override_extra_page", sa.Numeric(10, 2), nullable=True),
    )
    # Template ID overrides (stored as varchar UUID strings)
    op.add_column(
        "scenarios",
        sa.Column("cover_template_id_override", sa.String(36), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("inner_template_id_override", sa.String(36), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("back_template_id_override", sa.String(36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scenarios", "back_template_id_override")
    op.drop_column("scenarios", "inner_template_id_override")
    op.drop_column("scenarios", "cover_template_id_override")
    op.drop_column("scenarios", "price_override_extra_page")
    op.drop_column("scenarios", "price_override_base")
