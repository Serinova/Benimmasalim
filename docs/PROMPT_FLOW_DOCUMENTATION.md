# 🎯 SINGLE SOURCE OF TRUTH - Prompt Akış Dokümantasyonu

## ✅ DOĞRULAMA DURUMU (Güncellenmiş)

| Kontrol | Durum | Açıklama |
|---------|-------|----------|
| 1. cover_prompt_template kullanılıyor mu? | ✅ | `_compose_visual_prompts()` içinde `scenario.get_cover_prompt()` çağrılıyor |
| 2. page_prompt_template kullanılıyor mu? | ✅ | `_compose_visual_prompts()` içinde `scenario.get_page_prompt()` çağrılıyor |
| 3. ai_prompt_template entegre mi? | ✅ | `_pass1_write_story()` içinde Gemini'ye gönderiliyor |
| 4. location_constraints enforce ediliyor mu? | ✅ | Hem Pass1 hem Pass2 hem compose'da kontrol edilip enjekte ediliyor |
| 5. cultural_elements kullanılıyor mu? | ✅ | Pass1 ve compose'da background hint olarak ekleniyor |
| 6. learning_outcomes dağıtılıyor mu? | ✅ | Pass1'de educational_prompt ile her sayfaya dağıtım talimatı veriliyor |
| 7. Style tek yerde ekleniyor mu? | ✅ | SADECE `_compose_visual_prompts()` içinde |
| 8. Fal.ai style ekliyor mu? | ✅ DÜZELTILDI | `fal_service.py` ve `fal_ai_service.py` style EKLEMİYOR |
| 9. JSON repair var mı? | ✅ | `_extract_and_repair_json()` metodu eklendi |
| 10. fixed_outfit var mı? | ✅ | Her prompt'a outfit enjekte ediliyor |
| 11. Cache invalidation? | ✅ | style_id + scenario_id + outcomes_hash dahil |

---

