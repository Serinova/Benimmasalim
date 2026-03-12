# Senaryo Şablonu — BenimMasalım

> Bu şablonu doldurmadan önce SKILL.md'yi oku.
> Her bölümü eksiksiz doldur. Eksik bırakılan bölümler kalite puanını düşürür.

---

## 📌 SENARYO TİPİ

```
Senaryo Adı (TR)  : _______________________________________________
Tema Anahtarı   : _______________________________________________  (snake_case, benzersiz)
Senaryo Tipi    : □ TİP A: Tek Landmark  □ TİP B: Geniş Ortam  □ TİP C: Fantastik
Kategori        : □ Tarihi  □ Doğa  □ Uzay  □ Fantezi  □ Kültürel  □ Dini/Manevi
```

---

## BÖLÜM A — TEMEL KİMLİK

```yaml
name: ""                    # Türkçe, çekici senaryo adı
tagline: ""                 # Tek satır reklam sloganı (max 60 karakter)
description: ""             # 2-3 cümle kısa tanım (kullanıcıya gösterilir)
age_range: ""               # örn: "5-9 yaş"
estimated_duration: ""      # örn: "15-20 dakika okuma"
marketing_badge: ""         # örn: "Yeni!", "En Çok Tercih", "Zaman Yolculuğu"
marketing_price_label: "299 TL'den başlayan fiyatlarla"
marketing_features:         # 5-7 madde, somut özellikler
  - ""
  - ""
  - ""
  - ""
  - ""
```

---

## BÖLÜM B — TEKNİK BİLGİLER

```yaml
location_en: ""             # İNGİLİZCE lokasyon adı (Flux AI için) — Türkçe yazma!
theme_key: ""               # snake_case, örn: "galata_tower", "amazon_rainforest"
default_page_count: 22
display_order: 0            # Mevcut son sıradan devam et
linked_product: "A4 YATAY 32 sayfa"   # Genellikle bu

flags:
  no_family: false          # true ise anne/baba/kardeş sahnesi çıkar
  # indoor_only: false      # Sadece iç mekan ise true
```

---

## BÖLÜM C — KÜLTÜREL ATLAS (Min. 10 Mekan/Öğe)

> Her mekanın SADECE NE OLDUĞUNU değil, hikayede OYNAYABİLECEĞİ ROLÜ de yaz.
> Gezi rehberi değil — dramalık araç perspektifinden düşün.

```
1. [MEKAN ADI] — [Görsel özelliği] → [Hikayedeki dramatik potansiyeli]
   Örn: "Spiral taş merdiven — dar, yosunlu, her katta kemerli pencere 
         → Çocuğun tırmanırken her katta farklı bir sırrı keşfetmesi"

2. _______________________________________________

3. _______________________________________________

4. _______________________________________________

5. _______________________________________________

6. _______________________________________________

7. _______________________________________________

8. _______________________________________________

9. _______________________________________________

10. _______________________________________________
```

---

## BÖLÜM D — YARDIMCI KARAKTER KADROSU (Min. 4 Seçenek)

> Her karakter lokasyonla organik bağlantılı olmalı.
> Sadece "kartal" değil — bu kartal NEDEN bu mekânda?

```
1. [KARAKTER ADI] ([tür/cins])
   → Nasıl var oldu: _______________________________________________
   → Rolü (Mentor/Arkadaş/Rehber): _______________
   → Görsel ayırt edici özelliği: _______________________________________________

2. [KARAKTER ADI] ([tür/cins])
   → _______________________________________________

3. [KARAKTER ADI] ([tür/cins])
   → _______________________________________________

4. [KARAKTER ADI] ([tür/cins])
   → _______________________________________________
```

---

## BÖLÜM E — STORY PROMPT TR (Gemini İçin — Min. 400 Kelime)

> **En kritik bölüm.** Şu formatı kullan:
> Doldurulmuş örnekler için `examples/catalhoyuk_reference.md` veya
> `backend/alembic/versions/064_populate_all_scenario_story_prompts.py` dosyasına bak.

