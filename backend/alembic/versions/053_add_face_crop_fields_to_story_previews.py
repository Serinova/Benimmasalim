"""Add face_crop_url and face_embedding to story_previews.

Supports PuLID face similarity optimization:
- face_crop_url: cropped face image for better PuLID identity injection
- face_embedding: InsightFace 512-d embedding for post-generation quality gate

Revision ID: 053_face_crop_fields
Revises: 052_page_regenerate_count
Create Date: 2026-02-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "053_face_crop_fields"
down_revision: str = "052_page_regenerate_count"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("face_crop_url", sa.Text(), nullable=True),
    )
    op.add_column(
        "story_previews",
        sa.Column("face_embedding", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "face_embedding")
    op.drop_column("story_previews", "face_crop_url")
