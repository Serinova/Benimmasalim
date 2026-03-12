"""Set cover_title_source to 'gemini' for all page templates.

Gemini 2.0 Flash now renders book titles natively as part of the cover
illustration. PIL overlay is no longer needed.

Revision ID: 131_set_cover_title_source_gemini
Revises: 130_set_cover_title_source_overlay
Create Date: 2026-03-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "131_set_cover_title_source_gemini"
down_revision: str = "130_set_cover_title_source_overlay"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Tüm template'leri gemini moduna geçir — Gemini native title rendering
    op.execute("""
        UPDATE page_templates
        SET cover_title_source = 'gemini'
        WHERE cover_title_source = 'overlay'
           OR cover_title_source IS NULL
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE page_templates
        SET cover_title_source = 'overlay'
        WHERE cover_title_source = 'gemini'
    """)
