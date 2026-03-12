"""Blueprint task prompt builder.

PASS-0'da hikaye yapısını oluşturur. Senaryo'nun story_prompt_tr'sini
dikkate alarak detaylı, heyecanlı, örgülü bir blueprint üretir.
"""

BLUEPRINT_SYSTEM_PROMPT = """Sen ödüllü bir çocuk kitabı mimarı ve hikaye tasarımcısısın.

Görevin: Çocukların HEYECANLANIP, MERAK EDİP, ENDİŞELENİP, BAŞARDIĞI bir hikaye BLUEPRİNT'i oluşturmak.

## BLUEPRINT PRENSİPLERİ

### 1. HEYECAN ÖRGÜSÜ (Emotional Arc)
Her hikayede:
- GİRİŞ: Tanışma, keşfe başlama (heyecan)
- GELİŞME: Keşif, küçük zorluklar (merak + küçük endişeler)
- KRİZ: Bir engel/korku (endişe artıyor, çocuk tereddütte)
- DORUK: En büyük meydan okuma (epik moment)
- ÇÖZÜM: Cesaretle başarma (zafer, tatmin)
- KAPANIŞ: Kazanımlarla dönüş (mutlu, değişmiş)

### 2. KURGU/ÖRGÜ (Story Structure)
- Sayfalalar arası BAĞLANTI: Her sayfa bir öncekine atar
- PROGRESSION: Kademeli ilerme (örn: sığdan derine, gezegende gezegene)
- FORESHADOWING: İpucu ver (örn: "uzaktan garip ses", sonra dev canlı çıkar)
- PAY-OFF: Kurulan tuzakların meyve vermesi

### 3. ÇOCUK PSİKOLOJİSİ
- Çocuk HİSSETMELİ: "Kalbim hızlı atıyor", "Nefesimi tuttum"
- ENDİŞE: "Korkmalı mıyım?", "Ya..."
- KEŞİF: "Vay canına!", "İnanmıyorum!"
- ZAFER: "Başardım!", "Ben yapabilirim!"

### 4. DEĞER AKTARIMI (Subliminal)
Değeri ASLA direkt söyleme:
- ❌ "Cesur olmalısın"
- ✅ Çocuk korkuyor ama yine de adım atıyor → EYLEM

### 5. EPİK MOMENTLER
Her hikayede 5-7 epic moment olmalı:
- Görsel zenginlik (dev canlı, muhteşem manzara)
- Duygusal doruk (dokunma anı, binme, keşif)
- Scale vurgusu (çocuk küçük, dünya devasa)

## ÇIKTI FORMATI

```json
{
  "title": "Hikaye başlığı",
  "pages": [
    {
      "page": 1,
      "role": "opening" | "exploration" | "crisis" | "climax" | "resolution" | "conclusion",
      "scene_goal": "Sahnede ne olacak (kısa)",
      "emotion": "curiosity" | "wonder" | "worry" | "awe" | "fear" | "joy" | "triumph",
      "location_detail": "Konum detayı",
      "cultural_hook": "Kültürel element (varsa)",
      "magic_item": "Sihirli eşya (varsa)",
      "companion_action": "Yardımcı karakter ne yapıyor"
    }
  ]
}
```

Her sayfa blueprint'i hikayenin AKIŞINI göstermeli."""


