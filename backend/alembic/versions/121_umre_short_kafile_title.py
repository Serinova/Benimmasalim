"""Umre: kısa metin, kafile, uçak yok, kitap adı Kutsal Topraklara Ziyareti, custom_inputs kaldır.

Revision ID: 121_umre_short_kafile
Revises: 120_umre_story_rebalance
Create Date: 2026-03-05
"""

from alembic import op
from sqlalchemy.sql import text

revision = "121_umre_short_kafile"
down_revision = "120_umre_story_rebalance"
branch_labels = None
depends_on = None

NEW_NAME = "Kutsal Topraklara Ziyareti"
NEW_DESCRIPTION = (
    "Kafile ile Mekke ve Medine'ye umre ziyareti. "
    "Kabe ilk görüş, tavaf, Sa'y, saç kesme, Mescid-i Nebevi, Uhud, Hendek. "
    "Kitap adı: [Çocuk adı]'ın Kutsal Topraklara Ziyareti."
)

NEW_STORY_PROMPT_TR = r"""
# KUTSAL TOPRAKLARA ZİYARET — UMRE

## YAPI: {child_name} KAFİLE İLE UMRE YAPIYOR. UÇAK SAHNESİ YOK.

**KRİTİK — METİN UZUNLUĞU:** Her sayfa MUTLAKA kısa olsun; sayfaya sığmalı. Her sayfa 1-3 cümle, toplam 25-50 kelime. Daha uzun yazma; kurguyu bozmadan %30 kısa tut.

**KIYAFET:** Erkekler ihrama girince 2 parça dikişsiz beyaz bez, BAŞ AÇIK (takke yok). Saç kesilene kadar ihramda. Saç kesildikten sonra traşlı kafa + takke (baş örtüsü değil, takke). Kızlar hicap giyer.

**AKIŞ:** Havalimanı → ihram hazırlığı ve giriş → (Cidde varışı sonrası) Kabeye doğru ihramla yürüyüş, Lebbeyk sesleri → Kabe ilk görüş (ilk görüşte duaların kabulü dileği vurgula) → Tavaf 3 sayfa → Sa'y 2 sayfa → Saç kesme 1 sayfa → Mekke'deki kubbeli mescide ziyaret 2 sayfa → Medine yolculuğu → Mescid-i Nebevi (Resulullah hakkında bilgi, hissiyat) → Uhud tepesi 1 sayfa → Hendek Savaşı 1 sayfa → Eve dönüş.

---

### Sayfa 1-2: Havalimanı, kafile, ihram hazırlığı
- {child_name} kafile ile havalimanında buluşuyor. Heyecanlı. Uçak sahnesi YOK.
- İhrama hazırlanıyorlar: beyaz, dikişsiz 2 parça bez. Niyet, telbiye. Baş açık kalacak (erkekler için).

### Sayfa 3: Cidde varışı, Kabeye doğru yürüyüş
- Cidde'ye varıldı. Kabeye doğru ihramlı yürüyüş. "Lebbeyk Allahümme Lebbeyk" sesleri her yerde.

### Sayfa 4-5: Kabe ilk görüş
- Mescid-i Haram'a adım. Kabe ilk kez görülüyor. Gözyaşları, huşu.
- İlk görüşte edilen duaların kabul edildiği inancı vurgula. {child_name} içinden ne dilerse kalbiyle orada.

### Sayfa 6-8: Tavaf (3 sayfa)
- Tavafa başlama — Hacerülesved, 7 tur. İhramda, baş açık.
- Tavafın anlamı: Kabe etrafında birlikte dönmek, tek yürek. Kısa vurgu.
- Tavaf bitişi. Makam-ı İbrahim, Zemzem bir yudum.

### Sayfa 9-10: Sa'y (2 sayfa)
- Safa'dan Merve'ye 7 gidiş-geliş başlıyor. Hz. Hacer'in hikâyesi kısaca.
- Sa'y bitişi. Yoruldu ama tamamladı.

### Sayfa 11: Saç kesme (halq)
- Saç traş ediliyor (halq). İhramdan çıkış. Yenilenme, huzur. Sebebi ve hissiyatı kısa.

### Sayfa 12-13: Mekke — kubbeli mescit ziyareti (2 sayfa)
- Mekke'deki kubbeli mescide ziyaret. Tarih, maneviyat.
- Orada anlatılanlar, {child_name}'ın hissettiği huzur. 2 sayfa toplam.

### Sayfa 14: Medine yolculuğu
- Medine'ye yolculuk. Yeşil kubbe uzaktan. Artık traşlı kafa + takke (erkek). Kızlar hicap.

### Sayfa 15: Mescid-i Nebevi, Resulullah
- Mescid-i Nebevi. Yeşil kubbe. Resulullah (sav) hakkında bilgi, saygı, hissiyat. Görselleştirme yok, sadece anlatım.

### Sayfa 16: Uhud tepesi
- Uhud tepesi ziyareti. Tarihî önemi kısaca, bir sayfa.

### Sayfa 17: Hendek Savaşı
- Hendek (Ahzab) hatırası. Bir sayfa vurgu.

### Sayfa 18+: Eve dönüş ve kapanış
- Eve dönüş. "Kutsal topraklar beni değiştirdi." Kısa, duygusal kapanış. Kalan sayfa sayısına göre 1-2 sayfa.

---

## GÖRSEL KURALLAR
- Sayfa 1-2: Henüz ihram yok veya hazırlık (erkekte baş açık).
- Sayfa 3-10: İHRAM — 2 parça beyaz bez, BAŞ AÇIK (takke yok).
- Sayfa 11: Tıraş anı (halq).
- Sayfa 12-22: Traşlı kafa (erkek), takke takılı. Kızlar hicap.
- Peygamber/melek görseli YOK. Vaaz yok, yaşayarak anlat.
- İlk sayfa [Sayfa 1] ile başla. Uçak, kabin, uçuş sahnesi ÇİZME.

Hikayeyi TAM OLARAK {page_count} sayfa yaz. Her sayfa 1-3 cümle (25-50 kelime). Kısa tut; sayfaya sığsın.
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE scenarios
            SET name = :name,
                description = :description,
                story_prompt_tr = :prompt,
                custom_inputs_schema = '[]'::jsonb
            WHERE theme_key = 'umre_pilgrimage'
        """),
        {
            "name": NEW_NAME,
            "description": NEW_DESCRIPTION,
            "prompt": NEW_STORY_PROMPT_TR.strip(),
        },
    )


def downgrade() -> None:
    pass
