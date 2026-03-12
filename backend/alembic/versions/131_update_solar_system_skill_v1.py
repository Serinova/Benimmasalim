"""update_solar_system_skill_v1

Güneş Sistemi senaryosunu Scenario Writer Skill v1.0 standartlarına yükseltir.
Kıyafet bug'ı düzeltildi. Duygusal adrenalin yayı eklendi. G2 ve G3 revize edildi.

Revision ID: f8a3b2c4e5d6
Revises: e7f2a1b3c4d5
Create Date: 2026-03-09
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

revision: str = "f8a3b2c4e5d6"
down_revision: Union[str, None] = "e7f2a1b3c4d5"  # Galata'nın devamı
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from scripts.update_solar_system_scenario import (
        SPACE_COVER_PROMPT,
        SPACE_PAGE_PROMPT,
        SPACE_STORY_PROMPT_TR,
        SPACE_LOCATION_CONSTRAINTS,
        SPACE_CULTURAL_ELEMENTS,
        SPACE_CUSTOM_INPUTS,
        OUTFIT_GIRL,
        OUTFIT_BOY,
    )

    conn = op.get_bind()

    # İki varyasyon da olabilir (Uzayın Kayıp Sinyali veya Güneş Sistemi Macerası)
    # Biz genel space / solar_system_space olan tüm kayıtları Skill 1.0 formatına güncelliyoruz
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
            WHERE theme_key IN ('solar_system_space', 'space')
               OR name ILIKE '%Güneş Sistemi%' OR name ILIKE '%Uzay%'
        """),
        {
            "description": (
                "Güneş Sistemi'nin kalbine, adrenalin ve keşif dolu nefes kesici bir yolculuk! "
                "Kahramanımız küçük robot arkadaşı Nova ile birlikte Ay kraterlerinden sekiyor, "
                "Mars fırtınalarıyla boğuşuyor, Jüpiter'in çekimiyle savaşıyor ve Satürn'ün halkalarında huzur buluyor."
            ),
            "cover_prompt": SPACE_COVER_PROMPT,
            "page_prompt": SPACE_PAGE_PROMPT,
            "story_prompt": SPACE_STORY_PROMPT_TR,
            "location_constraints": SPACE_LOCATION_CONSTRAINTS,
            "cultural_elements": json.dumps(SPACE_CULTURAL_ELEMENTS, ensure_ascii=False),
            "custom_inputs": json.dumps(SPACE_CUSTOM_INPUTS),
            "outfit_girl": OUTFIT_GIRL,  # Bug fix: Straight text
            "outfit_boy": OUTFIT_BOY,    # Bug fix: Straight text
            "tagline": "Fırtınaları aş, uzayın gizemini fethet!",
        }
    )
    print("OK: Uzay/Güneş Sistemi senaryolu Skill v1.0 ile guncellendi (Kıyafet bug'ı çözüldü).")

def downgrade() -> None:
    pass
