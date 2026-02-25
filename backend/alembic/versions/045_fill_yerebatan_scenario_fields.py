"""Fill missing fields for Yerebatan Sarnici scenario.

Yerebatan Sarnici (Basilica Cistern) was missing:
- location_en
- location_constraints
- cultural_elements (JSON)
- story_prompt_tr

All other 10 scenarios have these fields populated.

Revision ID: 045_yerebatan_fields
Revises: 044_learning_outcome_keywords
Create Date: 2026-02-14
"""
from collections.abc import Sequence

from alembic import op

revision: str = "045_yerebatan_fields"
down_revision: str = "044_learning_outcome_keywords"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Yerebatan Sarnici data
# ---------------------------------------------------------------------------

YEREBATAN_LOCATION_EN = "Basilica Cistern, Istanbul"

YEREBATAN_LOCATION_CONSTRAINTS = (
    "Yerebatan Cistern (Basilica Cistern) iconic elements (include 1-2 relevant details depending on the scene): "
    "- Hundreds of ancient marble columns reflected in shallow water below, "
    "- Warm amber and orange lighting illuminating the underground space with dramatic shadows, "
    "- The famous Medusa head column base partially submerged in water, "
    "- Arched brick ceilings with Byzantine-era architectural details, "
    "- Cool stone tones contrasted with warm artificial lighting, "
    "- Istanbul above-ground elements for outdoor scenes (Hagia Sophia, Sultanahmet Square)"
)

YEREBATAN_CULTURAL_ELEMENTS = """{
    "primary_landmarks": [
        "Hundreds of ancient marble columns in a vast underground cistern",
        "Medusa head column bases (one upside-down, one sideways)",
        "Shallow water reflecting columns and amber lighting",
        "Arched brick ceilings with Byzantine architectural details"
    ],
    "secondary_elements": [
        "Hagia Sophia visible when exiting to street level",
        "Sultanahmet Square and Blue Mosque in the vicinity",
        "Roman and Byzantine era carved column capitals",
        "Tear-shaped column (Hen's Eye column) with peacock eye carvings",
        "Ancient aqueduct system that fed the cistern"
    ],
    "cultural_items": [
        "oil lanterns and torches for underground illumination",
        "Byzantine mosaic fragments on walls",
        "ancient water channels and stone pipes",
        "marble fish sculptures in the water"
    ],
    "color_palette": [
        "warm amber and orange from spotlights",
        "cool blue-grey of stone columns",
        "golden reflections on water surface",
        "deep shadows between columns",
        "mossy green on wet stone surfaces"
    ]
}"""

YEREBATAN_STORY_PROMPT_TR = (
    "Sen ödüllü çocuk kitabı yazarı ve İstanbul tarihi uzmanısın. "
    "Kahraman, yaş ve eğitsel değerler yukarıda verilmiştir. "
    "Görevin: Yerebatan Sarnıcı'nda geçen büyülü bir macera yazmak.\n\n"
    "📍 YEREBATAN SARNICI — KULLANILACAK KÜLTÜREL MEKANLAR (hikayeye en az 4 tanesini entegre et):\n"
    "1. Yüzlerce antik mermer sütun — su yüzeyinde yansımaları, kehribar ışıkla aydınlatılmış\n"
    "2. Medusa başı sütun altlıkları — biri ters, biri yan duran gizemli taş yüzler\n"
    "3. Tavus kuşu gözü sütunu (Gözyaşı Sütunu) — oyma desenli özel sütun\n"
    "4. Bizans tuğla kemerli tavanlar — yeraltı sarayının büyüleyici mimarisi\n"
    "5. Sığ su altındaki mermer zeminler — adım atınca su kıpırtısı\n"
    "6. Sokak seviyesine çıkış — Ayasofya ve Sultanahmet Meydanı manzarası\n\n"
    "📖 HİKAYE YAPISI:\n"
    "- Çocuk sarnıca giriyor ve yeraltı dünyasının büyüsüne kapılıyor\n"
    "- Medusa başlarının gizemi etrafında bir macera örgüsü kur\n"
    "- Sütunların arasında yankılanan fısıltılar, su damlası sesleri atmosfer oluştursun\n"
    "- Tarihî bilgiyi doğal diyalog ve keşif yoluyla ver, ders anlatır gibi yazma\n"
    "- Işık-gölge kontrastı, yansımalar ve yeraltı atmosferini duygusal sahne öğesi olarak kullan\n\n"
    "⚠️ KURALLAR:\n"
    "- Karanlık, korku veya tehlike vurgusu YASAK — macera merak ve hayranlık odaklı olsun\n"
    "- Hikayede DİNİ RİTÜEL veya İBADET SAHNESİ OLMAMALIDIR\n"
    "- Yerebatan Sarnıcı'nın gizemi arkeolojik ve tarihî merak perspektifinden işlensin\n\n"
    "🎨 SAHNE AÇIKLAMASI KURALLARI (Pass-2 için ipucu):\n"
    "Her sahne için spesifik Yerebatan lokasyonu ve mimari detay kullan.\n"
    "Örn: 'Medusa başı sütunlarının önünde', 'Gözyaşı Sütunu'nun yanında',\n"
    "'Sarnıcın en derin noktasında su yansımalarının arasında', "
    "'Sokağa çıkış merdivenlerinde Ayasofya manzarası ile'.\n"
    "Genel ifadelerden kaçın ('sarnıçta', 'sütunların yanında' yerine somut yer adı ve detay kullan)."
)


def upgrade() -> None:
    # Update Yerebatan Sarnıcı scenario fields
    op.execute(
        f"""
        UPDATE scenarios
        SET location_en = '{YEREBATAN_LOCATION_EN}',
            location_constraints = '{YEREBATAN_LOCATION_CONSTRAINTS.replace("'", "''")}',
            cultural_elements = '{YEREBATAN_CULTURAL_ELEMENTS.replace("'", "''")}' ::jsonb,
            story_prompt_tr = '{YEREBATAN_STORY_PROMPT_TR.replace("'", "''")}'
        WHERE name ILIKE '%Yerebatan%'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE scenarios
        SET location_en = NULL,
            location_constraints = NULL,
            cultural_elements = NULL,
            story_prompt_tr = NULL
        WHERE name ILIKE '%Yerebatan%'
        """
    )
