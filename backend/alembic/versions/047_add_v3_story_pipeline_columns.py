"""Add V3 story pipeline columns: scenario_bible, magic_items, blueprint_json.

- scenarios.scenario_bible: JSONB — cultural facts pack for location-based generation
- orders.magic_items: JSONB — user-selected magic items
- orders.blueprint_json: JSONB — PASS-0 blueprint for audit/debugging

Revision ID: 047_v3_story_pipeline
Revises: 046_consent_records
Create Date: 2026-02-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "047_v3_story_pipeline"
down_revision: str = "046_consent_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # scenarios.scenario_bible
    op.add_column(
        "scenarios",
        sa.Column(
            "scenario_bible",
            JSONB,
            nullable=True,
            comment="V3: Cultural facts pack, side characters, puzzle types, tone rules",
        ),
    )

    # orders.magic_items
    op.add_column(
        "orders",
        sa.Column(
            "magic_items",
            JSONB,
            nullable=True,
            comment="V3: User-selected magic items",
        ),
    )

    # orders.blueprint_json
    op.add_column(
        "orders",
        sa.Column(
            "blueprint_json",
            JSONB,
            nullable=True,
            comment="V3: PASS-0 blueprint for audit",
        ),
    )


def downgrade() -> None:
    op.drop_column("orders", "blueprint_json")
    op.drop_column("orders", "magic_items")
    op.drop_column("scenarios", "scenario_bible")
