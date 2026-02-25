"""Fix learning outcomes that conflict with story constraints (Family ban & historical settings).

Revision ID: 071_fix_incompatible_learning_outcomes
Revises: 070_remove_remaining_ghost_references
Create Date: 2026-02-23
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision: str = "071_fix_incompatible_learning_outcomes"
down_revision: str | None = "070_remove_remaining_ghost_references"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Kardeş Sevgisi -> İş Birliği ve Takım Çalışması
    # (Fixes the fatal conflict with STORY_NO_FIRST_DEGREE_FAMILY_TR rule)
    op.execute(
        text(
            """
            UPDATE learning_outcomes 
            SET name = 'İş Birliği ve Takım Çalışması',
                description = 'Başkalarıyla uyum içinde çalışmak',
                ai_prompt = 'Hikayede karakter karşılaştığı zorlukları yalnız başına değil, oradaki bilge rehberle veya hayvan dostuyla iş birliği yaparak aşsın ve takım çalışmasının gücünü anlasın.',
                keywords_tr = 'birlikte,beraber,takım,yardım,işbirliği',
                keywords_en = 'together,team,teamwork,help,collaboration',
                visual_hints_en = 'working together,helping each other'
            WHERE name = 'Kardeş Sevgisi'
            """
        )
    )

    # 2. Tuvalet Eğitimi -> Sorumluluk Bilinci
    # (Fixes inappropriateness for sacred/historical settings)
    op.execute(
        text(
            """
            UPDATE learning_outcomes 
            SET name = 'Sorumluluk Bilinci',
                description = 'Kendi görevlerini yerine getirmek',
                ai_prompt = 'Hikayede karakter kendi kararlarını alıp sonuçlarına sahip çıkmanın ve sorumluluk almanın onu nasıl büyüttüğünü görsün.',
                keywords_tr = 'sorumluluk,görev,karar',
                keywords_en = 'responsibility,duty,decision',
                visual_hints_en = 'determined face,taking action'
            WHERE name = 'Tuvalet Eğitimi'
            """
        )
    )

    # 3. Diş Fırçalama Alışkanlığı -> Temizlik ve Düzen
    # (Fixes anachronism for ancient/Neolithic settings)
    op.execute(
        text(
            """
            UPDATE learning_outcomes 
            SET name = 'Temizlik ve Düzen',
                description = 'Kendi çevresini temiz tutmak',
                ai_prompt = 'Hikayede karakter bulunduğu çevreyi ve kişisel eşyalarını temiz, düzenli tutmanın ona huzur ve başarı getirdiğini fark etsin.',
                keywords_tr = 'temiz,düzenli,toplu,düzen',
                keywords_en = 'clean,tidy,neat,order',
                visual_hints_en = 'cleaning,organizing,tidy environment'
            WHERE name = 'Diş Fırçalama Alışkanlığı'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        text(
            """
            UPDATE learning_outcomes 
            SET name = 'Kardeş Sevgisi',
                description = 'Kardeşlerle iyi geçinmek',
                ai_prompt = 'Hikayede karakter kardeşiyle iyi geçinmenin yollarını bulsun ve kardeş sevgisinin değerini anlasın.'
            WHERE name = 'İş Birliği ve Takım Çalışması'
            """
        )
    )
    op.execute(
        text(
            """
            UPDATE learning_outcomes 
            SET name = 'Tuvalet Eğitimi',
                description = 'Tuvaleti doğru kullanma',
                ai_prompt = 'Hikayede karakter tuvaletini yapmayı başarmanın gururunu yaşasın ve bu konuda özgüven kazansın.'
            WHERE name = 'Sorumluluk Bilinci'
            """
        )
    )
    op.execute(
        text(
            """
            UPDATE learning_outcomes 
            SET name = 'Diş Fırçalama Alışkanlığı',
                description = 'Düzenli diş fırçalamanın önemi',
                ai_prompt = 'Hikayede karakter dişlerini fırçalamayı eğlenceli bir oyun haline getirsin ve bunu her gün yapmanın önemini anlasın.'
            WHERE name = 'Temizlik ve Düzen'
            """
        )
    )
