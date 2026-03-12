---
name: Scenario Master — Senaryo Tasarım, Test & Tutarlılık Motoru
description: >
  BenimMasalım V3 pipeline'ını uçtan uca kapsayan MASTER beceri.
  Yeni senaryo oluşturma, mevcut senaryo denetimi, tutarlılık testi ve
  hikaye kalitesi analizi işlemlerini TEK BİR AKIŞTA gerçekleştirir.
  "senaryo oluştur", "senaryo denetle", "tutarlılık kontrolü", "hikaye testi",
  "master analiz", "saç tutarlılığı", "kıyafet kilidi", "companion lock",
  "senaryo puanla", "kalite raporu" dediğinde bu skill OKUNMALIDIR.
---
// turbo-all

# 🎯 Scenario Master Skill
## BenimMasalım — Senaryo Tasarım, Test & Tutarlılık Motoru

> **Bu skill iki ayrı skill'in (Scenario Writer + Dry-Run Tester) birleşimi ve
> genişletilmesidir.** Her iki skill'in eksiklerini kapatır ve pipeline
> bilgisiyle pekiştirir.

---

## ⚡ TEMEL PRENSİP

> Bir senaryo **7 katmanlı tutarlılık testini** geçemezse üretime giremez:
> 1. **Karakter yüzü** (PuLID + face analyzer lock)
> 2. **Saç stili** (hair_description + identity lock)
> 3. **Kıyafet** (outfit lock — senaryo > blueprint > varsayılan)
> 4. **Yardımcı karakter** (companion CAST LOCK — tür, renk, boyut)
> 5. **Önemli objeler** (madalyon, harita, anahtar — anchor cümle)
> 6. **Mekan sürekliliği** (her sayfada lokasyon belirtilmeli)
> 7. **İçerik güvenliği** (yasaklı kelime, aile kısıtı)

---

## 📂 VERİ KAYNAĞI — SENARYOLAR NEREDE?

> **⚠️ KRİTİK: Senaryolar artık veritabanında (DB) DEĞİL, Python dosyalarında kayıtlıdır!**
>
> DB'deki `scenarios` tablosunda sadece marketing alanları (description, tagline, image_url vb.) kalır.
> Prompt, kıyafet, companion, obje, bible gibi **tüm üretim verileri** Python kodundadır.

### 📁 Dosya Konumu

```
backend/app/scenarios/
├── _base.py          # ScenarioContent, CompanionAnchor, ObjectAnchor dataclass'ları
├── _registry.py      # register() fonksiyonu ve get_scenario_content()
├── cappadocia.py     # Kapadokya Macerası
├── gobeklitepe.py    # Göbeklitepe Macerası
├── ephesus.py        # Efes'in Zaman Kapısı
├── catalhoyuk.py     # Çatalhöyük'ün Çatı Yolu
├── sumela.py         # Sümela'nın Kayıp Mührü
├── galata.py         # Galata'nın Gizemli Kedileri
├── solar_system.py   # Güneş Sistemi Macerası
├── dinosaur.py       # Dinozor Çağı Macerası
├── ocean.py          # Okyanusun Derinlikleri
├── fairy_garden.py   # Peri Bahçesi
├── pamukkale.py      # Pamukkale'nin Sırrı
├── troy.py           # Truva'nın Gizemi
├── antalya.py        # Antalya Sualtı Macerası
├── nemrut.py         # Nemrut'un Devleri
├── mardin.py         # Mardin'in Taş Evleri
├── rainbow.py        # Gökkuşağı Adası
└── yerebatan.py      # Yerebatan'ın Sırrı
```

### 🔍 Senaryo İnceleme Yöntemi

Bir senaryoyu analiz etmek için **DB sorgusu YAPMA**, doğrudan dosyayı oku:
```
view_file backend/app/scenarios/<tema>.py
```

Her dosya bir `ScenarioContent` dataclass içerir:
- `theme_key` — benzersiz anahtar
- `story_prompt_tr` — Türkçe hikaye promptu
- `cover_prompt_template` — kapak görseli promptu
- `page_prompt_template` — sayfa görseli promptu
- `outfit_girl` / `outfit_boy` — kıyafet tanımları
- `companions` — `CompanionAnchor` listesi
- `objects` — `ObjectAnchor` listesi
- `cultural_elements` — kültürel öğeler dict
- `location_constraints` — sayfa bazlı lokasyon
- `scenario_bible` — side characters, zone map, consistency rules
- `custom_inputs_schema` — companion seçimi (`type: "hidden"` ZORUNLU)
- `flags` — `no_family`, vb.

---

## 📋 MODÜLLER

Bu skill 4 modülden oluşur. Her modül bağımsız çalışabilir:

| Modül | Komut | Ne Yapar |
|-------|-------|----------|
| **M1: Yeni Oluştur** | `senaryo oluştur` | Sıfırdan senaryo tasarlar |
| **M2: Denetle** | `senaryo denetle` | Mevcut senaryoyu 10 kriter + 7 hikaye metriği ile puanlar |
| **M3: Tutarlılık Testi** | `tutarlılık kontrolü` | Kıyafet, saç, companion, obje, placeholder kontrolü |
| **M4: Pipeline Simülasyonu** | `senaryo test et` | Gerçek PASS-0 + PASS-1 çalıştırıp çıktıyı analiz eder |

---

## 🏗️ MODÜL 1: YENİ SENARYO OLUŞTUR (M1)

### Adım 1.1 — Senaryo Tipini Belirle

| Tip | Tanım | Örnek |
|-----|-------|-------|
| **TİP A: Tek Landmark** | Belirli yapı/yer etrafında geçer | Galata, Efes, Yerebatan |
| **TİP B: Geniş Ortam** | Büyük bölge — tek yapı yok | Amazon, Uzay, Okyanus |
| **TİP C: Fantastik** | Büyü, zaman yolculuğu | Çatalhöyük, Dinozor |

