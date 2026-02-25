"""Add consent_records table for KVKK compliance.

Stores immutable consent records: one row per consent action (given/withdrawn).

Revision ID: 046_consent_records
Revises: vs_display_names_001
Create Date: 2026-02-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

revision: str = "046_consent_records"
down_revision: str = "vs_display_names_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consent_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("consent_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("ip_address", INET, nullable=True),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("idx_consent_email", "consent_records", ["email"], postgresql_where="email IS NOT NULL")
    op.create_index("idx_consent_type_action", "consent_records", ["consent_type", "action", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_consent_type_action", table_name="consent_records")
    op.drop_index("idx_consent_email", table_name="consent_records")
    op.drop_table("consent_records")
