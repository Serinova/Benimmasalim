"""Update COVER_TEMPLATE: elegant integrated title, proportional size, artistic.

Revision ID: 084_cover_title_elegant_integrated
Revises: 083_populate_scenario_descriptions
Create Date: 2026-02-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "084_cover_title_elegant_integrated"
down_revision: str = "083_populate_scenario_descriptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ── New cover template ────────────────────────────────────────────────────────
# Key design goals:
#   1. Title is proportional — NOT oversized, fits naturally in the scene
#   2. Perfectly horizontally centered, max 2 lines
#   3. Integrated into the scene (banner/arch/scroll/sky area), not pasted on top
#   4. Artistic lettering: hand-lettered feel, warm gradient, subtle glow
#   5. Title occupies top 10-12% of image height — strict upper bound
#   6. Never overlaps child or main subject
# ─────────────────────────────────────────────────────────────────────────────

_NEW_TEMPLATE = (
    "A young {child_gender} with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "BOOK TITLE: Render the EXACT text [{story_title}] as a beautifully integrated book title. "
    "PLACEMENT: Horizontally centered, confined strictly to the TOP 10% of the image — "
    "letters must NOT extend below the 10% line. "
    "SIZING: Proportional to the image width — title block width max 85% of image width, "
    "font size moderate (NOT oversized, NOT giant), split into 2 balanced lines if the text is long. "
    "STYLE: Hand-lettered storybook font, warm golden-amber gradient fill (bright gold center fading to deep amber at edges), "
    "thin dark-brown outline (1-2px), soft warm inner glow, subtle drop-shadow for gentle depth. "
    "The title should feel PAINTED INTO the scene — as if it belongs to the illustration, "
    "not stamped on top. Scatter 4-6 tiny golden stars around the title. "
    "STRICT RULE: Title must NEVER touch or overlap the child's head or body. "
    "Do NOT add any other text, subtitles, watermarks, or signatures anywhere in the image."
)

_OLD_TEMPLATE = (
    "A young {child_gender} with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "BOOK TITLE DESIGN: Render the EXACT text [{story_title}] letter by letter, HORIZONTALLY CENTERED, "
    "split into 2 centered lines if long, placed entirely in the top 14% of the image (open sky area). "
    "Style: large 3D embossed letters, warm amber-to-gold gradient fill, sharp specular highlight on each letter, "
    "thick dark-brown beveled outline, soft golden glow behind title block, warm drop-shadow. "
    "Scatter 6-10 small golden stars around the title. "
    "Title must NEVER touch or overlap the child''s head or body. "
    "Do NOT add any other text, watermarks, or signatures."
)


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE prompt_templates
        SET content_en = '{_NEW_TEMPLATE.replace("'", "''")}'
        WHERE key = 'COVER_TEMPLATE'
        """
    )


def downgrade() -> None:
    op.execute(
        f"""
        UPDATE prompt_templates
        SET content_en = '{_OLD_TEMPLATE.replace("'", "''")}'
        WHERE key = 'COVER_TEMPLATE'
        """
    )
