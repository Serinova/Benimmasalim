"""Add keywords_tr, keywords_en, visual_hints_en columns to learning_outcomes.

These fields allow DB-driven story validation and visual hint injection
instead of hardcoded keyword matching.

Revision ID: 044_learning_outcome_keywords
Revises: 043_clothing_description
Create Date: 2026-02-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "044_learning_outcome_keywords"
down_revision: str | None = "043_clothing_description"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "learning_outcomes",
        sa.Column(
            "keywords_tr",
            sa.Text(),
            nullable=True,
            comment="Comma-separated TR keywords for story validation",
        ),
    )
    op.add_column(
        "learning_outcomes",
        sa.Column(
            "keywords_en",
            sa.Text(),
            nullable=True,
            comment="Comma-separated EN keywords for story validation",
        ),
    )
    op.add_column(
        "learning_outcomes",
        sa.Column(
            "visual_hints_en",
            sa.Text(),
            nullable=True,
            comment="Comma-separated EN visual hints for image prompts",
        ),
    )

    # Seed known outcomes with keywords
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'diş,fırça,fırçalama',
            keywords_en = 'brush,toothbrush,teeth',
            visual_hints_en = 'toothbrush,tooth-brushing moment,brushing teeth'
        WHERE LOWER(name) LIKE '%diş%' OR LOWER(name) LIKE '%fırça%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'paylaş,paylaşma,birlikte,beraber',
            keywords_en = 'share,sharing,together',
            visual_hints_en = 'sharing toys,sharing food,giving to friend'
        WHERE LOWER(name) LIKE '%paylaş%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'sabır,sabırlı,bekle,bekleme',
            keywords_en = 'patience,patient,wait,waiting',
            visual_hints_en = 'waiting patiently,calm expression'
        WHERE LOWER(name) LIKE '%sabır%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'cesaret,cesur,kork,korku,yürek',
            keywords_en = 'courage,brave,bravery,fear',
            visual_hints_en = 'brave stance,overcoming fear'
        WHERE LOWER(name) LIKE '%cesaret%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'temiz,temizlik,yıka,yıkama',
            keywords_en = 'clean,cleaning,wash,washing',
            visual_hints_en = 'washing hands,cleaning up'
        WHERE LOWER(name) LIKE '%temiz%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'özür,özür dile,af,affet',
            keywords_en = 'sorry,apologize,apology,forgive',
            visual_hints_en = 'apologizing to friend,saying sorry'
        WHERE LOWER(name) LIKE '%özür%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'sorumluluk,sorumlu,görev',
            keywords_en = 'responsibility,responsible,duty',
            visual_hints_en = 'taking care of pet,doing chores'
        WHERE LOWER(name) LIKE '%sorumluluk%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'empati,empat,hisset,anlayış',
            keywords_en = 'empathy,understanding,compassion',
            visual_hints_en = 'comforting friend,showing kindness'
        WHERE LOWER(name) LIKE '%empati%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'doğa,ağaç,çiçek,bitki,hayvan,orman',
            keywords_en = 'nature,tree,flower,plant,animal,forest',
            visual_hints_en = 'planting tree,caring for nature'
        WHERE LOWER(name) LIKE '%doğa%'
        """
    )
    op.execute(
        """
        UPDATE learning_outcomes SET
            keywords_tr = 'yardım,yardımlaş,yardımsever',
            keywords_en = 'help,helping,helpful',
            visual_hints_en = 'helping others,lending a hand'
        WHERE LOWER(name) LIKE '%yardım%'
        """
    )


def downgrade() -> None:
    op.drop_column("learning_outcomes", "visual_hints_en")
    op.drop_column("learning_outcomes", "keywords_en")
    op.drop_column("learning_outcomes", "keywords_tr")
