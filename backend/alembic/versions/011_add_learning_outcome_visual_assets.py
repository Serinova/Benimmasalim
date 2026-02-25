"""Add visual assets and AI instruction fields to learning_outcomes

Revision ID: 011_learning_outcome_assets
Revises: 010_scenario_marketing
Create Date: 2026-02-01

This migration adds the following fields to the learning_outcomes table:
- UI Visual Assets: icon_url, color_theme
- AI Logic: ai_prompt_instruction (detailed instruction field)

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '011_learning_outcome_assets'
down_revision: str | None = '010_scenario_marketing'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ============ UI VISUAL ASSETS ============
    # Icon URL for selection card (SVG/PNG)
    op.add_column('learning_outcomes', sa.Column(
        'icon_url',
        sa.Text(),
        nullable=True,
        comment='URL of the SVG/PNG icon displayed on selection card'
    ))

    # Color theme for card styling (hex code)
    op.add_column('learning_outcomes', sa.Column(
        'color_theme',
        sa.String(20),
        nullable=True,
        comment='Hex color code for card border/background accent (e.g., #FF5733)'
    ))

    # ============ AI LOGIC ============
    # Detailed AI prompt instruction (preferred over legacy ai_prompt)
    op.add_column('learning_outcomes', sa.Column(
        'ai_prompt_instruction',
        sa.Text(),
        nullable=True,
        comment='Detailed AI instruction with {child_name} placeholder - preferred over ai_prompt'
    ))


def downgrade() -> None:
    op.drop_column('learning_outcomes', 'ai_prompt_instruction')
    op.drop_column('learning_outcomes', 'color_theme')
    op.drop_column('learning_outcomes', 'icon_url')
