"""Çatalhöyük: rehberli gezi, puzzle/zorluk, başlık '[Ad]'ın Çatalhöyük Macerası', custom_inputs kaldır.

Revision ID: 124_catalhoyuk_guide
Revises: 123_efes_antik
Create Date: 2026-03-05

"""
from alembic import op
from sqlalchemy.sql import text

revision = "124_catalhoyuk_guide"
down_revision = "123_efes_antik"
branch_labels = None
depends_on = None

NEW_NAME = "Çatalhöyük Macerası"
NEW_DESCRIPTION = (
    "Rehber ile Çatalhöyük gezisi. 9000 yıllık kerpiç evler, damdan giriş, "
    "duvar resimleri, kazı alanı. Çocuk zorlukları aşar, bulmaca çözer. "
    "Kitap adı: [Çocuk adı]'ın Çatalhöyük Macerası."
)

NEW_STORY_PROMPT_TR = r"""
# ÇATALHÖYÜK MACERASI

## YAPI: {child_name} REHBER İLE ÇATALHÖYÜK NEOLİTİK KENTİ GEZİSİNDE. Çocuk maceraya atılır, sır/bulmaca çözer, zorluklarla karşılaşır ve onları aşar.

**BAŞLIK:** Kitap adı sadece "[Çocuk adı]'ın Çatalhöyük Macerası" olmalı. Alt başlık (Neolitik Kenti Keşfi vb.) EKLEME.

**KURGU:** Rehber (arkeolog veya tur rehberi, yetişkin insan — yüzü detaylı tarif etme) çocuğu Çatalhöyük kazı alanında ve rekonstrüksiyon alanında gezdiriyor. Çocuk AKTİF: yol bulma, rehberin verdiği küçük görevler (duvardaki boğayı bul, damdan girişi bul, kazı katmanlarını say, haritada noktayı bul), yorulup devam etme. Zorluklar gerçekçi. Her zorluğu AŞAR. Sihir, zaman yolculuğu, konuşan hayvan YOK.

**YERLER (gerçek):** Konya ovasında höyük, 9000 yıllık (MÖ 7100–5700) Neolitik yerleşim. Kerpiç evler — kapı yok, damdan merdivenle giriş. Duvar resimleri: boğa, geometrik desenler, av sahneleri. Kazı alanı, katmanlar. Obsidyen aletler (volkanik cam), çömlek, tahıl depolama. UNESCO Dünya Mirası.

---

### Bölüm 1 — Varış, rehber, höyükle tanışma (Sayfa 1-4)
- {child_name} Çatalhöyük'e geliyor (Konya, Çumra). Tur rehberi ile tanışıyor. Uzaktan höyük görünüyor — "9000 yıl önce burada insanlar yaşamış!"
- Rehber kısaca anlatıyor: dünyanın en eski şehirlerinden biri, Neolitik Çağ. Çocuk merakla dinliyor.
- İlk zorluk: Kazı alanında yol ikiye ayrılıyor; rehber haritada "evlerin olduğu yön"ü gösteriyor, çocuk doğru yolu seçiyor. İlk başarı.

### Bölüm 2 — Kerpiç evler, damdan giriş (Sayfa 5-8)
- Rekonstrüksiyon alanında kerpiç evler. Rehber: "Kapı yok, evlere damdan merdivenle giriliyordu!"
- Küçük görev: Rehber "Hangi evin damında merdiven var, bul" diyor. Çocuk evleri dolaşıyor, merdiveni buluyor. Keşif sevinci.
- Damlarda yürüme, "Sokak yokmuş, herkes damlardan gidiyormuş!" Tarih bilinci.

### Bölüm 3 — Duvar resimleri (Sayfa 9-12)
- Bir evin içinde (veya müze/panoda) duvar resimleri: boğa, geometrik desenler. Rehber: 9000 yıllık sanat, doğal boyalar.
- Zorluk: Rehber "Bu odada duvarda kaç boğa var, say" diyor. Çocuk dikkatle sayıyor, doğru cevabı veriyor. Sebat.
- "İnsanlar o zaman da resim yapıyormuş!" Hayranlık.

### Bölüm 4 — Kazı alanı, katmanlar (Sayfa 13-16)
- Kazı alanına yaklaşma. Katmanlar, fırçalar, arkeologlar. Rehber: "Her katman farklı bir dönem."
- Küçük bulmaca: Rehber "En üstteki iki katmanı say, sonra bana söyle" diyor. Çocuk dikkatle bakıyor, sayıyor. Başarı.
- İlk çömlek parçası veya obsidyen alet (camdan) — "Bunlarla yemek yapılırmış, kesilirmiş." Merak.

### Bölüm 5 — Tahıl, tarım, günlük yaşam (Sayfa 17-19)
- Rehber tarımı anlatıyor: buğday, arpa. Depolama odaları, ocaklar. Çocuk yoruluyor ama dinliyor.
- "Biraz daha yürüyelim, haritadaki son noktaya ulaşalım" — çocuk ayakları ağrısa da rehberle birlikte bitiriyor. Sebat.
- "9000 yıl önce de çocuklar oynuyor, aileler birlikte yaşıyormuş!" Duygusal bağ.

### Bölüm 6 — Dünyanın ilk haritası, kapanış (Sayfa 20-22)
- Rehber: "Burada bulunan bir duvar resmi dünyanın ilk haritası sayılıyor." Çocuk haritayı (kopyasını veya anlatımını) görüyor.
- Gezinin sonu. Rehber tebrik ediyor: "Zorlukları aştın, 9000 yıllık Çatalhöyük'ü keşfettin."
- {child_name} eve dönüşe hazırlanıyor. Kısa ve duygusal kapanış.

---

## KURALLAR
- Rehber = gerçek insan (yüz detayı verme). Sihir, zaman yolculuğu, konuşan hayvan (Bilge Kedi vb.) YOK.
- Her bölümde en az bir küçük zorluk/görev ve çocuğun onu aşması.
- Yerler gerçek: höyük, kerpiç evler (damdan giriş), duvar resimleri (boğa, geometrik), kazı alanı, tahıl/tarım.
- Korku/şiddet yok; boyalı kafatası veya ürkütücü detay YOK. Çocuk güvenli, eğitici ton.
- Kitap adı SADECE "[Çocuk adı]'ın Çatalhöyük Macerası". Alt başlık ekleme.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 2-4 cümle, akıcı ve macera dolu.
"""