```
Sen ödüllü çocuk kitabı yazarı ve [LOKASYON] uzmanısın.
Kahraman, yaş ve eğitsel değerler yukarıda verilmiştir. Görevin: [LOKASYON]'da geçen
büyülü bir macera yazmak.

[LOKASYON] — KULLANILACAK KÜLTÜREL MEKANLAR (hikayeye en az 6 tanesini entegre et):
1. [Mekan 1 — detaylı açıklama]
2. [Mekan 2]
3. [Mekan 3]
...

YARDIMCI KARAKTER (en az biri hikayede olsun):
[Karakter 1 (özelliği, nasıl beliriyor)],
[Karakter 2], [Karakter 3].
Karakter, [lokasyonla bağlantılı] "uyanmış" olabilir.

ÖNEMLİ — BU BİR GEZİ REHBERİ DEĞİL, BİR MACERA HİKAYESİ!
[Lokasyon] mekanları ARKA PLAN olarak kullan. Hikayenin motorunu MEKANLAR DEĞİL,
çocuğun İÇ YOLCULUĞU ve eğitsel değerler oluştursun.

YANLIŞ: "[Karakter] [mekan]ı gördü. Sonra [mekan2]'a baktı."
DOĞRU: Çocuğun bir SORUNU/ZAYIFLIĞI var. Bu sorun [lokasyon]'un büyülü mekanlarında
bir MACERA'ya dönüşüyor.

EĞİTSEL DEĞER ENTEGRASYONU:
- [Değer 1] seçildiyse: [somut senaryo bağlantısı]
- [Değer 2] seçildiyse: [somut senaryo bağlantısı]
- [Değer 3] seçildiyse: [somut senaryo bağlantısı]
- [Değer 4] seçildiyse: [somut senaryo bağlantısı]
Değer sadece "söylenmesin", çocuk YAŞAYARAK öğrensin!

🎬 SAHNE YÖNETMENİ TALİMATLARI — LOKASYON AKIŞI:
[Senaryo tipine göre aşağıdakilerden uygun olanı seç ve doldur]

# TİP A (Tek Landmark) için:
Kilit kural: Çocuk [X] sayfalık kitapta [LOKASYON ADI]'nı geziyor ama HER KAREDE
[LOKASYON] çizmek YASAK. Sinematik bir akış ol:
◉ AÇILIŞ SHOTS (s.1-2): [LOKASYON] tam görünür, görkemli, geniş açı
◉ YAKLAŞMA (s.3-5): Lokasyon arka planda kalır, karakter ön planda
◉ İÇ DÜNYA (s.6-14): Lokasyonun iç mekânları — lokasyon adını her sayfaya yazma!
   → Atmosferi hissettir: [senaryoya özgü 3 atmosfer detayı]
◉ KRİTİK AN (s.15-18): Lokasyonun EN etkileyici noktasında büyük sahne
◉ KAPANIŞ (s.19-22): Lokasyon yeniden tam görünür, güçlü final
ÖNEMLİ: [LOKASYON ADI]'nı HER sayfaya yazma — 5-6 sayfada yazan yeter.
Lokasyon olmayan sahnelerde şu detaylardan birini ver: [atmosfer detayları]

# TİP B (Geniş Ortam) için:
Kamera açısı ZORUNLU ÇEŞİTLİLİĞİ — aynı sahneyi tekrarlama:
◉ Bazı sahneler: [Alt-lokasyon 1] — close-up / detail shot
◉ Bazı sahneler: [Alt-lokasyon 2] — wide epic panorama
◉ Bazı sahneler: [Alt-lokasyon 3] — medium action shot
◉ Bazı sahneler: Interior/underground — completely different atmosphere
image_prompt_en'de kamera açısını MUTLAKA belirt: (close-up / wide / medium / aerial)

🦊 YARDIMCI KARAKTER TUTARLILIĞI ZORUNLU:
[Karakter Adı] = "[ANCHOR CÜMLE — tüm sayfalar için sabit görsel tanım]"
Bu tanım TÜM SAYFALARDA AYNI kalacak. image_prompt_en'de her göründüğünde
bu tanımı AYNEN kullan, renk/boyut DEĞİŞTİRME.

✨ ÖZEL EŞYA TUTARLILIĞI ZORUNLU:
[Eşya Adı] = "[ANCHOR CÜMLE — renk, boyut, görünüm SABIT]"
Hikayede bu eşya göründüğünde image_prompt_en'e AYNI tanımı ekle.

ÖNEMLİ KISITLAMALAR:
[Senaryo özelinde içerik kuralları]

SAHNE AÇIKLAMASI KURALLARI (image_prompt_en için ipucu):
Her sahne için spesifik lokasyon ve mimari/doğal detay kullan.
Örn: [3-4 somut örnek cümle]
```

---

## BÖLÜM F — GÖRSEL PROMPT ŞABLONLARI

### F-1: Kapak Prompt Şablonu (`cover_prompt_template`)

> Kapak = ikonik sahne, geniş açı, çocuk %30 önde, mekân %70 arkada.
> Varsayılanı KULLANMA — senaryoya özgü yaz.