### Adım 1.2 — 13 Bölümlü Senaryo Kartını Doldur

| # | Bölüm | Açıklama | Zorunlu |
|---|-------|---------|---------|
| A | Temel Kimlik | İsim, tagline, yaş aralığı | ✅ |
| B | Teknik Bilgi | theme_key, location_en, flags | ✅ |
| C | Kültürel Atlas | Min. 10 mekan/öğe + hikayedeki rolleri | ✅ |
| D | Yardımcı Karakter Kadrosu | Min. 4 seçenek + görsel ANCHOR | ✅ |
| E | story_prompt_tr | Min. 400 kelime + DOĞRU/YANLIŞ örnekler | ✅ |
| F | Görsel Prompt Şablonları | cover + page prompt template | ✅ |
| G | Kahraman Kıyafeti | outfit_girl + outfit_boy (İngilizce) | ✅ |
| **G2** | **Tutarlılık Kartları** | Companion, obje, yan rol anchor'ları | ✅ |
| **G3** | **Görsel Akış Haritası** | Kademe haritası + kamera açıları | ✅ |
| H | Kültürel Elementler JSON | cultural_elements alanı | ✅ |
| I | Scenario Bible | Companion + obje + lokasyon paketi | ✅ (**Yeni: önceden opsiyoneldi**) |
| J | Custom Inputs Schema | Companion seçimi + özel girdiler | Gerekiyorsa |
| K | Kalite Kontrol | 80 puan checklist | ✅ |

### Adım 1.3 — G2 Tutarlılık Kartları (KRİTİK!)

> [!IMPORTANT]
> Bu bölüm **ÖNCEKİ skill'de eksikti**, şimdi ZORUNLU. Pipeline'ın CAST LOCK
> mekanizması bu kartlardaki bilgiyi kullanır.

#### G2-a: Yardımcı Karakter ANCHOR Kartı

Her companion seçeneği için şu formatı doldur:

```
🦊 COMPANION ANCHOR — [Karakter Adı]
├── species: [İngilizce tür — "fox", "eagle", "wild horse"]
├── appearance_en: [20-40 kelime fiziksel tanım — renk, boyut, ayırt edici öğe]
├── appearance_tr: [Türkçe karşılık — hikaye metninde kullanılacak]
└── consistency_rule: "Bu tanım TÜM SAYFALARDA AYNI — DEĞİŞTİRME"
```

**Pipeline bağlantısı:** Bu bilgi `_extract_companion_from_pages()` fonksiyonundaki
`_COMPANION_MAP` sözlüğüne eklenir. Yeni companion ekleniyorsa bu sözlük
güncellenmeli: `backend/app/tasks/generate_book.py` ve
`backend/app/services/ai/_story_blueprint.py`

#### G2-b: Önemli Obje ANCHOR Kartı

```
🗝️ OBJE ANCHOR — [Obje Adı]
├── appearance_en: "ancient golden medallion with carved sun symbol, palm-sized"
├── first_appear: Sayfa X
├── last_appear: Sayfa Y
└── prompt_suffix: "holding/wearing [obje tanımı] — SAME appearance on every page"
```

#### G2-c: Yan Rol Karakter Kartı (varsa)

```
👤 YAN ROL — [Karakter Adı]
├── outfit_en: "elderly craftsman in brown leather apron and white cotton shirt"
├── appears_on: [sayfa listesi]
└── rule: "SAME outfit on every appearance"
```

### Adım 1.4 — story_prompt_tr Standart Blokları

Her story_prompt_tr şunları İÇERMELİ:

```
1. GIRIŞ (kim, nerede, niçin) — ilk birkaç cümle
2. BÖLÜMLER (her bölüm = 3-4 sayfa, mekan değişimi)
3. DORUK NOKTASI (en heyecanlı an)
4. KAPANIŞ (değer + gurur + geri dönüş)

5. KURALLAR BLOĞU:
   ⚠️ YAZMAMA KURALLARI:
   ❌ YANLIŞ: "Ali Celsus Kütüphanesi'ni gördü. Sonra tiyatroya gitti."
   ✅ DOĞRU: "Ali kolon parçasının arkasına gizlendi. Kartal da..."
   
   ⚠️ TUTARLILIK KURALLARI:
   🦊 YARDIMCI KARAKTER: [companion] = [ANCHOR tanım]. TÜM SAYFALARDA AYNI.
   🗝️ ÖNEMLİ OBJE: [madalyon/harita] = [ANCHOR tanım]. TÜM SAYFALARDA AYNI.
   👗 KIYAFET: {clothing_description} tüm sayfalarda DEĞİŞMEZ.
   
   ⛔ İÇERİK YASAKLARI:
   - Anne, baba, aile üyesi YASAK (no_family senaryolarda)
   - Dini/siyasi referans YASAK
   - Gezi rehberi formatı YASAK
```

### Adım 1.5 — Companion SABİTLEME Kuralı

> [!IMPORTANT]
> **Kullanıcıya companion SEÇTİRME!** Her senaryonun TEK SABİT companion'ı olmalı.
> Companion senaryo tasarımında belirlenir ve tüm siparişlerde aynı kullanılır.
> Bu sayede:
> - Pipeline her zaman hangi companion'ı kilitleyeceğini bilir
> - CAST LOCK her sayfada aynı hayvanı/karakteri zorlar
> - `[object Object]` gibi frontend bug'ları oluşmaz
> - Görsel tutarlılık %100 garanti

#### Senaryo'da Companion Tanımlama

