"""Set cover_title_source to 'gemini' for all existing page templates.

Revision ID: 074_set_cover_title_source_gemini
Revises: 073_add_cover_title_source_to_page_templates
Create Date: 2026-02-24
"""

from collections.abc import Sequence

from alembic import op

revision: str = "074_set_cover_title_source_gemini"
down_revision: str = "073_add_cover_title_source_to_page_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Tüm mevcut template'leri gemini moduna geçir
    op.execute("""
        UPDATE page_templates
        SET cover_title_source = 'gemini'
        WHERE cover_title_source = 'overlay'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE page_templates
        SET cover_title_source = 'overlay'
        WHERE cover_title_source = 'gemini'
    """)