OUTFIT_GIRL = (
    "terracotta rust-colored cotton t-shirt with small geometric pattern on chest, "
    "dark brown cotton cargo shorts, tan leather ankle boots, "
    "light brown canvas bucket hat, small leather crossbody satchel. "
    "EXACTLY the same outfit on every page — same terracotta shirt, same brown shorts, same leather boots."
)
OUTFIT_BOY = (
    "ochre yellow cotton t-shirt with small arrowhead emblem, "
    "dark olive green cotton shorts, tan leather ankle boots, "
    "brown canvas explorer hat, small leather hip pouch on belt. "
    "EXACTLY the same outfit on every page — same ochre shirt, same olive shorts, same leather boots."
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
                outfit_boy = :outfit_boy
            WHERE theme_key = 'catalhoyuk'
               OR theme_key = 'catalhoyuk_neolithic_city'
               OR name ILIKE '%Çatalhöyük%'
               OR name ILIKE '%Catalhoyuk%'
        """),
        {
            "name": NEW_NAME,
            "description": NEW_DESCRIPTION,
            "prompt": NEW_STORY_PROMPT_TR.strip(),
            "outfit_girl": OUTFIT_GIRL,
            "outfit_boy": OUTFIT_BOY,
        },
    )


def downgrade() -> None:
    pass
