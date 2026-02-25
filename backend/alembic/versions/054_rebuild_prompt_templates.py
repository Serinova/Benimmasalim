"""Rebuild prompt_templates table (clean slate).

Eski 8 prompt migration'ı silindi. Bu migration tabloyu sıfırdan oluşturur.
Mevcut tablo varsa drop edip yeniden oluşturur.

Revision ID: 054_rebuild_prompt_templates
Revises: 053_face_crop_fields
Create Date: 2026-02-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "054_rebuild_prompt_templates"
down_revision: str = "053_face_crop_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS prompt_templates CASCADE")

    op.create_table(
        "prompt_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="story_system"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_en", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("modified_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("idx_prompt_category", "prompt_templates", ["category"])
    op.create_index(
        "idx_prompt_active",
        "prompt_templates",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_prompt_key_active", "prompt_templates", ["key", "is_active"])

    # Seed default prompts
    op.execute("""
        INSERT INTO prompt_templates (id, key, name, category, content, content_en) VALUES
        (gen_random_uuid(), 'PURE_AUTHOR_SYSTEM', 'Hikaye Yazarı System Prompt', 'story_system',
         'Sen ödüllü bir çocuk kitabı yazarısın. Görevin verilen senaryo ve eğitsel değerler doğrultusunda yaratıcı, tutarlı ve eğitici bir hikaye yazmak.',
         NULL),
        (gen_random_uuid(), 'AI_DIRECTOR_SYSTEM', 'Teknik Yönetmen System Prompt', 'story_system',
         'Sen bir teknik yönetmensin. Görevin hikayeyi sayfalara bölmek ve her sayfa için İngilizce sahne tanımı oluşturmak.',
         NULL),
        (gen_random_uuid(), 'COVER_TEMPLATE', 'Kapak Görsel Template', 'visual_template',
         'Kapak görseli için template',
         'A young child wearing {clothing_description}. {scene_description}. CRITICAL: Do NOT include ANY text, titles, letters, words, or typography anywhere in the image. Space for title at top.'),
        (gen_random_uuid(), 'INNER_TEMPLATE', 'İç Sayfa Görsel Template', 'visual_template',
         'İç sayfa görseli için template',
         'A young child wearing {clothing_description}. {scene_description}. Empty space at bottom for captions (no text in image).'),
        (gen_random_uuid(), 'NEGATIVE_PROMPT', 'Genel Negatif Prompt', 'negative_prompt',
         'Görsel üretimde kaçınılacak öğeler',
         'big eyes, chibi, oversized head, bobblehead, close-up, portrait, headshot, selfie, face filling frame, looking at camera, cropped body, cut-off legs, waist-up only, missing legs, missing feet, stiff pose, empty background, blurred background, bokeh, blurry, depth of field, low quality, deformed hands, extra fingers, reversed hand, text, watermark, unrecognizable face, bad anatomy')
    """)


def downgrade() -> None:
    op.drop_table("prompt_templates")
