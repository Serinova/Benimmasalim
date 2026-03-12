"""Add character_description to story_previews.

Caches the AI-Director character description so remaining pages
don't need to re-analyze the child photo (saves ~10-20s per book).
"""

from alembic import op
import sqlalchemy as sa

revision = "129_char_desc"
down_revision = "128_add_photo_storybook_style"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "story_previews",
        sa.Column("character_description", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("story_previews", "character_description")
