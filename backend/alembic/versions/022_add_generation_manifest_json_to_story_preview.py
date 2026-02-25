"""Add generation_manifest_json to story_previews.

Per-page manifest: provider, model, steps, guidance, size, is_cover,
prompt_hash, negative_hash, reference_image_used. Proves pipeline consistency.

Revision ID: 022_manifest
Revises: 021_prompt_debug
Create Date: 2026-02-05

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "022_manifest"
down_revision: str = "020_child_photo_url"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("generation_manifest_json", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "generation_manifest_json")