```
1. story_prompt_tr'de companion'ı SABİT yaz:
   "Yol arkadaşı: Cesur Yılkı Atı — küçük, kahverengi, uzun yeleli bir yılkı atı."

2. custom_inputs_schema'da type="hidden" kullan:
   [{"key": "animal_friend", "type": "hidden", "default": "Cesur Yılkı Atı"}]

3. _COMPANION_MAP sözlüğüne ekle (generate_book.py + _story_blueprint.py)

4. G2-a kartını doldur (ANCHOR tanım)
```

#### Placeholder Kuralı

> [!CAUTION]
> **`{animal_friend}` placeholder** otomatik replace edilir:
> 1. `custom_inputs_schema`'da `default` alanı DOLU olmalı 
> 2. `default` değer `_COMPANION_MAP` sözlüğünde tanımlı olmalı
> 3. Sözlükte yoksa generic fallback kullanılır (kötü tutarlılık!)

### Adım 1.6 — custom_inputs_schema Formatı

```json
[
  {
    "key": "animal_friend",
    "type": "hidden",
    "default": "Cesur Yılkı Atı"
  }
]
```

> [!WARNING]
> `type: "select"` KULLANMA — kullanıcıya seçim sunma.
> Companion senaryo tasarımcısı tarafından belirlenir, kullanıcıya bırakılmaz.
> Bu, görsel tutarlılık için kritik bir tasarım kararıdır.

---

## 🔍 MODÜL 2: MEVCUT SENARYO DENETLE (M2)

### Adım 2.1 — Senaryo Verilerini DB'den Çek

```powershell
python -c "
import asyncio, json
from dotenv import load_dotenv
load_dotenv(override=True)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

engine = create_async_engine(os.getenv('DATABASE_URL'))

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            \"\"\"SELECT theme_key, name, story_prompt_tr, scenario_bible,
                      custom_inputs_schema, outfit_girl, outfit_boy,
                      cover_prompt_template, page_prompt_template,
                      location_constraints, cultural_elements, flags
               FROM scenarios WHERE theme_key = '<THEME_KEY>'\"\"\"
        ))
        row = r.fetchone()
        if row:
            for i, col in enumerate(r.keys()):
                val = row[i]
                if isinstance(val, str) and len(val) > 300:
                    val = val[:300] + '...'
                print(f'{col}: {val}')
    await engine.dispose()

asyncio.run(check())
"
```

### Adım 2.2 — 10 Kriter Puanlama (80 üzerinden)

| # | Kriter | Max | Kontrol |
|---|--------|-----|---------|
| 1 | story_prompt_tr Uzunluğu | 10 | 400- = 0, 400-499 = 5, 500-699 = 7, 700+ = 10 |
| 2 | story_prompt_tr Kalitesi | 10 | Gezi rehberi yok (+3), YANLIŞ/DOĞRU var (+2), subliminal değer (+3), uyarı (+1), somut sahne (+1) |
| 3 | Kültürel Mekan | 10 | Min 10 mekan + hikayedeki rolleri |
| 4 | Yardımcı Karakter | 5 | Min 4 seçenek + lokasyon bağı + ANCHOR |
| 5 | Görsel Akış G3 | 10 | Kademe haritası + kamera açıları + sahne örnekleri |
| 6 | page_prompt_template | 10 | Custom + atmosfer + kamera çeşitlilik |
| 7 | G2 Tutarlılık Kartları | 10 | Companion anchor (+5), obje anchor (+3), yan rol (+2) |
| 8 | Kıyafet Sistemi | 5 | Detaylı + "EXACTLY same" + tema uyumu |
| 9 | Eğitsel Değer | 5 | 4+ değer + subliminal entegrasyon |
| 10 | İçerik Güvenliği | 5 | Kısıtlamalar açık + yasaklı içerik yok |

**Minimum geçer: 60/80. Hedef: 70+/80.**

### Adım 2.3 — 12 Hikaye Kalitesi Metriği (DETAYLI)

| # | Analiz | Ağırlık | İdeal Aralık |
|---|--------|---------|------------|
| 1 | 🪝 Sayfa Sonu Hook'ları | %12 | %50+ sayfada hook |
| 2 | 💬 Diyalog Kalitesi | %10 | %30-50 sayfada diyalog |
| 3 | 🏃 Aksiyon/Pasiflik Dengesi | %10 | %40-80 aktif fiil |
| 4 | 📈 Duygusal Yay | %15 | Min 5 farklı duygu, korku→cesaret |
| 5 | 🎭 Subliminal Değer Aktarımı | %10 | Doğrudan öğüt YOK |
| 6 | 🔁 Tekrar Analizi | %8 | 3 altı tekrar kalıp |
| 7 | 📏 Sayfa Ritmi | %5 | 40-70 kelime/sayfa |
| 8 | 🔤 Kelime Çeşitliliği | %5 | TTR 0.35-0.55 |
| 9 | 🌊 Gerilim Artışı (Tension Curve) | %8 | Sakin→heyecanlı→doruk→çözüm |
| 10 | 🎬 Sahne Çeşitliliği | %7 | Min 4 farklı mekan/ortam |
| 11 | 🧒 Karakter Gelişimi (Arc) | %5 | Başlangıç zayıflık → son güç |
| 12 | 🎨 Duyusal Detay (Sensory) | %5 | 5 duyudan en az 3'ü |

**Eğlence Puanı: Ağırlıklı ortalama → X/10**

---

### 🪝 METRİK 1: SAYFA SONU HOOK'LARI (En Kritik!)

> [!IMPORTANT]
> Hook = Okuyucuyu bir sonraki sayfayı çevirmeye zorlayan cümle sonu.
> **İdeal:** Her sayfanın son cümlesi merak uyandırmalı. Hedef: %50+ sayfada.

#### 5 Hook Tipi ve Örnekleri