```
Story "{book_title}". A young child {scene_description}.
The child is wearing {clothing_description}.
[LOKASYONA ÖZGÜ: İKONİK ARKA PLAN TANIMI — örn: "the towering stone Galata Tower filling 
the golden afternoon sky behind the child"]
[EK ATMOSFER DETAYI — renkler, ışık, hava]
Composition: dramatic low-angle hero shot, child in foreground, landmark filling background,
space for title at the top.
```

### F-2: İç Sayfa Prompt Şablonu (`page_prompt_template`)

> Varsayılanı KULLANMA — lokasyon öğeleri listesi ekle.
> TİP A/B/C'ye göre strateji farklı (SKILL.md Adım 3'e bak).

```
A young child {scene_description}.
The child is wearing {clothing_description}.
Setting elements (choose relevant based on scene):
  EXTERIOR: [Dış mekan öğeleri listesi]
  INTERIOR: [İç mekan öğeleri listesi]
  ATMOSPHERIC: [Renk, doku, ışık atmosfer öğeleri]
Shot variety: [close-up macro / medium action / wide epic / interior moody]
Composition: full body visible in action, text overlay space at bottom.
Earthy/vivid palette: [senaryo renk paleti].
```

### F-3: Lokasyon Kısıtlamaları (`location_constraints`)

```
Primary landmark: [LOKASYON] — visible in opening scenes (p.1-2), climax (p.15+), and closing
Interior spaces: [İÇ MEKAN LİSTESİ] — no full exterior shot needed in these scenes
Atmospheric cues (always usable, even without landmark visible):
  - [Lokasyona özgü detay 1]
  - [Lokasyona özgü detay 2]
  - [Lokasyona özgü detay 3]
Camera variation: alternate between [geniş / orta / yakın / havadan / iç mekan] shots
```

---

## BÖLÜM G — KAHRAMAN KIYAFETİ (3 Seçenek)

> Antigravity 3 seçenek üretir, kullanıcı seçer.
> Kıyafet kuralları: Senaryo temasına uygun, çocuk güvenliği standardı
> (mini etek YASAK, kısa şort YASAK, karın açık YASAK), İNGİLİZCE yaz.

```
── SEÇENEK 1: [KIYAFET TEMA İSMİ] ──
   Kız versiyonu: [İngilizce tam tanım — her detayı ver]
   Erkek versiyonu: [İngilizce tam tanım]
   Neden uygun: [1 cümle tema ile bağlantı]

── SEÇENEK 2: [KIYAFET TEMA İSMİ] ──
   Kız versiyonu: [İngilizce tam tanım]
   Erkek versiyonu: [İngilizce tam tanım]
   Neden uygun: [1 cümle]

── SEÇENEK 3: [KIYAFET TEMA İSMİ] ──
   Kız versiyonu: [İngilizce tam tanım]
   Erkek versiyonu: [İngilizce tam tanım]
   Neden uygun: [1 cümle]
```

**Kullanıcı seçiminden sonra doldur:**
```yaml
outfit_girl: ""    # Seçilen kız versiyonu + "EXACTLY same outfit on every page"
outfit_boy: ""     # Seçilen erkek versiyonu + "EXACTLY same outfit on every page"
```

---

## BÖLÜM G2 — KARAKTER TUTARLILIK KARTLARI

### G2-a: Yardımcı Karakter Görsel Kimlik Kartı

```
YARDIMCI KARAKTER: [karakter adı]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tür/Cins          : [örn: kızıl tilki, küçük boy]
Renk              : [örn: bright orange fur with white chest]
Boyut             : [örn: small, about knee-height to child]
Ayırt edici öğe   : [örn: tiny wooden bead necklace]
Göz               : [örn: amber eyes]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANCHOR CÜMLE (image_prompt_en'e her sayfada eklenecek):
"[karakter adı], a [renk] [tür] with [ayırt edici öğe]"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### G2-b: Özel Eşya/Obje Kartı (Varsa Doldur)

```
EŞYA ADI: _______________
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Renk ve doku    : _______________________________________________
Boyut           : _______________________________________________
Özel görünüm    : _______________________________________________  (parlar mı? oyma var mı?)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANCHOR CÜMLE: "holding/wearing [obje tam tanımı]"
Göründüğü sayfalar: _______________
```

### G2-c: Yan Rol Karakter Kartı (Varsa Doldur)

```
YAN ROL: _______________ (belirdiği sayfalar: _______)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Kıyafet         : [İngilizce, sabit tanım]
Saç/Sakal       : _______________________________________________
Ayırt edici öğe : _______________________________________________
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANCHOR CÜMLE: "[yan rol], [yaş/tip] with [kıyafet + ayırt edici öğe]"
```

---

## BÖLÜM G3 — GÖRSEL AKIŞ & LOKASYON KADEME HARİTASI

> TİP A senaryolar için ZORUNLU.

```yaml
location_flow:
  iconic_pages: []        # Lokasyon tam ve görkemli — MAX 4-5 sayfa
  contextual_pages: []    # Lokasyon arka planda
  atmosphere_pages: []    # Lokasyon hissedilir, görünmez
  independent_pages: []   # Lokasyondan bağımsız (iç mekan, yakın plan)