def build_blueprint_task_prompt(
    *,
    child_name: str,
    child_age: int,
    child_description: str,
    location_key: str,
    location_display_name: str,
    visual_style: str,
    magic_items: list[str],
    page_count: int,
    bible: dict | None = None,
    book_title: str = "",
    story_structure: str = "",  # YENİ! story_prompt_tr buradan gelir
) -> str:
    """Blueprint task prompt oluşturur.
    
    Args:
        story_structure: Senaryo'nun story_prompt_tr içeriği (hikaye yapısı, zone progression, epic moments)
    """
    
    bible_str = ""
    if bible and isinstance(bible, dict):
        import json as _json
        try:
            bible_str = _json.dumps(bible, ensure_ascii=False, indent=2)
        except Exception:
            bible_str = str(bible)
    
    magic_str = ""
    if magic_items:
        magic_str = f"\nSihirli eşyalar: {', '.join(magic_items)}"
    
    # KRITIK: Senaryo yapısı varsa blueprint'e dahil et
    structure_hint = ""
    if story_structure and len(story_structure) > 100:
        # İlk 4000 karakteri kullan (uzun senaryolarda kritik bilgi kaybolmasın)
        structure_preview = story_structure[:4000]
        structure_hint = f"""
🎭 SENARYO YAPISINI DİKKATE AL:
Bu senaryo özel bir hikaye yapısına sahip. Aşağıdaki yapıyı blueprint'e UYARLA:

{structure_preview}

ÖNEMLİ: Bu yapıyı aynen kopyalama! Bunun YERİNE:
- Açılış-gelişme-kapanış yapısını koru
- Önemli olayları (epic moments) blueprint'te işaretle
- Progression'ı (örn: zone-by-zone, planet-by-planet) sayfa rollerine yansıt
- Endişe-çözüm döngülerini emotion field'ında belirt
"""
    
    return f"""## GÖREV: Hikaye Blueprint'i Oluştur

### Çocuk Bilgileri
- İsim: {child_name}
- Yaş: {child_age}
- Görünüm: {child_description if child_description else "Doğal çocuk"}
- Konum: {location_display_name}{magic_str}

### Görsel Stil
{visual_style}
{structure_hint}

### Scenario Bible (Referans)
{bible_str if bible_str else "Yok"}

## BLUEPRINT GEREKSİNİMLERİ

### Heyecan Grafiği Tasarla:
```
       ┌── DORUK (climax)
      /│\\
     / │ \\
    /  │  \\__ Resolution
   /   │
  /    │  Crisis (endişe artıyor)
 /     │
START   │                    END
        Epic moments 5-7 tane
```

### Sayfa Rolleri:
- opening (2-3 sayfa): Tanışma, keşfe başlama
- exploration (5-8 sayfa): Keşif, küçük heyecanlar
- crisis (2-3 sayfa): Zorluk, endişe artıyor
- climax (2-3 sayfa): En epic moment, doruk
- resolution (2-3 sayfa): Başarı, zafer
- conclusion (2-3 sayfa): Dönüş, kapanış

### Her Sayfa İçin:
- **scene_goal**: Sahnede ne olacak (action-oriented)
- **emotion**: Çocuğun hissi (curiosity/wonder/worry/awe/triumph)
- **location_detail**: Konum özelliği (zone/alan detayı)
- **cultural_hook**: Kültürel/bilimsel element (varsa)
- **magic_item**: Sihirli eşya kullanımı (varsa)
- **companion_action**: Yardımcı karakter durumu

### Zorunlu Ek Alanlar:
- **child_outfit**: {{ "description_en": "outfit worn throughout the story (English)", "hair_style_en": "hairstyle in English" }}
- **side_character**: {{ "name": "companion name", "type": "species (owl, cat, dragon)", "appearance": "color, size, distinctive features — SAME on every page" }}

### ZORUNLU KURALLAR:
1. TAM OLARAK {page_count} sayfa blueprint üret
2. Endişe-başarı döngüsü OLMALI (sayfa 8-12 arası endişe, sonra çözüm)
3. Epic moment en az 5 tane işaretle
4. Progression mantıklı olsun (kademeli ilerleme)
5. side_character alanında companion'ın appearance bilgisini MUTLAKA yaz (renk, boyut, ayırt edici özellik)
6. child_outfit alanını MUTLAKA doldur (kıyafet + saç stili İngilizce)

## ÇIKTI:
JSON formatında {page_count} sayfalık blueprint."""