## 📊 YENİ AKIŞ DİYAGRAMI

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (create/page.tsx)                         │
│                                                                              │
│  scenario_id ────────────┐                                                  │
│  style_id ───────────────┼──► API Request                                   │
│  learning_outcomes[] ────┤                                                  │
│  childInfo ──────────────┘                                                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               BACKEND API (ai.py - /test-story-structured)                   │
│                                                                              │
│  1. Fetch Scenario from DB (WITH ALL TEMPLATE FIELDS!)                      │
│     - ai_prompt_template                                                    │
│     - cover_prompt_template                                                 │
│     - page_prompt_template                                                  │
│     - location_constraints                                                  │
│     - cultural_elements                                                     │
│                                                                              │
│  📝 LOG: "📋 SCENARIO TEMPLATES CHECK"                                      │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   GEMINI SERVICE - PASS 1: Pure Author                       │
│                                                                              │
│  INPUTS USED:                                                               │
│  ✅ scenario.ai_prompt_template → Gemini system prompt'a ekleniyor          │
│  ✅ scenario.location_constraints → Lokasyon gereksinimleri                 │
│  ✅ scenario.cultural_elements → Kültürel atmosfer                          │
│  ✅ learning_outcomes → educational_prompt olarak dağıtılıyor               │
│                                                                              │
│  OUTPUT: Beautiful story TEXT (Türkçe)                                       │
│                                                                              │
│  📝 LOG: "SCENARIO TEMPLATE: Using ai_prompt_template"                      │
│  📝 LOG: "SCENARIO TEMPLATE: Using location_constraints"                    │
│  📝 LOG: "SCENARIO TEMPLATE: Using cultural_elements"                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                GEMINI SERVICE - PASS 2: Technical Director                   │
│                                                                              │
│  INPUTS:                                                                    │
│  - story_text from Pass 1                                                   │
│  - location_constraints (enforced in prompt)                                │
│                                                                              │
│  OUTPUT: JSON with pages, each containing:                                  │
│    - text: Türkçe hikaye metni                                              │
│    - scene_description: İngilizce sahne tanimi (❌ NO STYLE!)               │
│                                                                              │
│  📝 JSON REPAIR: _extract_and_repair_json() handles malformed output        │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              GEMINI SERVICE - _compose_visual_prompts()                      │
│                                                                              │
│  ⭐ SINGLE SOURCE OF TRUTH: ALL TEMPLATES USED HERE! ⭐                      │
│                                                                              │
│  FOR COVER (page 0):                                                        │
│    IF scenario.cover_prompt_template EXISTS:                                │
│      visual_prompt = scenario.get_cover_prompt(                             │
│        book_title, scene_description, fixed_outfit, visual_style            │
│      )                                                                       │
│    ELSE:                                                                    │
│      visual_prompt = scene + outfit + cultural_hint + style                 │
│                                                                              │
│  FOR PAGES (1-N):                                                           │
│    IF scenario.page_prompt_template EXISTS:                                 │
│      visual_prompt = scenario.get_page_prompt(                              │
│        scene_description, fixed_outfit, visual_style                        │
│      )                                                                       │
│    ELSE:                                                                    │
│      visual_prompt = scene + outfit + cultural_hint + style                 │
│                                                                              │
│  ENFORCEMENTS:                                                              │
│  ✅ fixed_outfit injected to every page                                     │
│  ✅ location_constraints injected if missing                                │
│  ✅ cultural_elements added as background hint                              │
│  ✅ Style added ONCE (single source!)                                       │
│                                                                              │
│  📝 LOG: "📋 USING SCENARIO cover_prompt_template"                          │
│  📝 LOG: "📋 USING SCENARIO page_prompt_template"                           │
│  📝 LOG: "📍 INJECTED location_constraints"                                 │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FAL.AI SERVICE                                      │
│                                                                              │
│  ⚠️ NO STYLE ADDED HERE! ⚠️                                                 │
│                                                                              │
│  generate_cover():                                                          │
│    full_prompt = f"{prompt}. High quality, detailed."                       │
│    # NO style.prompt_modifier!                                              │
│                                                                              │
│  generate_page_image():                                                     │
│    # Uses prompt AS-IS, no modifications!                                   │
│                                                                              │
│  generate_image() / generate_with_pulid():                                  │
│    # Uses prompt AS-IS from Gemini (style already included)                 │
│                                                                              │
│  📝 LOG: "FAL GENERATE_COVER - Using prompt AS-IS (no extra style)"        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 DEĞİŞTİRİLEN DOSYALAR (DIFF ÖZETİ)

### 1. `backend/app/services/ai/gemini_service.py`

| Değişiklik | Açıklama |
|------------|----------|
| `_pass1_write_story()` | `ai_prompt_template`, `location_constraints`, `cultural_elements` parametreleri eklendi |
| `_pass1_write_story()` | Scenario template'leri Gemini prompt'una entegre edildi |
| `_pass2_format_story()` | `location_constraints` enforced |
| `_compose_visual_prompts()` | `scenario.get_cover_prompt()` ve `scenario.get_page_prompt()` kullanılıyor |
| `_compose_visual_prompts()` | `fixed_outfit` parametresi eklendi |
| `_compose_visual_prompts()` | `cultural_elements` background hint olarak eklendi |
| `_compose_visual_prompts()` | `location_constraints` eksikse enjekte ediliyor |
| `_extract_and_repair_json()` | YENİ - JSON parsing ve repair fonksiyonu |
| `generate_story_structured()` | Tüm scenario template alanları çekilip Pass1'e geçiriliyor |

### 2. `backend/app/services/ai/fal_service.py`

| Değişiklik | Açıklama |
|------------|----------|
| `generate_cover()` | `style.prompt_modifier` KALDIRILDI - çift style önlendi |
| `generate_cover_from_mm()` | `style.prompt_modifier` KALDIRILDI |
| `generate_page_image()` | "children's book illustration" ekleme KALDIRILDI |
| Tüm metodlar | Prompt AS-IS kullanılıyor, ekstra ekleme yok |

### 3. `backend/app/services/trial_service.py`

