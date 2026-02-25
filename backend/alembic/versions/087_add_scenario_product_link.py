"""Add linked_product_id and extended override fields to scenarios.

Revision ID: 087_add_scenario_product_link
Revises: 086_add_scenario_product_overrides
Create Date: 2026-02-25

Adds:
- linked_product_id: FK to products — base product whose settings the scenario inherits
- ai_config_id_override: override Product.ai_config_id
- paper_type_override, paper_finish_override: override paper settings
- cover_type_override, lamination_override: override cover settings
- orientation_override: override book orientation
- min_page_count_override, max_page_count_override: override page count limits
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "087_add_scenario_product_link"
down_revision: str | None = "086_add_scenario_product_overrides"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Linked product FK
    op.add_column(
        "scenarios",
        sa.Column("linked_product_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_scenarios_linked_product",
        "scenarios",
        "products",
        ["linked_product_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # AI config override
    op.add_column(
        "scenarios",
        sa.Column("ai_config_id_override", sa.String(36), nullable=True),
    )

    # Paper overrides
    op.add_column(
        "scenarios",
        sa.Column("paper_type_override", sa.String(100), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("paper_finish_override", sa.String(50), nullable=True),
    )

    # Cover overrides
    op.add_column(
        "scenarios",
        sa.Column("cover_type_override", sa.String(50), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("lamination_override", sa.String(50), nullable=True),
    )

    # Orientation override
    op.add_column(
        "scenarios",
        sa.Column("orientation_override", sa.String(20), nullable=True),
    )

    # Page count overrides
    op.add_column(
        "scenarios",
        sa.Column("min_page_count_override", sa.Integer(), nullable=True),
    )
    op.add_column(
        "scenarios",
        sa.Column("max_page_count_override", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_constraint("fk_scenarios_linked_product", "scenarios", type_="foreignkey")
    op.drop_column("scenarios", "linked_product_id")
    op.drop_column("scenarios", "ai_config_id_override")
    op.drop_column("scenarios", "paper_type_override")
    op.drop_column("scenarios", "paper_finish_override")
    op.drop_column("scenarios", "cover_type_override")
    op.drop_column("scenarios", "lamination_override")
    op.drop_column("scenarios", "orientation_override")
    op.drop_column("scenarios", "min_page_count_override")
    op.drop_column("scenarios", "max_page_count_override")