| Tip | Açıklama | Örnek |
|-----|----------|-------|
| **1. Soru Hook** | Direkt veya dolaylı soru ile bitiş | "Acaba bu ses nereden geliyordu?" |
| **2. Ani Olay (Cliffhanger)** | Beklenmedik olay tam kapanmadan kesilir | "Tam o sırada, duvardaki taş kayarak açıldı ve..." |
| **3. Tehdit/Gerilim** | Belirsizlik ve tehlike hissi | "Ama karanlık koridordan gelen ayak sesleri gittikçe yaklaşıyordu." |
| **4. Keşif İpucu** | Yeni bir sır ortaya çıkar | "Haritanın arkasında, daha önce fark etmediği küçük bir sembol parıldıyordu." |
| **5. Duygusal Merak** | Karakterin iç dünyasına dair merak | "Yüreğinde tuhaf bir sıcaklık hissetti — sanki bu yeri daha önce tanıyormuş gibi." |

#### Hook Tetikleyici Kelimeler (Türkçe)

```
"birden", "ansızın", "tam o sırada", "ama", "ancak", "fakat",
"bir anda", "derken", "o an", "tam o anda", "baktığında",
"dönünce", "merak", "acaba", "nasıl olur da", "kim",
"ne olacak", "bu kez", "henüz", "hâlâ"
```

#### Puanlama

```
%60+ sayfada hook  → 10/10 (Mükemmel)
%50-59 sayfada     → 8/10
%40-49 sayfada     → 6/10
%30-39 sayfada     → 4/10
%30 altı           → 2/10 (Ciddi sorun)
```

---

### 💬 METRİK 2: DİYALOG KALİTESİ

#### Miktar Kontrolü

```
Diyalog oranı hesaplama:
  Diyalog = tırnak ("), guillemet (« ») veya tire (—) ile başlayan konuşma satırları
  Oran = diyalog içeren sayfa sayısı / toplam sayfa sayısı

İdeal: %30-50
  %30 altı → monoton (çocuk sıkılır)
  %50 üstü → çok konuşma (aksiyon azalır)
  %70 üstü → tiyatro metni gibi
```

#### Kalite Kontrolü

```
□ Konuşmalar karaktere özgü mü? (Çocuk = meraklı, Companion = bilge/komik)
□ Diyalog hikayeyi ilerletiyor mu? (Bilgi veriyor VEYA duygusal bağ kuruyor)
□ Boş diyalog yok mu? ("Hadi gidelim!" "Tamam!" gibi anlamsız)
□ Konuşma çocuk diline uygun mu? (Kısa cümleler, basit kelimeler)
□ Monolog yok mu? (Tek karakter 3+ cümle arka arkaya konuşmasın)
```

---

### 🏃 METRİK 3: AKSİYON/PASİFLİK DENGESİ

#### Aktif Fiil Listesi (Yüksek Puanlı)

```
koştu, atladı, tırmandı, kaydı, bastı, çekti, döndürdü, fırlattı,
yakaladı, uzandı, kucakladı, salladı, eğildi, dokundu, açtı,
kırdı, bağırdı, fısıldadı, gülümsedi, kaçtı, uçtu, dalga dalga
yürüdü, adım attı, tutundu, sıçradı, yuvarlandı, derin nefes aldı
```

#### Pasif Fiil Listesi (Düşük Puanlı)

```
gördü, baktı, hissetti, düşündü, izledi, anladı, biliyordu,
merak etti, fark etti, hatırladı, uyandı (durağan), durdu,
bekledi, oturdu, sessizce dinledi
```

#### Puanlama

```
Aktif fiil oranı:
  %60-80 aktif → 10/10 (canlı, aksiyon dolu)
  %40-59 aktif → 7/10 (orta, kabul edilir)
  %30-39 aktif → 4/10 (çok pasif kahraman)
  %30 altı     → 2/10 (çocuk sıkılır, izleyen değil yapan kahraman lazım)
```

---

### 📈 METRİK 4: DUYGUSAL YAY (En yüksek ağırlık)

#### 8 Duygu Kategorisi + Anahtar Kelimeler

| Duygu | Türkçe Tetikleyiciler |
|-------|----------------------|
| 😮 Merak | merak, acaba, ne olacak, ilginç, tuhaf, sır, gizem |
| 😄 Heyecan | heyecan, kalbi hızla, gözleri parlayarak, coşku, harika |
| 😨 Korku/Endişe | korku, ürperdi, karanlık, titrek, endişe, tehlike, sessiz |
| 😢 Üzüntü | gözyaşı, üzgün, kırıldı, yalnız, özlem, ayrılık |
| 😊 Sevinç | sevinç, mutluluk, güldü, neşe, kahkaha, güneş gibi |
| 💪 Cesaret | cesaret, kararlı, gözlerinde ateş, dikildi, boyun eğmedi |
| 😲 Şaşkınlık | hayret, ağzı açık, inanamadı, beklenmedik, mucize |
| 🏆 Gurur | gurur, başardı, gögüs kabartan, alkış, hayranlık |

#### İdeal Duygusal Yay Şeması

```
Sayfa 1-3:   😮 Merak + 😄 Heyecan       (Giriş — dünyayı keşfetme)
Sayfa 4-7:   😄 Heyecan + 😮 Merak        (Yükselen aksiyon)
Sayfa 8-10:  😨 Korku/Endişe               (Kriz — en karanlık an)
Sayfa 11-13: 💪 Cesaret + 😲 Şaşkınlık    (Dönüm noktası — karar anı)
Sayfa 14-16: 😊 Sevinç + 😲 Şaşkınlık     (Çözüm)
Sayfa 17-18: 🏆 Gurur + 😊 Sevinç         (Kapanış — büyüme)
```

#### Puanlama

