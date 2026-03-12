"""update_galata_scenario_skill_v1

Galata senaryosunu Scenario Writer Skill v1.0 standartlarına yükseltir.
Yeni: G2 karakter tutarlılık kartları, G3 lokasyon kademe haritası,
      custom page_prompt_template, duygusal yay (heyecan→merak→endişe→keşif→zafer)

Revision ID: e7f2a1b3c4d5
Revises: 132_efes_outfit_title
Create Date: 2026-03-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "e7f2a1b3c4d5"
down_revision: Union[str, None] = "132_efes_outfit_title"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from scripts.update_galata_scenario import (
        GALATA_COVER_PROMPT,
        GALATA_PAGE_PROMPT,
        GALATA_STORY_PROMPT_TR,
        GALATA_LOCATION_CONSTRAINTS,
        GALATA_CULTURAL_ELEMENTS,
        GALATA_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )
    import json

    conn = op.get_bind()

    conn.execute(
        sa.text("""
            UPDATE scenarios SET
                description = :description,
                cover_prompt_template = :cover_prompt,
                page_prompt_template = :page_prompt,
                story_prompt_tr = :story_prompt,
                location_constraints = :location_constraints,
                cultural_elements = :cultural_elements,
                custom_inputs_schema = :custom_inputs,
                outfit_girl = :outfit_girl,
                outfit_boy = :outfit_boy,
                tagline = :tagline,
                updated_at = now()
            WHERE theme_key = 'galata' OR name ILIKE '%Galata%'
        """),
        {
            "description": (
                "Gün batarken Galata'da gizemli bir ışık aparatı bulan kahraman, "
                "altın harita çizgilerini izleyerek dar yokuşlarda ve kedi gölgelerinde "
                "heyecanlı bir kayıp eşya avcılığına çıkar. Güneş batmadan yetişebilecek mi?"
            ),
            "cover_prompt": GALATA_COVER_PROMPT,
            "page_prompt": GALATA_PAGE_PROMPT,
            "story_prompt": GALATA_STORY_PROMPT_TR,
            "location_constraints": GALATA_LOCATION_CONSTRAINTS,
            "cultural_elements": json.dumps(GALATA_CULTURAL_ELEMENTS, ensure_ascii=False),
            "custom_inputs": json.dumps(GALATA_CUSTOM_INPUTS),
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
            "tagline": "Işık haritasını izle, Galata'nın sırrını çöz!",
        }
    )
    print("OK: Galata senaryosu Skill v1.0 ile guncellendi.")


def downgrade() -> None:
    pass
