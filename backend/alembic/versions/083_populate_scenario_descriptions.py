"""Populate description field for all 11 scenarios (karşılama 2 sayfası için).

Her senaryo için çocuk dostu, eğitici ve büyülü bir tanıtım paragrafı ekler.
Bu metin karşılama 2 sayfasında (senaryo intro) kullanılır.

Revision ID: 083_populate_scenario_descriptions
Revises: 082_add_back_cover_image_url_to_story_previews
Create Date: 2026-02-24
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "083_populate_scenario_descriptions"
down_revision: str = "082_add_back_cover_image_url_to_story_previews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DESCRIPTIONS: list[tuple[str, str]] = [
    (
        "cappadocia",
        "Kapadokya, Türkiye'nin kalbinde yer alan ve milyonlarca yıl önce yanardağların şekillendirdiği "
        "büyülü bir diyardır. Peri bacaları adı verilen dev kaya kulelerinin arasında, kayalara oyulmuş "
        "antik mağara evler ve renkli sıcak hava balonları gökyüzünü süsler. Yeraltı şehirleri, gizli "
        "tüneller ve harika vadilerle dolu bu eşsiz coğrafya, her köşesinde yeni bir sürprizi saklayan "
        "gerçek bir macera diyarıdır!",
    ),
    (
        "gobeklitepe",
        "Göbeklitepe, Türkiye'nin Şanlıurfa iline bağlı ve yaklaşık 12.000 yıl önce inşa edilmiş "
        "dünyanın bilinen en eski tapınak kompleksidir. Dev T biçimli dikilitaşlar üzerinde tilki, "
        "aslan, yılan ve akbaba kabartmaları bulunur. Bu gizemli yapılar, insanlığın tarihini yeniden "
        "yazan ve arkeologları şaşırtan bir bilgeliği barındırır. Göbeklitepe'de her taş, binlerce "
        "yıllık bir sırrı fısıldar!",
    ),
    (
        "ephesus",
        "Efes, günümüz Türkiye'sinin İzmir iline bağlı ve antik çağın en büyük şehirlerinden biri olan "
        "efsanevi bir kenttir. Mermer sütunlarla döşeli Kuretes Caddesi, görkemli Celsus Kütüphanesi ve "
        "25.000 kişilik dev tiyatrosuyla Efes, Akdeniz uygarlığının en parlak dönemlerine ışık tutar. "
        "Her adımda tarihin sesini duyabileceğin bu antik kentte, geçmişle geleceğin buluştuğu "
        "unutulmaz bir macera seni bekliyor!",
    ),
    (
        "catalhoyuk",
        "Çatalhöyük, Konya ovasında yer alan ve yaklaşık 9.000 yıl önce kurulmuş dünyanın en eski "
        "şehir yerleşimlerinden biridir. Evlerin birbirine bitişik inşa edildiği ve kapıların çatıdan "
        "açıldığı bu eşsiz kentte, insanlığın ilk sanat eserleri ve renkli duvar resimleri bulunmuştur. "
        "Çatalhöyük, atalarımızın nasıl yaşadığını, ne yediğini ve neler hayal ettiğini gösteren "
        "gerçek bir zaman kapsülüdür!",
    ),
    (
        "sumela",
        "Sümela Manastırı, Trabzon'un yemyeşil ormanlarında, dik bir kayalığa adeta yapışmış gibi "
        "duran ve 4. yüzyılda inşa edilmiş efsanevi bir yapıdır. Karadeniz'in sisli dağlarında, "
        "şelale seslerinin eşliğinde yükselen bu manastır, renkli freskler ve gizemli koridorlarıyla "
        "ziyaretçilerini büyüler. Doğanın içinde yükselen bu tarihi yapı, her çocuğun hayal gücünü "
        "ateşleyen gerçek bir kaya sarayıdır!",
    ),
    (
        "sultanahmet",
        "Sultanahmet, İstanbul'un kalbinde yer alan ve binlerce yıllık tarihin iç içe geçtiği büyülü "
        "bir meydandır. Mavi Cami'nin altı minaresi, Ayasofya'nın muhteşem kubbesi ve Hipodrom'un "
        "antik sütunları bu alanda yan yana yükselir. Roma, Bizans ve Osmanlı uygarlıklarının izlerini "
        "taşıyan bu eşsiz mekân, her adımda farklı bir tarihin kapısını aralar. İstanbul'un kalbi "
        "Sultanahmet'te, geçmiş ile bugün el ele tutuşur!",
    ),
    (
        "galata",
        "Galata Kulesi, İstanbul'un Beyoğlu semtinde yükselen ve yaklaşık 700 yıllık geçmişiyle "
        "şehrin simgesi haline gelmiş görkemli bir yapıdır. Efsaneye göre Hezarfen Ahmed Çelebi, "
        "bu kuleden kanatlarıyla uçarak Boğaz'ı geçmiştir! Dar taş sokaklarla çevrili Galata "
        "semtinde müzisyenler, sanatçılar ve renkli dükkanlar sizi karşılar. Galata'da her köşe, "
        "hayal gücünü besleyen yeni bir hikaye barındırır!",
    ),
    (
        "kudus",
        "Kudüs, üç büyük dinin kutsal şehri olup binlerce yıllık tarihi, kültürü ve mimarisiyle "
        "dünyanın en özel şehirlerinden biridir. Eski Şehir'in dar taş sokakları, renkli çarşılar "
        "ve antik surlar arasında dolaşmak, zamanın içinde bir yolculuğa çıkmak gibidir. "
        "Zeytin ağaçları, baharat kokuları ve farklı kültürlerin bir arada yaşadığı bu kadim "
        "şehirde, her taş bir medeniyetin izini taşır!",
    ),
    (
        "abusimbel",
        "Ebu Simbel, Mısır'ın güneyinde, Nil kıyısında yükselen ve yaklaşık 3.300 yıl önce "
        "Firavun II. Ramses tarafından inşa ettirilen dev bir tapınak kompleksidir. Dört devasa "
        "Ramses heykeli tapınağın girişini bekler; her yıl iki kez, güneş ışınları tam olarak "
        "tapınağın derinliklerine kadar ulaşır. Çöl kumlarının altında yüzyıllarca saklı kalan "
        "bu efsanevi yapı, antik Mısır'ın büyüsünü ve gücünü günümüze taşır!",
    ),
    (
        "tacmahal",
        "Tac Mahal, Hindistan'ın Agra şehrinde yükselen ve 17. yüzyılda inşa edilmiş dünyanın "
        "en güzel yapılarından biri olarak kabul edilen bir mimari şaheserdir. Bembeyaz mermerden "
        "inşa edilen bu görkemli yapı, güneşin konumuna göre pembe, altın ve gümüş renklere "
        "bürünür. Simetrik bahçeleri, yansıma havuzu ve ince işlemeli minareleriyle Tac Mahal, "
        "sanatın ve mimarinin sınırlarını zorlayan, insanı büyüleyen bir dünya harikasıdır!",
    ),
    (
        "yerebatan",
        "Yerebatan Sarnıcı, İstanbul'un Sultanahmet semtinin hemen altında gizlenen ve 6. yüzyılda "
        "Bizans İmparatoru Justinianus tarafından inşa ettirilen büyülü bir yeraltı sarayıdır. "
        "Yüzlerce antik mermer sütunun su yüzeyine yansıdığı bu gizemli mekânda, kehribar ışıklar "
        "sütunlar arasında dans eder. En ilginç köşesinde ise ters ve yan duran iki Medusa başı "
        "sütun kaidesi bulunur. Yerebatan'da her adım, Bizans'ın gizemli dünyasına açılan "
        "bir kapıdır!",
    ),
]


def upgrade() -> None:
    for theme_key, description in _DESCRIPTIONS:
        op.execute(
            sa.text(
                "UPDATE scenarios SET description = :desc "
                "WHERE theme_key = :key "
                "AND (description IS NULL OR description = '' OR length(description) < 20)"
            ).bindparams(desc=description, key=theme_key)
        )


def downgrade() -> None:
    pass
