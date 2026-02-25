# OKYANUS SENARYOSU - PILOT UYGULAMA PLANI
## Değer Mesajları + Heyecanlı Örgü Odaklı

## 1. DEĞER ANALİZİ

### Mevcut Değerler (story_prompt_tr'den):
```
💎 ANA DEĞER: MERAK + DOĞA SEVGİSİ
- Okyanusları keşfetme isteği
- Deniz yaşamını koruma bilinci
- Devasa canlılara saygı
- Bilimsel merak (okyanografi)
- Çevre sorumluluğu
```

### Ek Değer Katmanları (Hikayeye Doğal Entegre):
1. **CESARET**: Karanlık sulara inme cesareti
2. **DOSTLUK**: Yunus ve balinayla bağ kurma
3. **SABIR**: Dev canlının güvenini kazanmak için sabırlı olma
4. **SAYGI**: Farklı (dev) varlıklara saygı duyma
5. **BİLİMSEL DÜŞÜNME**: Gözlem yapma, merak etme, öğrenme

### Değer İletim Yöntemi (Subliminal):
- ❌ "Cesur olmalısın" (didaktik)
- ✅ Elif karanlığa inerken korkuyor ama devam ediyor (eylem)
- ❌ "Doğayı korumalıyız" (öğüt)
- ✅ Balina ile bağ kurduktan sonra "Seni her zaman koruyacağım" diyor (hissetme)

---

## 2. HEYECAN ÖRGÜSÜNÜ TASARIMI

### Hikaye Grafiği (Emotional Arc):
```
           ┌──── ZİRVE (Sayfa 15: Balina binme)
          /│\
         / │ \
        /  │  \_____ Keşif devam (hidrotermal)
       /   │
      /    │ Endişe artıyor (karanlık, yunus veda)
     /     │
    /      │ İlk heyecan (fosforlu canlılar)
   /       │
BAŞLANGIÇ  │                              BİTİŞ
(tanışma)  │                             (vedalaşma)
           13-15 (3 sayfa: Görünüş-Dokunma-Binme)
```

### Heyecan Momentleri (7 Epic Scene):
1. **Sayfa 4-5**: Mercan tüneli + yunus atlama gösterileri
2. **Sayfa 8**: İlk fosforlu denizanası (sihir gibi!)
3. **Sayfa 11**: Dev kalamar kolu görünür (endişe! ama yunus koruyor)
4. **Sayfa 13**: MAVİ BALİNA İLK GÖRÜNÜŞ (ŞOK - DEVASA!)
5. **Sayfa 14**: Dokunma anı (kalp atışları, bağ kurma)
6. **Sayfa 15**: Sırt yolculuğu (ZİRVE - epic!)
7. **Sayfa 18**: Fosforlu galaksi (binlerce ışık, büyü gibi)

### Endişe → Başarı Döngüleri:
| Sayfa | Endişe | Çözüm/Başarı |
|-------|--------|--------------|
| 7-8 | "Işık azalıyor, karanlık... korkuyor muyum?" | İlk fosforlu canlıyı görünce: "Karanlık değilmiş, sihirli!" |
| 11 | "Dev kalamar kolu! Tehlikeli mi?" | Yunus: "Merak etme, uzakta." + Güvenli geçiş |
| 12 | "Yunus gidiyor, yalnız kalacağım" | Balina çağrısı duyuluyor: "Daha büyük arkadaş geliyor!" |
| 13 | "DEVASA balina! Çok büyük, korkmalı mıyım?" | Balina şarkı söylüyor, nazik gözleri: "Dost!" |

---

## 3. MODULAR PROMPT TASARIMI

### COVER PROMPT (Mevcut: 976 → Yeni: 350 char)

**YENİ**:
```python
OCEAN_COVER_PROMPT = """Epic underwater adventure scene: {scene_description}. 
Dolphin companion swimming beside child (playful, friendly, guiding). 
MASSIVE blue whale in background (30 meters long, emphasize scale dramatically). 
Bioluminescent jellyfish and creatures glowing around. 
Vibrant coral reefs, deep ocean blue gradient (turquoise to indigo). 
Sunlight god rays from above. Peaceful, wondrous atmosphere."""
```

**Korunan**:
- ✅ Scale: "30 meters, emphasize dramatically"
- ✅ Yunus arkadaş
- ✅ Mavi balina
- ✅ Bioluminescence
- ✅ Ocean gradient

**Kaldırılan** (pipeline ekler):
- ❌ CLOTHING block → Pipeline'dan
- ❌ COMPOSITION → Pipeline'dan
- ❌ TITLE SPACE → Cover builder'dan