```
6+ farklı duygu + korku→cesaret geçişi    → 10/10
5 farklı duygu + dramatik geçiş            → 8/10
4 farklı duygu                              → 6/10
3 farklı duygu                              → 4/10
2 veya daha az                              → 2/10
```

---

### 🎭 METRİK 5: SUBLİMİNAL DEĞER AKTARIMI (KRİTİK!)

> [!CAUTION]
> Pipeline'ın PAGE_GENERATION_SYSTEM_PROMPT'unda bu kural var:
> "Çocuğa özgüven, cesaret, empati gibi değerleri ASLA doğrudan öğüt vererek anlatma.
> Mesajları YALNIZCA karakterin cesur eylemleri, metaforlar ve hikayenin doğal akışı
> üzerinden, dolaylı (subliminal) bir dille hissettir."

#### YASAK Kalıplar (Doğrudan Öğüt)

```
❌ "Ali cesaretin ne kadar önemli olduğunu anlamıştı."
❌ "Böylece paylaşmanın güzelliğini öğrendi."
❌ "Cesaret göstermek gerektiğini biliyordu artık."
❌ "Farklılıklara saygı göstermek lazımdı."
❌ "Bu macera ona çok şey öğretmişti."
❌ "...olduğunu anladı", "...olduğunu öğrendi", "...olduğunu kavradı"
```

#### DOĞRU Kalıplar (Subliminal Aktarım)

```
✅ "Ali derin bir nefes aldı ve karanlık koridora ilk adımını attı." (cesaret → EYLEM ile)
✅ "Küçük tilki tökezleyince, Ali onu kucağına alıp sırtını okşadı." (empati → EYLEM ile)
✅ "Madalyonun ışığı, Ali'nin gülümsediği anda daha parlak yandı." (METAFOR ile)
✅ "Kanatlarını açtığında, rüzgar onu gökyüzüne taşıdı." (özgüven → METAFOR ile)
```

#### Puanlama

```
0 doğrudan öğüt + 3+ subliminal sahne  → 10/10
0 doğrudan öğüt + 1-2 subliminal sahne → 8/10
1 doğrudan öğüt                         → 5/10
2+ doğrudan öğüt                        → 2/10 (KRİTİK SORUN)
```

---

### 🔁 METRİK 6: TEKRAR ANALİZİ

```
Kontroller:
□ 4-6 kelimelik n-gram kalıplarını say
□ Benzer açılış cümlelerini tespit et ("Bir anda...", "O sırada...")
□ Aynı fiil art arda kullanılıyor mu? ("baktı... baktı... baktı")
□ Companion tanımı her sayfada tekrar ediliyor mu? (Bu DOĞRU — anchor)
□ Mekan tanımı gereksiz tekrar ediyor mu?

3+ özgün tekrar kalıp → puan düşer
Anchor tekrarları → puan düşürmez (kasıtlı tutarlılık)
```

---

### 🌊 METRİK 9: GERİLİM ARTIŞI (Tension Curve)

```
Her sayfaya 1-10 gerilim puanı ver:

İdeal eğri (22 sayfalık kitap):
  S1-S3:   2-3 (sakin giriş, dünya kurulumu)
  S4-S7:   4-6 (yükselen gerilim, ilk engeller)
  S8-S10:  7-8 (kriz derinleşir)
  S11-S13: 9-10 (DORUK — en heyecanlı anlar)
  S14-S16: 6-7 (çözüme doğru)
  S17-S18: 3-4 (huzurlu kapanış)

Kötü eğri örnekleri:
  ❌ Düz çizgi: her sayfa aynı seviye → monoton
  ❌ Dalgalı: sürekli iniş-çıkış → tutarsız
  ❌ Erken doruk: sayfa 3-4'te doruk → geri kalan boş
  ❌ Geç doruk: sayfa 16'da doruk → çözüm için yeterli yer yok
```

---

### 🎬 METRİK 10: SAHNE ÇEŞİTLİLİĞİ

```
Kontroller:
□ En az 4 farklı mekan/ortam var mı?
□ İç mekan ↔ Dış mekan geçişleri var mı?
□ Gündüz ↔ Alacakaranlık/Gece geçişi var mı?
□ Kamera açıları değişiyor mu? (yakın ↔ geniş ↔ kuşbakışı)
□ Hava/atmosfer değişiyor mu? (güneşli ↔ sisli ↔ yağmurlu)

5+ farklı ortam/atmosfer değişimi → 10/10
4 farklı ortam                   → 8/10
3 farklı ortam                   → 6/10
2 veya daha az                   → 3/10
```

---

### 🧒 METRİK 11: KARAKTER GELİŞİMİ (Character Arc)

```
Çocuğun başlangıç durumu (zayıflık/eksiklik):
  Örn: çekingen, korkak, yalnız, güvensiz, merak eksikliği

Kapanış durumu (kazanılan güç):
  Örn: cesur, özgüvenli, arkadaş canlısı, lider, keşifçi

Dönüşüm ARC'ı:
  S1-S3:  Zayıflık açıkça hissedilir (ama söylenmez!)
  S8-S10: Zayıflık nedeniyle bir kriz yaşar
  S11-13: Zayıflığıyla yüzleşir ve AŞAR
  S16-18: Artık farklı bir çocuk — ama farkında bile değil (subliminal!)

Dönüşüm belirgin + subliminal → 10/10
Dönüşüm var ama doğrudan söyleniyor → 5/10
Dönüşüm yok → 2/10
```

---

### 🎨 METRİK 12: DUYUSAL DETAY (Sensory Details)

