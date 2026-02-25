"""Add dedication page support.

- page_templates: dedication_default_text column
- story_previews: dedication_note column
- orders: dedication_note column

Revision ID: 039_dedication_page
Revises: 038_promo_codes
Create Date: 2026-02-12
"""

from alembic import op
import sqlalchemy as sa

revision = "039_dedication_page"
down_revision = "038_promo_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PageTemplate: dedication default text template
    op.add_column(
        "page_templates",
        sa.Column("dedication_default_text", sa.Text(), nullable=True),
    )

    # StoryPreview: dedication note from parent
    op.add_column(
        "story_previews",
        sa.Column("dedication_note", sa.Text(), nullable=True),
    )

    # Order: dedication note from parent
    op.add_column(
        "orders",
        sa.Column("dedication_note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "dedication_note")
    op.drop_column("story_previews", "dedication_note")
    op.drop_column("page_templates", "dedication_default_text")
