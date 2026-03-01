"""Add billing_data JSONB column to story_previews for trial-based checkout billing info.

Revision ID: 103_add_billing_data_to_story_previews
Revises: 102_invoice_download_tokens
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "103_add_billing_data_to_story_previews"
down_revision = "102_invoice_download_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("story_previews", sa.Column("billing_data", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("story_previews", "billing_data")