---

### PAGE PROMPT (Mevcut: 1565 → Yeni: 420 char)

**YENİ**:
```python
OCEAN_PAGE_PROMPT = """Underwater exploration scene: {scene_description}. 
Dolphin companion present in shallow-mid depths (playful guide, swimming beside child). 
Ocean zone atmosphere and creatures: [Epipelagic: vibrant coral gardens, tropical fish schools, clear turquoise / Mesopelagic: blue-purple gradient, glowing jellyfish, lanternfish / Bathypelagic: dark water, anglerfish with lure, bioluminescence only / Whale encounter: MASSIVE blue whale (30m, 200 tons), child TINY in comparison, gentle and peaceful, allowing child to ride / Abyssopelagic: complete darkness, hydrothermal vents, phosphorescent creatures like galaxy]. 
Match current page depth and creatures to scene context."""
```

**Korunan** (kritik detaylar):
- ✅ 5 derinlik zonu tanımları
- ✅ Zone-specific creatures
- ✅ Mavi balina scale (30m, 200 tons, TINY child)
- ✅ Yunus companion
- ✅ Bioluminescence detayları
- ✅ Hidrotermal bacalar

**Kaldırılan** (pipeline ekler):
- ❌ CLOTHING: {clothing_description} → outfit_girl/boy'dan
- ❌ COMPOSITION REQUIREMENTS → COMPOSITION_RULES'tan
- ❌ AVOID block → negative_builder'dan
- ❌ SAFETY RULES → BASE_NEGATIVE'de

---

## 4. STORY_PROMPT_TR İYİLEŞTİRMESİ

### Mevcut yapı zaten güçlü ama Blueprint için optimize edelim:

