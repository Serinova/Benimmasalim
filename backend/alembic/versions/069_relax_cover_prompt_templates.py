"""Relax strict requirements in cover prompt templates to prevent overcrowding.

Revision ID: 069_relax_cover_prompt_templates
Revises: 068_relax_location_constraints
Create Date: 2026-02-22
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision: str = "069_relax_cover_prompt_templates"
down_revision: str | None = "068_relax_location_constraints"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Update all cover prompt templates to be less restrictive
    op.execute(
        """
        UPDATE scenarios 
        SET cover_prompt_template = REPLACE(cover_prompt_template, 'ICONIC BACKGROUND ELEMENTS (must include):', 'ICONIC BACKGROUND ELEMENTS (include 2-3 key details):')
        WHERE cover_prompt_template LIKE '%ICONIC BACKGROUND ELEMENTS (must include):%'
        """
    )
    
    # Specifically for Yerebatan: fix the 'entrance' issue which causes exterior shots
    op.execute(
        """
        UPDATE scenarios
        SET cover_prompt_template = REPLACE(cover_prompt_template, 'standing at the entrance of the magnificent Yerebatan Cistern', 'exploring deep inside the magnificent underground Yerebatan Cistern')
        WHERE name ILIKE '%yerebatan%' AND cover_prompt_template LIKE '%entrance%'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE scenarios 
        SET cover_prompt_template = REPLACE(cover_prompt_template, 'ICONIC BACKGROUND ELEMENTS (include 2-3 key details):', 'ICONIC BACKGROUND ELEMENTS (must include):')
        WHERE cover_prompt_template LIKE '%ICONIC BACKGROUND ELEMENTS (include 2-3 key details):%'
        """
    )