```
5 Duyu ve Örnekleri:

👁️ Görme: renkler, ışık, parıltı, gölge, şekiller
  "Altın renkli ışık taş duvarlara yansıyordu"

👂 İşitme: sesler, müzik, fısıltı, patlama, rüzgar
  "Eski kapı gıcırdayarak açıldı"

👃 Koklama: çiçek, toprak, yemek, duman, deniz
  "Hava baharatlı ve sıcak kokuyordu"

✋ Dokunma: doku, sıcaklık, sertlik, yumuşaklık
  "Soğuk taş duvarı avuçlarıyla hissetti"

👅 Tat: (nadiren, ama etkili)
  "Rüzgar tuzlu deniz tadı taşıyordu"

En az 3 duyu kullanılmış → 10/10
2 duyu (sadece görme + işitme) → 6/10
Sadece görme → 3/10
```

---

## 📖 MÜKEMMEL HİKAYE ALTIN KURALLARI

> [!TIP]
> Bu kurallar, 10/10 eğlence puanı alacak bir hikayenin taşıması gereken özellikleri tanımlar.

### 1. İlk Sayfa = Kanca (Opening Hook)

İlk cümle merak uyandırmalı. Tanıtım değil, OLAY!

```
❌ "Ali 7 yaşında bir çocuktu. Bir gün Kapadokya'ya gitti."
✅ "Ali'nin ayağının altındaki toprak birden titredi — peri bacası açılıyordu!"
```

### 2. Show, Don't Tell (Göster, Söyleme)

```
❌ "Ali çok korkmuştu."  (söyleme)
✅ "Ali'nin elleri titriyordu. Yutkundu."  (gösterme)

❌ "Mağara çok güzeldi."  (söyleme)
✅ "Tavandaki kristaller yıldız gibi parlıyordu."  (gösterme)
```

### 3. Her Sayfada MİKRO-ENGEL

Çocuk her sayfada küçük bir zorlukla karşılaşmalı:

```
✅ Bir kapı kilitli → anahtar bul
✅ Köprü yıkık → başka yol bul  
✅ Companion kayboldu → ara
✅ Bulmaca/bilmece → çöz
✅ Yanlış yol → geri dön ve ipucu oku
```

### 4. Companion = Komik Anlar

Yardımcı karakter ciddi maceraya komedi dengesini sağlar:

```
✅ Tilki bir şeye takılıp yuvarlanır → çocuk güler
✅ Kartal yanlış yöne uçar → çocuk düzeltir
✅ Companion çocuktan önce korkar → çocuk cesaret gösterir
```

### 5. Doruk Noktası = Çocuk TEK BAŞINA Çözer

En kritik anda companion YARDIM EDEMEMELİ:

```
✅ Companion yaralı/sıkışmış → çocuk kendi cesaretiyle çözer
✅ Companion uzakta → çocuk kendi aklıyla bulmaca çözer
❌ Companion her şeyi çocuk için yapar → kahraman çocuk değil companion olur
```

### 6. Son Sayfa = Sıcak Kapanış

Macera biter ama DÜNYA devam eder hissi:

```
✅ "Güneş batarken Ali gülümsedi. Madalyon cebinde sıcacık parlıyordu.
    Belki yarın başka bir kapı daha açılırdı..."
❌ "Ali eve döndü. Çok güzel bir gün geçirmişti. Son."
```

### 7. Gezi Rehberi DEĞİL, Macera!

```
❌ YANLIŞ (Gezi rehberi formatı):
  "Ali Celsus Kütüphanesi'ni gördü. Bu kütüphane M.S. 135 yılında
   yapılmıştır. Sonra tiyatroya gitti. Tiyatro 25.000 kişi alıyordu."

✅ DOĞRU (Macera formatı):
  "Ali'nin ayağı bir taşa takıldı — ama bu sıradan bir taş değildi.
   Üzerinde tanıdık semboller vardı. Kütüphanenin gizli odasına giden
   yolun haritasıydı bu!"
```

---

## 🛡️ MODÜL 3: TUTARLILIK TESTİ (M3)

> Bu modül M2'de YOKTU — tamamen yeni.

Bu modül, pipeline kodundaki tutarlılık mekanizmalarının senaryo tarafında
doğru beslenip beslenmediğini kontrol eder.

### 3.1 — Placeholder Kontrolü

```python
# story_prompt_tr'de çözülmemiş placeholder var mı?
KONTROL_PLACEHOLDER = [
    "{animal_friend}", "{animal_friend_en}", "{companion}",
    "{guide}", "{rehber}", "{child_name}", "{clothing_description}"
]
```

- `{child_name}` ve `{clothing_description}` → pipeline tarafından otomatik replace edilir ✅
- `{animal_friend}` → `_resolve_companion_placeholder()` tarafından replace edilir ✅
  - **AMA** yeni companion adı `_TR_TO_EN` sözlüğünde yoksa generic fallback kullanılır ⚠️
- `{guide}`, `{rehber}` → pipeline'da replace MEKANİZMASI YOK ❌

### 3.2 — Companion CAST LOCK Kontrolü

Pipeline'da companion'ın düzgün çalışması için 4 koşul:

| # | Koşul | Kontrol Yeri |
|---|-------|-------------|
| 1 | `custom_inputs_schema`'da `animal_friend` key'i var | DB → scenarios tablosu |
| 2 | `default` alanı dolu | DB → custom_inputs_schema[0].default |
| 3 | `options` formatı doğru (dict, `[object Object]` yok) | DB → custom_inputs_schema[0].options |
| 4 | Default değer `_COMPANION_MAP` sözlüğünde var | Kod → `generate_book.py` + `_story_blueprint.py` |

Koşul 4 sağlanmazsa → companion oluşturulur ama generic görünüm kullanılır.

### 3.3 — Kıyafet Zinciri Kontrolü

3 katmanlı kıyafet önceliği doğru çalışıyor mu?

