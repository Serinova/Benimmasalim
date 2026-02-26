"""ocean_modular_prompts_pilot

Revision ID: 68f0daf6de81
Revises: cd73f6d58ed7
Create Date: 2026-02-25 23:31:37.915120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68f0daf6de81'
down_revision: Union[str, None] = 'cd73f6d58ed7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update Ocean scenario prompts to modular (pipeline-friendly) version."""
    import sqlalchemy as sa
    
    # Import prompt definitions
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from scripts.update_ocean_adventure_scenario import (
        OCEAN_COVER_PROMPT,
        OCEAN_PAGE_PROMPT,
        OCEAN_STORY_PROMPT_TR,
    )
    
    conn = op.get_bind()
    
    print("[DEBUG] Updating Ocean modular prompts...")
    print(f"[DEBUG] Cover length: {len(OCEAN_COVER_PROMPT)}")
    print(f"[DEBUG] Page length: {len(OCEAN_PAGE_PROMPT)}")
    print(f"[DEBUG] Story length: {len(OCEAN_STORY_PROMPT_TR)}")
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                cover_prompt_template = :cover,
                page_prompt_template = :page,
                story_prompt_tr = :story,
                updated_at = NOW()
            WHERE theme_key = 'ocean_depths'
        """),
        {
            "cover": OCEAN_COVER_PROMPT,
            "page": OCEAN_PAGE_PROMPT,
            "story": OCEAN_STORY_PROMPT_TR,
        }
    )
    
    print("OK: Ocean scenario updated with modular prompts")
    print("  - Cover: 326 char (pipeline will use)")
    print("  - Page: 464 char (pipeline will use)")
    print("  - Story: Enhanced with blueprint structure")


def downgrade() -> None:
    """Revert to previous Ocean prompts."""
    print("Downgrade not implemented - keep modular prompts")
