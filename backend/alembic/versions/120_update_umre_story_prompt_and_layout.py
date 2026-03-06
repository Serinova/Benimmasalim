"""Update Umre scenario: rebalanced story prompt (more Medina, ihram state info, halq timeline).

Revision ID: 120_umre_story_rebalance
Revises: 119_update_umre_boy_taqiyah
Create Date: 2026-03-05
"""

from alembic import op
from sqlalchemy.sql import text

revision = "120_umre_story_rebalance"
down_revision = "119_update_umre_boy_taqiyah"
branch_labels = None
depends_on = None

# Story prompt updated: added ihram state visual annotations, more Medina pages (17-20),
# halq (tıraş) moved earlier (page 15-16), flight pages reduced.
NEW_STORY_PROMPT_TR = """\
# UMRE YOLCULUĞU — KUTSAL TOPRAKLARDA MANEVİ KEŞİF

## TEMEL YAPI: 7 BÖLÜM, 22 SAYFA

Bu hikaye bir manevi yolculuk. {child_name}, büyükleriyle birlikte umre
yapmaya gidiyor. Her ibadet adımında çocuğun İÇ DÜNYASI'ndaki bir
duyguyla yüzleşmesi ve o ibadetin manevi anlamıyla dönüşmesi anlatılır.

ÖNEMLİ KURALLAR:
- Umre ibadeti DOĞRU SIRAYLA yapılmalı: İhram → Telbiye → Tavaf → Sa'y → Zemzem → Tıraş (Halq) → Medine
- İHRAM KIYAFETİ: İhrama girince (Sayfa 3'ten başlayarak Sayfa 14 tıraşa kadar) beyaz 2 parça dikişsiz bez giyin — TAKKE YOKTUR! İhramda başı AÇIK olmalı.
- TIRAŞ/HALQ sonrası (Sayfa 15-16): Saç tamamen traş edilmiş; ihramdan çıkılır, normal kıyafet.
- Çocuk büyükleriyle birlikte (yüzleri, kıyafetleri, fiziksel özellikleri ASLA tarif edilmez)
- Her ibadette çocuğun bir İÇ SAVAŞI var — ibadet onu dönüştürüyor
- Vaaz edici DEĞİL, YAŞAYARAK öğrenme
- Hz. Muhammed, peygamberler, melekler GÖRSELLEŞTİRİLMEZ (sadece hikâye anlatımı)
- Korku/baskı/travma YOK
- Saygılı, huzurlu, duygusal ton

---

### BÖLÜM 1 — HAZIRLIK VE İHRAMA GİRİŞ (Sayfa 1-3)
Havaalanında heyecan. Büyükleriyle kutsal topraklara gidiş. Mikat'a
yaklaşırken ihrama giriş — beyaz, sade, dikişsiz kıyafet. BAŞI AÇIK.
- S1: Havaalanı heyecanı, büyükleriyle yolculuk
- S2: Mikat'a yaklaşma, ihram hazırlığı (beyaz bez)
- S3: İhrama giriş — "Neden herkes aynı?" İÇ SAVAŞ — "Herkes eşit" FARKINDALIK
**Değer**: Tevazu, eşitlik, sadelik

---

### BÖLÜM 2 — TELBİYE VE KABE (Sayfa 4-7)
Telbiye okuyarak Mekke'ye giriş. HÂLÂ İHRAMDA (başı açık).
- S4: Telbiye okuyarak yürüyüş — "Lebbeyk..." + Mekke girişi
- S5: Mescid-i Haram kapısı — heybetli mimari
- S6: KABE'Yİ İLK GÖRÜŞ — gözyaşları, hayranlık DORUK DUYGU
- S7: "Kalbim durdu..." — huşu, hayranlık. İhramda, Kabe'nin önünde.
**Değer**: Teslimiyet, huşu, sabır

---

### BÖLÜM 3 — TAVAF: KABE'NİN ETRAFINDA 7 TUR (Sayfa 8-10)
Hacerülesved köşesinden başlayarak Kabe'nin etrafında 7 tur.
HÂLÂ İHRAMDA (başı açık). Binlerce insan birlikte dönüyor.
- S8: Tavafa başlama — Hacerülesved, ihramlı kalabalık
- S9: 7 tur — farklı ülkeler, tek yürek; {child_name} yoruluyor ama devam ediyor
- S10: Makam-ı İbrahim'de dua — "Hepimiz biriz" BİRLİK ZİRVESİ
**Değer**: Birlik, bencillikten kurtulma

---

### BÖLÜM 4 — SA'Y: SAFA-MERVE ARASI 7 GİDİŞ-GELİŞ (Sayfa 11-13)
Safa Tepesi'nden Merve'ye 7 kez. HÂLÂ İHRAMDA (başı açık).
- S11: Safa'dan başlama — uzun beyaz koridor, ihramlı kalabalık
- S12: Hz. Hacer'in hikâyesi; {child_name} yoruluyor İÇ SAVAŞ
- S13: Son tur — "Vazgeçmediğinde mucize gelir!" SEBAT ZİRVESİ
**Değer**: Sebat, umut, vazgeçmeme

---

### BÖLÜM 5 — ZEMZEM VE TIRAŞ/HALQ (Sayfa 14-16)
Zemzem içme (ihramdayken). Ardından kutsal tıraş (halq) — ihramdan çıkış.
- S14: Zemzem suyu — ihramdayken (başı açık); "Binlerce yıldır akıyor!" ŞÜKÜR
- S15: Tıraş alanı — minik saçlar traş ediliyor (halq ritual) YENİLENME
- S16: Tıraş sonrası aynaya bakış — ihramdan çıkış, huzur DÖNÜŞÜM
NOT: Sayfa 15'te tıraş yapılıyor. Sayfa 16'dan itibaren saç SIFIR (traşlı kafa).
**Değer**: Şükür, yenilenme, nimet bilinci

---

### BÖLÜM 6 — MEDİNE: YEŞİL KUBBE VE HUZUR (Sayfa 17-20)
Medine'ye yolculuk. Mescid-i Nebevi, yeşil kubbe, hurma ağaçları.
Saç kısa/traşlı. Normal kıyafet + takke takabilir.
- S17: Medine'ye varış — hurma ağaçları, yeşil kubbe uzaktan görünüyor
- S18: Mescid-i Nebevi'ye giriş — sakin, huzurlu avlu
- S19: Yeşil kubbenin altında sessiz an — iç huzur HUZUR ZİRVESİ
- S20: Medine sokaklarında yürüyüş — hurma pazarı, insanlar, renkler
**Değer**: İç huzur, tefekkür, sakinlik

---

### BÖLÜM 7 — FİNAL: DÖNÜŞ VE YENİ BEN (Sayfa 21-22)
- S21: Dönüş uçuşu — camdan bulutlara bakarken iç muhasebe
- S22: "Ben aynı ben değilim. Umre beni değiştirdi." DÖNÜŞÜM DORUĞU
**Değer**: Manevi dönüşüm, yenilenme, minnet

---

## GÖRSELİ ETKİLEYEN KRİTİK KISIMLAR:
- Sayfa 1-2: Normal kıyafet, henüz ihrama girilmedi
- Sayfa 3-14: İHRAM KIYAFETİ — 2 parça dikişsiz beyaz bez, BAŞ AÇIK (takke yok!)
- Sayfa 15: TIRAŞ ANI (halq) — saç kesiliyor
- Sayfa 16-22: Traşlı kafa (sıfır/kısa saç), normal kıyafet + takke takılabilir

## GÜVENLİK KURALLARI:
- Peygamber/melek görseli YOK
- İlk sayfa her zaman "[Sayfa 1]" diye başlamalıdır.
- İbadet close-up YOK
- Korku/baskı/travma YOK
- Vaaz edici DEĞİL, yaşayarak öğrenme
- Gerçek dışı/fantastik öğeler YOK

Hikayeyi TAM OLARAK {page_count} sayfa olacak şekilde yaz. Her sayfa 2-4 cümle (40-80 kelime) olmalıdır. İlk sayfa [Sayfa 1] ile başlamalıdır.
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            "UPDATE scenarios SET story_prompt_tr = :prompt "
            "WHERE theme_key = 'umre_pilgrimage'"
        ),
        {"prompt": NEW_STORY_PROMPT_TR},
    )


def downgrade() -> None:
    pass  # story_prompt_tr rollback not critical