```
1. ✅ outfit_girl/outfit_boy dolu mu?
2. ✅ "EXACTLY same outfit on every page" yazıyor mu?
3. ✅ İngilizce mi? (Türkçe kıyafet → Flux AI anlayamaz)
4. ✅ Senaryo temasıyla uyumlu mu? (uzay = astronot, deniz = dalış)
```

### 3.4 — Obje Tutarlılık Kontrolü

story_prompt_tr'de tekrarlayan önemli objeler var mı?

```
Obje örnekleri: madalyon, harita, anahtar, taş, fener, pusula, kitap
Kontrol: Bu objeler G2-b kartında tanımlı mı?
         Prompt'a anchor cümlesi ekleniyor mu?
```

### 3.5 — Saç Tutarlılığı Kontrolü

```
1. ✅ PuLID referans fotoğrafı kullanılıyorsa → otomatik (face analyzer)
2. ⚠️ Fotoğraf yoksa → hair_description fallback kullanılır
3. ⚠️ hair_description boşsa → get_default_hair() çağrılır
4. ❌ AI hikaye yazarken saç rengi uyduruyor mu? → PAGE_GENERATION_SYSTEM_PROMPT kontrolü
```

---

## 🧪 MODÜL 4: PİPELINE SİMÜLASYONU (M4)

### Adım 4.1 — Dry-Run Çalıştır

```powershell
# Cloud SQL Proxy gerekli (port 5433)
python scripts/scenario_dry_run.py --theme_key <THEME_KEY> --child_name "Yusuf" --child_age 7 --child_gender erkek
```

Bu şunları yapar:
1. DB'den senaryoyu çeker
2. PASS-0 Blueprint Architect çalıştırır (~30sn)
3. PASS-1 Story Writer + Art Director çalıştırır (~60sn)
4. Teknik denetim uygular
5. Hikaye kalitesi analizi yapar
6. Eğlence Puanı hesaplar
7. JSON'a kaydeder: `tmp/dry_run/<theme>_dry_run.json`

### Adım 4.2 — Pipeline Çıktı Analizi

Dry-run çıktısında şunları kontrol et:

#### Teknik Denetim (5 Kontrol)

| # | Kontrol | Nasıl |
|---|---------|-------|
| 1 | Companion Tutarlılığı | Her sayfanın `image_prompt_en`'inde aynı companion tanımı var mı? |
| 2 | Kıyafet Kilidi | Outfit anchor tüm sayfalarda birebir aynı mı? |
| 3 | İçerik Güvenliği | Yasaklı kelime, ten/saç rengi uydurma var mı? |
| 4 | Sayfa Tamamlılığı | Beklenen sayfa sayısı = üretilen sayfa sayısı? |
| 5 | Metin-Görsel Uyumu | text_tr'deki öğeler image_prompt_en'de var mı? |

#### Hikaye Kalitesi Analizi (12 Metrik)

M2'deki 12 metriğin TAMAMINI gerçek AI çıktısı üzerinden uygula:

1. 🪝 Hook'lar → Her sayfanın son cümlesini kontrol et (5 hook tipi)
2. 💬 Diyalog → Gerçek konuşma oranını say
3. 🏃 Aksiyon → Aktif vs pasif fiilleri say
4. 📈 Duygusal Yay → Her sayfaya duygu atama, geçişleri çiz
5. 🎭 Subliminal → Doğrudan öğüt cümlelerini tespit et
6. 🔁 Tekrar → N-gram kalıplarını say
7. 📏 Ritim → Kelime sayısı min/max/ortalama/stddev
8. 🔤 Kelime çeşitliliği → TTR hesapla
9. 🌊 Gerilim eğrisi → Sayfa başına 1-10 puan ata
10. 🎬 Sahne çeşitliliği → Farklı mekan sayısı
11. 🧒 Karakter arc → Başlangıç zayıflık → kapanış güç
12. 🎨 Duyusal detay → 5 duyudan kaçı kullanılmış

### Adım 4.3 — Rapor Oluştur

```markdown
# 🎯 [Senaryo Adı] — Master Analiz Raporu

## 📊 PUAN TABLOSU
| Kategori | Puan |
|----------|------|
| Senaryo Kalitesi (M2) | XX/80 |
| Tutarlılık Testi (M3) | X/7 kontrol |
| Eğlence Puanı (M2+M4) | X.X/10 |

## 🛡️ TUTARLILIK DURUMU
| Öğe | Durum |
|-----|-------|
| Kıyafet kilidi | ✅/❌ |
| Companion CAST LOCK | ✅/❌ |
| Obje anchor | ✅/❌ |
| Placeholder çözümleme | ✅/❌ |
| Saç tutarlılığı | ✅/❌ |
| Mekan sürekliliği | ✅/❌ |
| İçerik güvenliği | ✅/❌ |

## 📈 DUYGUSAL YAY
S1:merak → S5:heyecan → S11:korku → S12:cesaret → S18:gurur

## 🛠️ İYİLEŞTİRME ÖNERİLERİ (öncelik sırasıyla)
### 🔴 KRİTİK
1. ...

### 🟡 ÖNEMLİ
1. ...

### 🟢 İYİ OLUR
1. ...
```

---

## 🔗 PİPELINE MİMARİSİ (Referans)

### V3 Blueprint Pipeline Akışı