# Kademe dağılımı kuralı:
# İkonik:     %15-20 → max 4-5 sayfa
# Bağlamsal:  %25-30 → 6-7 sayfa
# Atmosfer:   %30-35 → 7-8 sayfa
# Bağımsız:   %15-20 → 4-5 sayfa
```

---

## BÖLÜM H — KÜLTÜREL ELEMENTLER JSON

```json
{
  "location": "[Lokasyon adı, şehir, ülke]",
  "primary": [
    "İkonik öğe 1",
    "İkonik öğe 2",
    "İkonik öğe 3"
  ],
  "secondary": [
    "Destekleyici öğe 1",
    "Destekleyici öğe 2"
  ],
  "colors": "[Renk paleti tanımı]",
  "atmosphere": "[Atmosfer tanımı]",
  "values": ["Değer 1", "Değer 2", "Değer 3"]
}
```

---

## BÖLÜM I — SCENARIO BIBLE JSON (Önerilir)

```json
{
  "cultural_facts": [
    "Çocuğa uygun ilginç gerçek 1",
    "Çocuğa uygun ilginç gerçek 2",
    "Çocuğa uygun ilginç gerçek 3"
  ],
  "allowed_side_characters": [
    {"name": "Karakter Adı", "species": "tür", "role": "mentor/friend/guide"},
    {"name": "Karakter Adı 2", "species": "tür2", "role": "guide"}
  ],
  "puzzle_types": [
    "Hikayede kullanılabilecek bulmaca türü 1",
    "Bulmaca türü 2"
  ],
  "tone_rules": [
    "Bu senaryo özel ton kuralı 1",
    "Ton kuralı 2"
  ]
}
```

---

## BÖLÜM J — ÖZEL GİRDİ ŞEMASI (Gerekiyorsa)

```json
[
  {
    "key": "alan_adi",
    "label": "Kullanıcıya gösterilecek etiket",
    "type": "text",
    "required": true,
    "placeholder": "örnek değer",
    "help_text": "Kullanıcıya yardım metni"
  }
]
```

> Senaryo kurgusunu bozacak özel girdiler EKLEME.
> Çatalhöyük gibi sabit kurgu senaryolarda bu alan BOŞ bırakılmalı.

---

## BÖLÜM K — KALİTE KONTROL PUANLAMASI

> Bu bölümü sen (Antigravity) doldurursun. Kullanıcıya sun.

| # | Kriter | Max | Puan | Not |
|---|--------|-----|------|-----|
| 1 | story_prompt_tr uzunluğu (min 400 kelime) | 10 | | |
| 2 | story_prompt_tr kalitesi (gezi rehberi değil, drama odaklı) | 10 | | |
| 3 | Kültürel mekan sayısı ve hikayedeki rolü (min 10) | 10 | | |
| 4 | Yardımcı karakter çeşitliliği (min 4) | 5 | | |
| 5 | Görsel akış sistemi (G3 kademe haritası) | 10 | | |
| 6 | custom page_prompt_template (varsayılan değil!) | 10 | | |
| 7 | Karakter tutarlılık kartları (G2-a min. 1 kart) | 10 | | |
| 8 | Kahraman kıyafeti — kural uyumu + kilitlenme | 5 | | |
| 9 | Eğitsel değer → olay örgüsü bağlantısı (4 değer) | 5 | | |
| 10 | İçerik güvenliği (kısıtlama uyumu) | 5 | | |
| 11 | Kapak, Arka Kapak ve Karşılama sayfaları düzeni | 10 | | |
| 12 | Işık ve Doku (Lighting & Texture) Vurgusu | 5 | | |
| 13 | Duygu (Emotion) Çıpası | 5 | | |

| **TOPLAM** | | **100** | | |

> **Minimum geçer: 80/100** — Altında olan senaryo tekrar düzenlenmeden sisteme girmez.
