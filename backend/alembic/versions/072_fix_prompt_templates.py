"""Fix prompt_templates content_en texts to leave empty space for text.

Revision ID: 055_fix_prompt_templates
Revises: 054_rebuild_prompt_templates
Create Date: 2026-02-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "072_fix_prompt_templates"
down_revision: str = "071_fix_incompatible_learning_outcomes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Update COVER
    op.execute("""
        UPDATE prompt_templates 
        SET content_en = 'A young child wearing {clothing_description}. {scene_description}. CRITICAL COVER LAYOUT: Leave massive empty negative space / clear sky at the top 30% of the image for the book title. Do not draw important elements or the child''s head at the very top. CRITICAL: Do NOT include ANY text, titles, letters, words, or typography anywhere in the image.' 
        WHERE key = 'COVER_TEMPLATE'
    """)
    
    # Update INNER
    op.execute("""
        UPDATE prompt_templates 
        SET content_en = 'A young child wearing {clothing_description}. {scene_description}. Ensure clear areas in the environment where text can be placed without obscuring the main action. Do NOT include ANY text, letters, words, or watermarks.' 
        WHERE key = 'INNER_TEMPLATE'
    """)


def downgrade() -> None:
    # Revert to previous basic templates
    op.execute("""
        UPDATE prompt_templates 
        SET content_en = 'A young child wearing {clothing_description}. {scene_description}. CRITICAL: Do NOT include ANY text, titles, letters, words, or typography anywhere in the image. Space for title at top.' 
        WHERE key = 'COVER_TEMPLATE'
    """)
    
    op.execute("""
        UPDATE prompt_templates 
        SET content_en = 'A young child wearing {clothing_description}. {scene_description}. Empty space at bottom for captions (no text in image).' 
        WHERE key = 'INNER_TEMPLATE'
    """)
