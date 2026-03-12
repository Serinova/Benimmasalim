"""fix_dinosaur_pari_consistency

Dinozor senaryosundaki Pari (yavru Parasaurolophus) karakter tutarlılık sorunu düzeltmesi:
1. {animal_friend} placeholder'ı kaldırıldı (pipeline'da resolve edilmiyordu)
2. custom_inputs_schema boşaltıldı (obje seçimi gereksiz — hikaye zaten Pari'ye özelleştirilmiş)
3. scenario_bible'a side_character bilgisi eklendi (CharacterBible + cast_validator uyumu)
4. G2 tutarlılık kuralları güçlendirildi

Revision ID: d5e6f7a8b9c0
Revises: c3a4b5d6e7f8
Create Date: 2026-03-11
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c3a4b5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from scripts.update_dinosaur_scenario import (
        DINOSAUR_COVER_PROMPT,
        DINOSAUR_PAGE_PROMPT,
        DINOSAUR_STORY_PROMPT_TR,
        DINOSAUR_LOCATION_CONSTRAINTS,
        DINOSAUR_CULTURAL_ELEMENTS,
        DINOSAUR_CUSTOM_INPUTS,
        DINOSAUR_SCENARIO_BIBLE,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )

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
                scenario_bible = :scenario_bible,
                outfit_girl = :outfit_girl,
                outfit_boy = :outfit_boy,
                tagline = :tagline,
                updated_at = now()
            WHERE theme_key IN ('dinosaur', 'dinosaur_time_travel')
               OR name ILIKE '%Dinozor%'
        """),
        {
            "description": (
                "Bulduğu sihirli fosil pusula ile zamanda yolculuk yapan maceracımız, "
                "yaklaşan büyük fırtınadan önce kafa kalkanlı şirin bir dinozor yavrusunu "
                "dev ormanlarda ipuçları bularak ailesine kavuşturmak için zamana karşı yarışıyor!"
            ),
            "cover_prompt": DINOSAUR_COVER_PROMPT,
            "page_prompt": DINOSAUR_PAGE_PROMPT,
            "story_prompt": DINOSAUR_STORY_PROMPT_TR,
            "location_constraints": DINOSAUR_LOCATION_CONSTRAINTS,
            "cultural_elements": json.dumps(DINOSAUR_CULTURAL_ELEMENTS, ensure_ascii=False),
            "custom_inputs": json.dumps(DINOSAUR_CUSTOM_INPUTS),
            "scenario_bible": json.dumps(DINOSAUR_SCENARIO_BIBLE, ensure_ascii=False),
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
            "tagline": "Fırtına kopmadan yavruyu ailesine kavuştur!",
        }
    )
    print("OK: Dinozor senaryosu — Pari tutarlılık düzeltmesi uygulandı.")

def downgrade() -> None:
    pass