| Değişiklik | Açıklama |
|------------|----------|
| `_compute_outcomes_hash()` | YENİ - Learning outcomes hash'i hesaplıyor |
| `generated_prompts_cache` | `outcomes_hash` eklendi |

### 4. `backend/app/models/story_preview.py`

| Değişiklik | Açıklama |
|------------|----------|
| `generated_prompts_cache` | `outcomes_hash` formatı dokümante edildi |

---

## 📦 ÖRNEK: KAPADOKYA SENARYOSU (10 Sayfa)

### Senaryo Veritabanı Kayıtları

```json
{
  "id": "kapadokya-uuid",
  "name": "Kapadokya Macerası",
  "description": "Peri bacaları arasında büyülü bir yolculuk",
  "ai_prompt_template": "Hikaye Kapadokya'nın peri bacaları arasında geçmeli. Her sayfada en az bir peri bacası veya balon referansı olmalı. Kapadokya'nın mistik atmosferi hikayenin her anında hissedilmeli.",
  "location_constraints": "Cappadocia fairy chimneys, hot air balloons, rock formations, cave dwellings, Goreme valley",
  "cultural_elements": {
    "primary": ["fairy chimneys", "hot air balloons", "rock formations"],
    "colors": "warm earth tones, sunrise golden, sunset orange"
  },
  "cover_prompt_template": "A breathtaking children's book cover showing {scene_description}. The child is wearing {clothing_description}. Cappadocia fairy chimneys and colorful hot air balloons in the background. {visual_style}. Epic wide angle composition with space for title at top.",
  "page_prompt_template": "A children's book illustration showing {scene_description}. The child is wearing {clothing_description}. Background features Cappadocia's unique rock formations. {visual_style}. Soft background suitable for text overlay."
}
```

### API Request

```json
{
  "child_name": "Ali",
  "child_age": 6,
  "child_gender": "erkek",
  "scenario_id": "kapadokya-uuid",
  "visual_style": "Pixar Disney 3D animation style, warm cinematic lighting, vibrant colors",
  "page_count": 10,
  "learning_outcomes": ["Cesaret", "Merak"]
}
```

### Backend Debug Logları

```
📋 SCENARIO TEMPLATES CHECK
   scenario_name=Kapadokya Macerası
   has_ai_prompt_template=True
   has_location_constraints=True
   has_cultural_elements=True
   ai_prompt_preview=Hikaye Kapadokya'nın peri bacaları arasında geçmeli...

SCENARIO TEMPLATE: Using ai_prompt_template
   template_preview=Hikaye Kapadokya'nın peri bacaları arasında geçmeli...

SCENARIO TEMPLATE: Using location_constraints
   constraints=Cappadocia fairy chimneys, hot air balloons...

SCENARIO TEMPLATE: Using cultural_elements
   elements={'primary': ['fairy chimneys', 'hot air balloons'...]}

🎨 COMPOSE VISUAL PROMPTS - Template Check
   scenario_name=Kapadokya Macerası
   has_cover_template=True
   has_page_template=True
   fixed_outfit=adventure jacket and comfortable pants

📋 USING SCENARIO cover_prompt_template
   page=0

📋 USING SCENARIO page_prompt_template
   page=1
   page=2
   ...

🔍 FINAL PROMPT CHECK - Page 0
   prompt_length=425
   style_keywords_found={'pixar': 1, 'disney': 1}
   total_style_count=2
   contamination=✅ CLEAN

FAL GENERATE_COVER - Using prompt AS-IS (no extra style)
   prompt_preview=A breathtaking children's book cover showing a 6-year-old boy...
```

### Çıktı JSON (10 Sayfa)