**Eklenecek** (Blueprint'e açık sinyaller):

```python
OCEAN_STORY_PROMPT_TR = """
[BAŞA EKLE]

🎯 BLUEPRINT YAPISI (22 sayfa):
BÖLÜM 1 - GİRİŞ (Sayfa 1-6):
- Sayfa 1-2: Tanışma (Epipelagic, yüzey)
- Sayfa 3-6: İlk keşif (Epipelagic, mercan tüneli, yunus oyunu)
  → Heyecan: Mercan tüneli, yunus atlama gösterileri

BÖLÜM 2 - DERİNLEŞME + ENDİŞE (Sayfa 7-12):
- Sayfa 7-10: Alacakaranlık (Mesopelagic)
  → Heyecan: İlk fosforlu denizanası (büyü gibi!)
  → Endişe: "Işık azalıyor, daha karanlık oluyor..."
- Sayfa 11-12: Gece bölgesi (Bathypelagic)
  → Endişe ARTYOR: Dev kalamar işaretleri, yunus veda
  → Geçiş: Uzaktan balina şarkısı duyuluyor

BÖLÜM 3 - DORUK/ZİRVE (Sayfa 13-15):
- Sayfa 13: İlk görünüş
  → ŞOK: "DEVASA! 30 metre! Gözü kafamdan büyük!"
  → Endişe: "Korkmalı mıyım?"
- Sayfa 14: Dokunma ve bağ
  → Rahatlama: "Nazik! Kalp atışları..."
  → Kabul: Balina çocuğu arkadaş olarak kabul eder
- Sayfa 15: Sırt yolculuğu
  → ZAFER: "En büyük canlıyla birlikte uçuyorum!"
  → Tatmin: Başarı hissi, rüya gibi

BÖLÜM 4 - DAHA DERİN KEŞİF (Sayfa 16-19):
- Sayfa 16-19: Abyss sırları (Abyssopelagic)
  → Heyecan: Hidrotermal bacalar, fosforlu galaksi
  → Keşif: Gizli hazine veya kristal mağara

BÖLÜM 5 - KAPANIŞ (Sayfa 20-22):
- Sayfa 20-21: Yüzeye dönüş
  → Vedalaşma: Balina, yunus, deniz kaplumbağası
- Sayfa 22: Gün batımı
  → Kapanış: "Devler bile nazik olabilir"

[Mevcut içerik devam eder...]
"""
```

---

## 5. UYGULAMA ADIMLARI

### Adım 1: Blueprint System'e story_prompt_tr Desteği
```python
# app/prompt_engine/blueprint_prompt.py veya ilgili modül

def build_blueprint_task_prompt(
    # ... mevcut parametreler
    story_structure: str = "",  # YENİ!
) -> str:
    # ...
    
    structure_hint = ""
    if story_structure:
        structure_hint = f"""
🎭 SENARYO YAPISINI KULLAN:
Bu senaryo özel bir hikaye yapısına sahip. Blueprint oluştururken 
aşağıdaki yapıyı DİKKATE AL:

{story_structure[:1500]}  # İlk 1500 char (blueprint için yeterli)
"""
    
    return f"""
{structure_hint}

## GÖREV: Hikaye Blueprint'i Oluştur
[... mevcut blueprint instructions]
"""
```

### Adım 2: gemini_service.py'de story_prompt_tr'yi geç
```python
# Satır ~2478
task_prompt = build_blueprint_task_prompt(
    # ... mevcut
    story_structure=getattr(scenario, "story_prompt_tr", ""),  # YENİ!
)
```

### Adım 3: Ocean Prompt'ları Güncelle
```python
# update_ocean_adventure_scenario.py

# Cover: 976 → 350 char
OCEAN_COVER_PROMPT = """..."""  # Yukarıdaki yeni versiyon

# Page: 1565 → 420 char  
OCEAN_PAGE_PROMPT = """..."""  # Yukarıdaki yeni versiyon

# Story: Mevcut + Blueprint yapısı eklentisi
OCEAN_STORY_PROMPT_TR = """
🎯 BLUEPRINT YAPISI (22 sayfa):
[Yukarıdaki detaylı yapı]

[Mevcut tüm içerik korunuyor]
"""
```

---

## 6. BEKLENİLEN İYİLEŞTİRMELER

### Hikaye Metni:
**ŞU AN**:
- Sayfa 13: "Elif bir balina gördü. Çok büyüktü."
- Sayfa 14: "Balina nazikti."
- Sayfa 15: "Elif balınaya bindi."

**YENİ** (Blueprint zone-aware):
- Sayfa 13: "Karanlıktan DEVASA bir gölge çıktı. Mavi balina! 30 metre uzunluğunda - gözü Elif'in kafasından büyüktü. Elif nefesini tuttu. 'Bu kadar büyük olabileceğine inanmıyorum!'"
- Sayfa 14: "Elif yavaşça yaklaştı. Balinanın derisine dokundu - yumuşacıktı! Kalp atışlarını su altında hissediyordu. Balina Elif'e baktı. Gözlerinde nezaket vardı."
- Sayfa 15: "Balina Elif'i sırtına aldı! Su altında uçuyormuş gibiydi. Dünyanın en büyük canlısı ile en küçük keşifçi birlikte yolculuk ediyordu."

### Görsel Zenginliği:
**ŞU AN**: "Child sees large whale"
**YENİ**: "MASSIVE blue whale (30m, 200 tons), child TINY, whale singing, bioluminescent creatures, dark bathypelagic zone"

---

## 7. ÖNCE-SONRA ÖZET

| Özellik | Şu An | Pilot Sonrası |
|---------|-------|---------------|
| **Blueprint** | Generic | Ocean zone-specific |
| **Mavi Balina** | 1 sayfa | 3 sayfa (buildup) |
| **Endişe** | ❌ Yok/az | ✅ Karanlık, kalamar, yalnızlık |
| **Zafer** | ⚠️ Sığ | ✅ Epic (balina binme) |
| **Zone Progression** | ❌ Yok | ✅ 5 zone, kademeli |
| **Epic Scale** | ❌ Yok | ✅ "30m, child TINY" |
| **Değer İletimi** | ✅ Var | ✅✅ Daha derin (cesaret+sabır+saygı) |
| **Görsel Prompt Kullanımı** | ❌ Default | ✅ Ocean-specific |

---

## 8. UYGULAMA SIRASI

1. ✅ **negative_builder.py**: face swap, pasted face, collage eklendi
2. ⏳ **blueprint_prompt**: story_prompt_tr desteği ekle
3. ⏳ **Ocean prompt'ları kısalt**: 350 + 420 char
4. ⏳ **story_prompt_tr'ye blueprint yapısı ekle**
5. ⏳ **update_ocean_adventure_scenario.py güncelle**
6. ⏳ **Migration + deploy**
7. ⏳ **Test**: Kitap üret, prompt loglarını kontrol et

---

## 9. BAŞLAYALIM!

Şimdi:
1. blueprint_prompt modülünü bulup story_structure desteği ekliyorum
2. Ocean prompt'larını modular hale getiriyorum
3. Deploy ediyoruz
4. Sen test ediyorsun

Onay verirsen başlıyorum! 🚀
