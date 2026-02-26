"""update_dinosaur_epic_giant_adventure

Revision ID: 6ac798b22980
Revises: a22af3bbaa39
Create Date: 2026-02-25 19:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6ac798b22980'
down_revision: Union[str, None] = 'a22af3bbaa39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update Dinosaur scenario with epic giant dinosaur adventure prompts."""
    from scripts.update_dinosaur_scenario import (
        DINOSAUR_COVER_PROMPT,
        DINOSAUR_PAGE_PROMPT,
        DINOSAUR_STORY_PROMPT_TR,
    )
    
    conn = op.get_bind()
    
    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                cover_prompt_template = :cover_prompt,
                page_prompt_template = :page_prompt,
                story_prompt_tr = :story_prompt,
                description = :description
            WHERE name ILIKE '%Dinozor%'
        """),
        {
            "cover_prompt": DINOSAUR_COVER_PROMPT,
            "page_prompt": DINOSAUR_PAGE_PROMPT,
            "story_prompt": DINOSAUR_STORY_PROMPT_TR,
            "description": "Zaman makinesi ile 65 milyon yıl öncesine git! DEVASA dinozorlarla dostluk kur: T-Rex'e bin, Pteranodon ile uç, Brachiosaurus'un sırtında yolculuk yap. Epik macera!",
        }
    )
    print("OK: Dinozor senaryosu EPIK DEVASA maceraya guncellendi!")


def downgrade() -> None:
    """Revert dinosaur scenario changes."""
    pass