```
Kullanıcı senaryo seçer
  ↓
PASS-0: Blueprint Architect
  ├── story_prompt_tr + scenario_bible → Gemini
  ├── {animal_friend} placeholder → _resolve_companion_placeholder()
  └── Çıktı: Blueprint JSON (page roles, side_character, child_outfit)
  ↓
PASS-1: Story Writer + Art Director
  ├── Blueprint → Gemini (text_tr + image_prompt_en + negative_prompt_en)
  └── Çıktı: Pages JSON
  ↓
Enhancement: CharacterBible + VisualPromptBuilder
  ├── build_character_bible() → companion + outfit + hair lock
  ├── enhance_all_pages() → stil inject + likeness hint
  └── CAST LOCK inject → page_builder.py
  ↓
Validation:
  ├── StoryValidators → sayfa sayısı, güvenlik, aile yasağı
  ├── VisualPromptValidator → shot conflict, stil uyumu
  └── QA checks → location contamination, text instructions
  ↓
Image Generation:
  ├── BookContext.build() → companion_name, companion_species, companion_appearance
  ├── build_page_prompt() → CAST LOCK (1 çocuk + 1 companion)
  └── generate_consistent_image() → PuLID face + prompt
```

### 7 Katmanlı Prompt Birleştirme

```
1. TEMPLATE  → Yaş, cinsiyet, kıyafet, saç, sahne tanımı
2. STYLE     → "2D hand-painted storybook" anchor
3. LIKENESS  → PuLID face lock directive
4. CHARACTER → Face analyzer text description
5. CAST LOCK → "EXACTLY 2 characters: child + companion"
6. COMPOSE   → "Wide shot, %25-30 çocuk, %70-75 ortam"
7. STYLE BLK → Son rendering stili pekiştirmesi
```

### Kıyafet Öncelik Zinciri

```
1. Senaryo outfit_girl/outfit_boy  (en yüksek)
2. Blueprint child_outfit.description_en
3. Cinsiyet varsayılanı (fallback)
```

### Companion Çözümleme Zinciri

```
story_prompt_tr → {animal_friend} placeholder
  ↓ _resolve_companion_placeholder()
custom_inputs_schema → default value ("Cesur Yılkı Atı")
  ↓ _TR_TO_EN mapping
İngilizce tür ("wild horse") → blueprint'e gider
  ↓
Blueprint → side_character {name, type, appearance}
  ↓ _extract_companion_from_pages() / CharacterBible
BookContext → companion_name, companion_species, companion_appearance
  ↓
page_builder.py → CAST LOCK prompt'a enjekte edilir
```

---

## 🚫 KESİN KURALLAR

### İçerik Yasakları
1. Dini ritüel/ibadet (Umre özel izinli)
2. Siyasi mesaj, güncel çatışma
3. Korku/şiddet ağırlıklı sahneler
4. Mini etek, kısa şort, karın açık
5. `image_prompt_en`'e ten/saç/göz rengi YAZMA (PuLID halleder)
6. Gezi rehberi formatı ("...gördü. Sonra ...gitti." YASAK)
7. Değeri doğrudan öğüt vererek anlatma
8. `no_family: true` → anne/baba/kardeş kesinlikle yasak

### Teknik Yasaklar
1. `story_prompt_tr` < 400 kelime → geçersiz
2. `theme_key` mevcut key ile çakışma → geçersiz
3. `outfit_girl/boy` Türkçe → Flux anlayamaz
4. `custom_inputs_schema` ile kullanıcıya companion SEÇTİRME → `type: "hidden"` kullan
5. Yeni companion → `_COMPANION_MAP` sözlüğü güncellenmeli
6. `scenario_bible` boş → companion tutarlılığı düşer

### Görsel Tutarlılık Yasakları
1. Companion rengi/görünümü sayfa sayfa değişemez
2. Companion kullanıcıya bırakılamaz — senaryo tasarımında SABİTLENİR
3. Önemli objeler görünüş değiştiremez
4. Kahraman kıyafeti tek sayfada bile değişemez
5. Her sayfaya aynı landmark fotoğrafı çizdirme

---

## 📁 DOSYA YAPISI

```
.agent/skills/scenario-master/
├── SKILL.md                    ← Bu dosya (Master giriş noktası)
└── templates/
    ├── master_report.md        ← Tam rapor şablonu
    ├── consistency_checklist.md ← 7 katmanlı tutarlılık kontrol listesi
    └── companion_registry.md   ← Tüm bilinen companion'ların kayıt defteri
```

---

## 📁 İLGİLİ KOD DOSYALARI

| Dosya | Ne İşe Yarar |
|-------|-------------|
| `app/services/ai/_story_blueprint.py` | PASS-0 + `_resolve_companion_placeholder()` |
| `app/services/ai/_story_writer.py` | V3 pipeline orchestration + CharacterBible build |
| `app/tasks/generate_book.py` | Final kitap üretimi + `_extract_companion_from_pages()` |
| `app/prompt/page_builder.py` | CAST LOCK + companion/outfit/hair enjeksiyonu |
| `app/prompt/book_context.py` | BookContext dataclass (companion_name/species/appearance) |
| `app/prompt_engine/__init__.py` | CharacterBible, CompanionSpec, PAGE_GENERATION_SYSTEM_PROMPT |
| `app/services/trial_generation_service.py` | Trial preview + CharacterBible companion |
| `app/models/scenario.py` | DB model (tüm senaryo alanları) |

---

## 🔄 TAM AKIŞ ÖZETİ

```
MODÜL SEÇİMİ
  ├── M1: Yeni Oluştur → 13 bölüm doldur → G2 kartları → kalite kontrol → migration
  ├── M2: Denetle → DB'den veri çek → 10 kriter puanla → 7 metrik analiz → rapor
  ├── M3: Tutarlılık → placeholder + CAST LOCK + kıyafet + obje + saç + güvenlik
  └── M4: Pipeline Sim → dry-run script → gerçek AI çıktı → teknik + hikaye analiz

SON ÇIKTI: Master Analiz Raporu (artifact)
  ├── Senaryo Kalitesi: XX/80
  ├── Tutarlılık: X/7
  ├── Eğlence Puanı: X.X/10
  └── İyileştirme Önerileri (öncelikli)
```
