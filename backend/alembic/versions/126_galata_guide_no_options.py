"""Galata: rehberli gezi, puzzle/zorluk, başlık '[Ad]'ın Galata Macerası', custom_inputs kaldır.

Revision ID: 126_galata_guide
Revises: 125_sumela_guide
Create Date: 2026-03-05

"""
from alembic import op
from sqlalchemy.sql import text

revision = "126_galata_guide"
down_revision = "125_sumela_guide"
branch_labels = None
depends_on = None

NEW_NAME = "Galata Macerası"
NEW_DESCRIPTION = (
    "Rehber ile Galata Kulesi ve İstanbul keşfi. Mahalle, spiral merdiven, "
    "360° manzara, Galata Köprüsü ve Haliç. Çocuk zorlukları aşar, bulmaca çözer. "
    "Kitap adı: [Çocuk adı]'ın Galata Macerası."
)

NEW_STORY_PROMPT_TR = r"""
# GALATA MACERASI

## YAPI: {child_name} REHBER İLE GALATA KULESİ VE İSTANBUL KEŞFİ GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Galata Macerası" olmalı. Alt başlık (İstanbul Keşfi vb.) EKLEME.

**KURGU:** Rehber (tur rehberi, yetişkin insan — yüzü detaylı tarif etme) çocuğu Galata mahallesinden başlayıp Galata Kulesi'ne çıkarıyor, sonra iniş ve mahalle turu. Çocuk AKTİF: yol bulma, rehberin verdiği küçük görevler (haritada kuleyi bul, merdivende kaç pencere var say, gözlem katında Haliç'i bul), yorulup devam etme. Zorluklar gerçekçi (yükseklik, merdiven yorgunluğu). Her zorluğu AŞAR. Sihir, fantastik varlık YOK.

**YERLER (gerçek):** İstanbul, Beyoğlu — Galata semti. Arnavut kaldırımlı sokaklar, taş binalar, kırmızı kiremit. Galata Kulesi: 1348 Ceneviz yapısı, 67m, konik çatı. Spiral merdiven, gözlem terası, 360° İstanbul manzarası. Galata Köprüsü, Haliç, Boğaz. Nostaljik kırmızı tramvay.

---

### Bölüm 1 — Varış, Galata mahallesi (Sayfa 1-4)
- {child_name} Galata'ya geliyor (İstanbul). Tur rehberi ile tanışıyor. Taş sokaklar, eski binalar.
- Rehber kısaca anlatıyor: "Galata Kulesi 67 metre, tepesinden İstanbul'un tamamı görünür." Çocuk merakla dinliyor.
- İlk zorluk: Sokaklar karışık; rehber haritada kuleyi işaretliyor, çocuk yönü bulup kuleye ulaşıyor. İlk başarı.

### Bölüm 2 — Kuleye giriş, spiral merdiven (Sayfa 5-8)
- Kuleden içeri giriliyor. Dar spiral merdiven, pencerelerden ışık. Rehber: "Adım adım çıkacağız."
- Küçük görev: Rehber "Bu katta kaç pencere var, sayalım" diyor. Çocuk sayıyor, doğru söylüyor. Keşif sevinci.
- Yorgunluk artıyor; çocuk "Biraz dinlenelim" diyor, rehber onaylıyor. Dinlenip devam. Sebat.

### Bölüm 3 — Gözlem terası, 360° manzara (Sayfa 9-12)
- Gözlem katına ulaşılıyor. 360° İstanbul: Boğaz, minareler, kırmızı çatılar. Rehber Avrupa ve Asya yakasını gösteriyor.
- Zorluk: Rüzgâr güçlü; çocuk ilk başta tedirgin, rehber yanında, alışıyor. Cesaret.
- "İki kıta bir arada!" Hayranlık.

### Bölüm 4 — Galata Köprüsü, Haliç (Sayfa 13-16)
- Tepeden Galata Köprüsü ve Haliç görünüyor. Rehber: "Altın Boynuz, balıkçılar, vapurlar."
- Küçük bulmaca: Rehber "Haritada Haliç'i bul — hangi yönde?" Çocuk parmağıyla gösteriyor. Başarı.
- Gemiler, martılar. "İstanbul ne kadar büyük!" Duygu.

### Bölüm 5 — Kuleden iniş, sokaklar (Sayfa 17-19)
- İnişe geçiliyor. Rehber dikkatli adım atmayı hatırlatıyor. Mahalle sokaklarına çıkılıyor.
- Nostaljik kırmızı tramvay geçiyor. Taş sokaklar, kafeler. Çocuk yoruluyor ama rehber "Son köşe, oradan dönüş" diyor. Bitiriyor. Sebat.
- "Galata'nın her köşesi ayrı güzel!" Tatmin.

### Bölüm 6 — Kapanış (Sayfa 20-22)
- Rehber tebrik ediyor: "Zorlukları aştın, Galata'yı keşfettin."
- Günbatımına doğru İstanbul silueti (isteğe bağlı). {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış.

---

## KURALLAR
- Rehber = gerçek insan (yüz detayı verme). Sihir, konuşan hayvan YOK.
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: Galata mahallesi, Galata Kulesi (67m, spiral merdiven, gözlem terası), Galata Köprüsü, Haliç, Boğaz.
- Korku/tehlike yok; tırmanış rehberli, korkuluklar var.
- Kitap adı SADECE "[Çocuk adı]'ın Galata Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

OUTFIT_GIRL = (
    "bright cherry-red cotton hoodie with small white heart logo on chest, "
    "dark navy blue denim jeans, white canvas sneakers with red laces, "
    "small light gray backpack on back. "
    "EXACTLY the same outfit on every page — same red hoodie, same navy jeans, same white sneakers."
)
OUTFIT_BOY = (
    "royal blue zip-up cotton jacket over white crew-neck t-shirt, "
    "dark gray cargo pants with side pockets, black and white striped sneakers, "
    "small navy blue backpack on back. "
    "EXACTLY the same outfit on every page — same blue jacket, same gray pants, same striped sneakers."
)

COVER_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Iconic Galata Tower (67m stone tower, conical roof) in background, Istanbul. "
    "Bosphorus visible, historic Galata neighborhood, cobblestone. "
    "Wide shot: child 25%, tower and cityscape 75%. Historic, nostalgic."
)
PAGE_PROMPT = (
    "An {child_age}-year-old {child_gender} named {child_name} "
    "with {hair_description}, wearing {clothing_description}. "
    "{scene_description}. "
    "Elements: [Galata Tower: 67m medieval stone, conical roof, observation deck / "
    "Bosphorus: strait, ships, ferries / Galata Bridge, Golden Horn / "
    "Cobblestone streets, stone buildings, red tram]. "
    "Warm Istanbul colors: stone beige, red tile, blue strait."
)


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE scenarios
            SET name = :name,
                description = :description,
                story_prompt_tr = :prompt,
                custom_inputs_schema = '[]'::jsonb,
                outfit_girl = :outfit_girl,
                outfit_boy = :outfit_boy,
                cover_prompt_template = :cover_prompt,
                page_prompt_template = :page_prompt
            WHERE theme_key = 'galata'
               OR theme_key = 'galata_tower_istanbul'
               OR name ILIKE '%Galata%'
        """),
        {
            "name": NEW_NAME,
            "description": NEW_DESCRIPTION,
            "prompt": NEW_STORY_PROMPT_TR.strip(),
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
            "cover_prompt": COVER_PROMPT,
            "page_prompt": PAGE_PROMPT,
        },
    )


def downgrade() -> None:
    pass
