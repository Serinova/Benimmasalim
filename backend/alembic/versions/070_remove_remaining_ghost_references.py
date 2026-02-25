"""Remove remaining ghost references from scenario story prompts for child safety.

Revision ID: 070_remove_remaining_ghost_references
Revises: 069_relax_cover_prompt_templates
Create Date: 2026-02-23
"""
from collections.abc import Sequence

from alembic import op

revision: str = "070_remove_remaining_ghost_references"
down_revision: str | None = "069_relax_cover_prompt_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Remove "hayalet" references from story prompts (especially Galata, Tac Mahal, Abu Simbel)
    op.execute(
        """
        UPDATE scenarios 
        SET story_prompt_tr = REPLACE(story_prompt_tr, 'hayaleti', 'hatırası')
        WHERE story_prompt_tr LIKE '%hayaleti%'
        """
    )
    op.execute(
        """
        UPDATE scenarios 
        SET story_prompt_tr = REPLACE(story_prompt_tr, 'Hayaleti', 'Sesi')
        WHERE story_prompt_tr LIKE '%Hayaleti%'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE scenarios 
        SET story_prompt_tr = REPLACE(story_prompt_tr, 'hatırası', 'hayaleti')
        WHERE story_prompt_tr LIKE '%hatırası%'
        """
    )
    op.execute(
        """
        UPDATE scenarios 
        SET story_prompt_tr = REPLACE(story_prompt_tr, 'Sesi', 'Hayaleti')
        WHERE story_prompt_tr LIKE '%Sesi%' AND name ILIKE '%Galata%'
        """
    )