```json
{
  "success": true,
  "generation_method": "TWO-PASS (Pure Author + Technical Director)",
  "story": {
    "title": "Ali'nin Kapadokya Macerası",
    "pages": [
      {
        "page_number": 0,
        "text": "Ali, Kapadokya'nın büyülü dünyasına adım atıyordu...",
        "scene_description": "A 6-year-old boy named Ali standing at the entrance of Goreme valley, looking up in wonder at hundreds of colorful hot air balloons rising into the golden sunrise sky. Massive fairy chimneys surround him like ancient guardians. Wide angle f/8, child 30% of frame.",
        "visual_prompt": "A breathtaking children's book cover showing A 6-year-old boy named Ali standing at the entrance of Goreme valley, looking up in wonder at hundreds of colorful hot air balloons rising into the golden sunrise sky. Massive fairy chimneys surround him like ancient guardians. Wide angle f/8, child 30% of frame. The child is wearing adventure jacket and comfortable pants. Cappadocia fairy chimneys and colorful hot air balloons in the background. Pixar Disney 3D animation style, warm cinematic lighting, vibrant colors. Epic wide angle composition with space for title at top."
      },
      {
        "page_number": 1,
        "text": "[SAYFA 1] Güneşin ilk ışıkları peri bacalarını altın rengine boyarken...",
        "scene_description": "A 6-year-old boy named Ali walking through a narrow path between tall fairy chimneys, touching the ancient rock surface with curiosity. Morning mist swirls around his feet. Warm golden light streams from the right.",
        "visual_prompt": "A children's book illustration showing A 6-year-old boy named Ali walking through a narrow path between tall fairy chimneys, touching the ancient rock surface with curiosity. Morning mist swirls around his feet. Warm golden light streams from the right. The child is wearing adventure jacket and comfortable pants. Background features Cappadocia's unique rock formations. Pixar Disney 3D animation style, warm cinematic lighting, vibrant colors. Soft background suitable for text overlay."
      }
      // ... pages 2-9 follow same pattern
    ]
  },
  "page_count": 10
}
```

### Style Count Doğrulama

Her sayfa için style keyword sayımı:

| Sayfa | pixar | disney | TOPLAM | Durum |
|-------|-------|--------|--------|-------|
| 0 | 1 | 1 | 2 | ✅ TEK |
| 1 | 1 | 1 | 2 | ✅ TEK |
| 2 | 1 | 1 | 2 | ✅ TEK |
| ... | 1 | 1 | 2 | ✅ TEK |

---

## 🛡️ KONTAMINASYON KONTROLLERI

### Log Çıktıları

```
✅ CLEAN - Page 0: No contamination
✅ CLEAN - Page 1: No contamination
⚠️ STYLE_LEAK:PIXAR - scene_description içinde style bulundu (Gemini'den sızma)
⚠️ LOCATION:ISTANBUL_IN_CAPPADOCIA - Kapadokya senaryosunda İstanbul elementi
⚠️ DOUBLE_STYLE:PIXARx2 - Style 2 kez eklendi (bug!)
```

---

## 📝 CACHE YAPISI

```json
{
  "style_id": "visual-style-uuid",
  "scenario_id": "kapadokya-uuid",
  "outcomes_hash": "a1b2c3d4e5f6",
  "prompts": [
    {
      "page_number": 0,
      "text": "Ali, Kapadokya'nın...",
      "scene_description": "A 6-year-old boy...",
      "visual_prompt": "A breathtaking..."
    }
  ]
}
```

### Cache Invalidation Kuralları

Cache aşağıdaki durumlardan birinde geçersiz olur:
1. `style_id` değişirse
2. `scenario_id` değişirse
3. `outcomes_hash` değişirse (farklı learning outcomes seçilirse)

---

## ✅ KURALLAR ÖZETİ

1. **Scenario Templates KULLANILIYOR:** `ai_prompt_template`, `cover_prompt_template`, `page_prompt_template`
2. **Location/Cultural ENFORCE ediliyor:** Her sayfada kontrol ve enjeksiyon
3. **Style TEK YERDE eklenir:** `_compose_visual_prompts()` içinde
4. **Fal.ai style EKLEMİYOR:** Prompt AS-IS kullanılıyor
5. **JSON repair VAR:** `_extract_and_repair_json()` ile
6. **fixed_outfit VAR:** Her prompt'a enjekte ediliyor
7. **Cache invalidation TAM:** style_id + scenario_id + outcomes_hash
