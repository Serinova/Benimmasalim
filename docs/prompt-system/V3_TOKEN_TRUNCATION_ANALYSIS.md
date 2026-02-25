# V3 Token / Uzunluk Kesilmesi Analizi

> **Tarih:** 2026-02-18  
> **Kapsam:** Gemini prompt input truncation + Fal.ai token budget + STYLE/negative kayıp riski

---

## 1. Executive Summary

Sistemde **iki bağımsız truncation noktası** var: Gemini (hikaye üretimi) ve Fal.ai (görsel üretimi). Kritik bulgu:

| Hedef | Limit | Mevcut Prompt | Risk | Kesilme Var mı? |
|-------|-------|---------------|------|-----------------|
| **Gemini PASS-0** | 1M token input | ~2.5K karakter (~625 token) | **YOK** | Hayır |
| **Gemini PASS-1** | 1M token input | ~6-15K karakter (~1.5-3.7K token) | **YOK** | Hayır |
| **Fal.ai Prompt** | 512 token (~2048 char) | ~800-1800 karakter | **ORTA** | Evet, bazen |
| **Fal.ai Negative** | Bilinmiyor (soft) | ~400-600 karakter | **DÜŞÜK** | Hayır |

**Ana Risk:** Fal.ai'de `max_sequence_length=512` token limiti aşıldığında **STYLE: bloğu kesilir** çünkü prompt sonunda yer alır. Kodda `truncate_safe_2d(prompt, 2048)` koruması var ama bu sadece karakter bazlı — Fal.ai'nin kendi tokenizer'ı farklı uzunlukta kesebilir.

---

## 2. Gemini Prompt Boyutları

### 2.1 PASS-0: Blueprint Generation

**Model:** `gemini-2.0-flash`  
**Input limit:** 1.048.576 token (1M)  
**maxOutputTokens:** 16.000

| Bileşen | Tahmini Karakter | Kaynak |
|---------|------------------|--------|
| `BLUEPRINT_SYSTEM_PROMPT` | ~2.000 char | `blueprint_prompt.py:26-120` |
| `build_blueprint_task_prompt()` | ~500-1.500 char | Değişken: bible facts, characters |
| **Toplam Input** | **~2.500-3.500 char** | **~625-875 token** |

**Sonuç:** Gemini 1M token limitine göre **%0.06** kullanım. Kesilme riski **sıfır**.

### 2.2 PASS-1: Story Pages Generation

**Model:** `gemini-2.0-flash`  
**Input limit:** 1.048.576 token (1M)  
**maxOutputTokens:** 32.000

| Bileşen | Tahmini Karakter | Kaynak |
|---------|------------------|--------|
| `PAGE_GENERATION_SYSTEM_PROMPT` | ~2.800 char | `page_prompt.py:24-113` |
| `STORY_NO_FIRST_DEGREE_FAMILY_TR` | ~400 char | Sabit (aile yasağı) |
| `build_page_task_prompt()` sabit kısım | ~600 char | Talimatlar |
| Blueprint JSON (16 sayfa) | ~3.000-8.000 char | Değişken |
| Blueprint JSON (22 sayfa) | ~5.000-12.000 char | Değişken |
| Value message block | ~100 char | Opsiyonel |
| Magic items | ~200 char | Opsiyonel |
| Banned words | ~200 char | Sabit |
| **Toplam Input (16 sayfa)** | **~7.300-12.300 char** | **~1.800-3.000 token** |
| **Toplam Input (22 sayfa)** | **~9.300-16.300 char** | **~2.300-4.000 token** |

**Sonuç:** Gemini limitinin **%0.4** kullanımı. Kesilme riski **sıfır**.

### 2.3 Gemini Output Truncation

| Pass | maxOutputTokens | Beklenen Output | Risk |
|------|-----------------|-----------------|------|
| PASS-0 | 16.000 | ~2.000-5.000 token (Blueprint JSON) | **Düşük** — 22 sayfa blueprint ~12K token |
| PASS-1 | 32.000 | ~5.000-15.000 token (22 sayfa × text+prompt+negative) | **Düşük** — 22 sayfa ~20K token worst case |

PASS-1 worst case (22 sayfa × ~800 token/sayfa) = ~17.600 token < 32.000 limiti. Güvenli, ama çok uzun cultural_hook'larla margin düşebilir.

**Dikkat:** `_extract_and_repair_json` fonksiyonu (`:1037`) kesilmiş JSON'u tespit edip kapama denemesi yapıyor — bu mekanizma output truncation yaşandığında devreye girer:
```python
"JSON appears truncated, attempting repair"
```

---

## 3. Fal.ai Prompt Boyutları — KRİTİK BÖLGE

### 3.1 Token Budget

```python
# constants.py:49-53
MAX_FAL_PROMPT_CHARS = 2048   # 512 token × ~4 char/token
MAX_VISUAL_PROMPT_BODY_CHARS = 720  # Body kısmı; STYLE kesilmesin diye
```

Fal.ai `flux-pulid` modeline gönderilen payload:
```python
"max_sequence_length": 512  # Token limit — bu değer 128'den 512'ye çıkarılmış
```

**Önceki sorun (çözüldü):** `max_sequence_length=128` iken prompt'ların ~%70'i kesiliyordu. 512'ye çıkarılmasıyla iyileşti.

### 3.2 V3 Composed Prompt Anatomy

`compose_enhanced_prompt()` çıktısı şu bileşenlerden oluşur:

| Sıra | Bileşen | Tahmini Uzunluk | Örnek |
|------|---------|-----------------|-------|
| 1 | `style_anchor` | 25-40 char | `"2D hand-painted storybook."` |
| 2 | `character_bible.prompt_block` | 200-350 char | `"4-year-old boy named Bora, curly brown hair..."` |
| 3 | Cleaned LLM scene prompt | 100-300 char | `"exploring a cave with torch-lit corridors..."` |
| 4 | Extra objects | 20-60 char | `"lantern, map, stone door"` |
| 5 | Iconic anchors | 40-80 char | `"fairy chimneys, hot air balloons"` |
| 6 | Shot plan fragment | 80-150 char | `"Wide shot, child 30% of frame..."` |
| 7 | Value visual motif | 40-80 char | `"a small golden confidence charm..."` |
| 8 | Emotion | 25-40 char | `"child's expression: curious"` |
| 9 | `STYLE: {style_block}` | 150-250 char | `"STYLE: Cheerful 2D hand-painted..."` |
| 10 | Required suffix | 30 char | `"no text, no watermark, no logo"` |
| | **TOPLAM** | **~710-1380 char** | |

### 3.3 Senaryo Bazlı Boyut Tahmini

| Senaryo | Prompt Boyutu | Risk |
|---------|---------------|------|
| **Minimum** (kısa bible, kısa scene, no motif) | ~710 char (~178 token) | Güvenli |
| **Tipik** (normal bible + scene + motif + anchors) | ~1000-1200 char (~250-300 token) | Güvenli |
| **Uzun** (uzun bible + companion + uzun scene + motif) | ~1400-1600 char (~350-400 token) | **Margin düşük** |
| **Worst case** (face analysis desc + companion + tüm bileşenler) | ~1600-2000 char (~400-500 token) | **RİSK: STYLE kesilir** |
| **Aşım** (>2048 char) | 2000+ char | **truncate_safe_2d devreye girer** |

### 3.4 Kesilme Zinciri (V3 Path)

Fal.ai'ye ulaşana kadar **3 ayrı truncation noktası** var:

```
compose_enhanced_prompt()
  └─ Çıktı: image_prompt_en (koruma yok, ham uzunluk)

gemini_service.py:2794  ← TRUNCATION POINT 1 (Gemini tarafı)
  if len(final_prompt) > MAX_FAL_PROMPT_CHARS:  # 2048
      final_prompt = truncate_safe_2d(final_prompt, MAX_FAL_PROMPT_CHARS)
      # ⚠️ Basit kelime-sınırı kesmesi, STYLE bloğu korunmuyor!

fal_ai_service.py:387  ← TRUNCATION POINT 2 (Fal servis tarafı)
  if len(full_prompt) > MAX_FAL_PROMPT_CHARS:  # 2048
      full_prompt = truncate_safe_2d(full_prompt, MAX_FAL_PROMPT_CHARS)
      # ⚠️ Aynı basit kesme, STYLE korunmuyor!

Fal.ai server-side  ← TRUNCATION POINT 3 (API tarafı)
  max_sequence_length=512 token → Fal kendi tokenizer'ı ile keser
  # ⚠️ Bu kesme görünmez — log'a düşmez!
```

---

## 4. STYLE Bloğu Kaybı Senaryoları

### 4.1 V3 Path — `truncate_safe_2d` STYLE Korumaz

**Dosya:** `gemini_service.py:2794` ve `fal_ai_service.py:387`

V3'te `truncate_safe_2d()` çağrılır — bu fonksiyon sadece kelime sınırında keser, **STYLE: bloğunu koruma mekanizması yok:**

```python
def truncate_safe_2d(text: str, max_length: int = 1200) -> str:
    cut = s[:max_length + 1].rsplit(" ", 1)[0]  # Basit kesme
```

STYLE bloğu prompt'un **sonunda** olduğu için, uzun prompt kesildiğinde ilk kurban olur:

```
[style_anchor][bible][scene][objects][anchors][shot][motif][emotion][STYLE: ...][suffix]
                                                                     ^^^^^^^^^^^^^^^^
                                                                     İLK KESİLEN BÖLGE
```

### 4.2 V2 Path — STYLE Koruması VAR (Karşılaştırma)

**Dosya:** `visual_prompt_composer.py:785-808`

V2'de akıllı truncation var — STYLE bloğunu kısaltır ama tamamen silmez:

```python
if len(prompt) > MAX_FAL_PROMPT_CHARS:
    style_marker = "\n\nSTYLE:"
    style_start = prompt.find(style_marker)
    if style_start > 0:
        body_part = prompt[:style_start]
        available = MAX_FAL_PROMPT_CHARS - len(body_part) - len(style_marker) - 1
        if available > 50:
            prompt = f"{body_part}{style_marker}\n{style_content[:available]}"
        else:
            prompt = body_part[:MAX_FAL_PROMPT_CHARS]  # Son çare: STYLE drop
```

**Sonuç:** V3 path'inde V2'deki STYLE-korumalı truncation **kullanılmıyor**. Bu bir eksiklik.

### 4.3 Fal.ai Server-Side Truncation (Görünmez)

`max_sequence_length=512` ayarı Fal.ai'nin **kendi tokenizer'ına** bağlı. Bizim karakter hesabımız (~4 char/token) bir tahmin. Gerçek tokenizer farklı olabilir:

| Prompt İçeriği | Char/Token Oranı |
|----------------|------------------|
| Basit İngilizce kelimeler | ~4.0 |
| Teknik terimler (subsurface scattering) | ~5-6 |
| Virgüllü kısa token'lar | ~3-4 |
| Türkçe isimler (Göbeklitepe, Kapadokya) | ~6-8 |

1200 char'lık tipik prompt → gerçek token sayısı: 280-350 token (512'nin altında)  
1800 char'lık uzun prompt → gerçek token sayısı: 400-500 token (**512 sınırına yakın**)

### 4.4 Negative Prompt — Kesilme Riski

Negative prompt ayrı bir parametre olarak gönderilir:

```python
payload = {
    "prompt": full_prompt,
    "negative_prompt": full_negative,  # Ayrı parametre
}
```

`build_enhanced_negative()` çıktısı: ~400-600 karakter. Fal.ai'nin negative prompt token limiti belgelenmemiş ama pratikte kesilme gözlemlenmemiş.

---

## 5. Mevcut Log Durumu

### 5.1 Zaten Loglanan Bilgiler

| Log Key | Dosya | Ne Logluyor |
|---------|-------|-------------|
| `V3_PAGE_PIPELINE_STATS.prompt_length` | `gemini_service.py:2812` | Final prompt karakter uzunluğu |
| `V3_PAGE_PIPELINE_STATS.negative_length` | `gemini_service.py:2813` | Negative prompt uzunluğu |
| `V3_PAGE_PIPELINE_STATS.has_style_block` | `gemini_service.py:2814` | `"STYLE:" in prompt` boolean |
| `V3 prompt truncated to Fal limit` | `gemini_service.py:2797` | Kesilme uyarısı |
| `V3_SKIP_COMPOSE_PROMPT_STATS.prompt_length` | `fal_ai_service.py:400` | Fal'a giden prompt uzunluğu |
| `V3_SKIP_COMPOSE_PROMPT_STATS.has_style_block` | `fal_ai_service.py:402` | STYLE varlığı |

### 5.2 Eksik Log Bilgileri

| Eksik | Neden Gerekli |
|-------|---------------|
| **Tahmini token sayısı** | Karakter uzunluğu yanıltıcı — token sayısı asıl limit |
| **Truncation flag (boolean)** | Kesilip kesilmediği tek bakışta görülmeli |
| **STYLE block kaybedildi mi?** | Truncation sonrası STYLE var mı kontrolü |
| **Fal.ai server-side truncation** | API'nin kendi kesmesi görünmez |
| **Bileşen bazlı uzunluklar** | Hangi bileşen büyütüyor? (bible, scene, anchors...) |
| **PASS-0/PASS-1 input prompt uzunluğu** | Gemini inputu loglanmıyor |

---

## 6. Log Önerisi

### 6.1 `compose_enhanced_prompt()` Çıkışı

```python
# visual_prompt_builder.py — compose_enhanced_prompt() sonuna ekle

_estimated_tokens = len(prompt) / 4.0  # Rough estimate
logger.info(
    "V3_PROMPT_COMPOSED",
    page=shot_plan.page,
    total_chars=len(prompt),
    estimated_tokens=round(_estimated_tokens),
    token_budget_pct=round(_estimated_tokens / 512 * 100, 1),
    has_style_block="STYLE:" in prompt,
    style_block_chars=len(prompt[prompt.index("STYLE:"):]) if "STYLE:" in prompt else 0,
    bible_chars=len(character_bible.prompt_block),
    scene_chars=len(cleaned),
    anchors_chars=len(anchors_str),
    truncation_needed=len(prompt) > 2048,
)
```

### 6.2 Truncation Event Log

```python
# gemini_service.py — truncation noktasına ekle

if len(final_prompt) > MAX_FAL_PROMPT_CHARS:
    _had_style_before = "STYLE:" in final_prompt
    original_len = len(final_prompt)
    final_prompt = truncate_safe_2d(final_prompt, MAX_FAL_PROMPT_CHARS)
    _has_style_after = "STYLE:" in final_prompt
    logger.warning(
        "V3_PROMPT_TRUNCATED",
        page=llm_page_num,
        original_chars=original_len,
        truncated_chars=len(final_prompt),
        chars_removed=original_len - len(final_prompt),
        style_block_lost=_had_style_before and not _has_style_after,  # ← KRİTİK
        estimated_tokens_after=round(len(final_prompt) / 4.0),
        truncated_flag=True,
    )
```

### 6.3 Gemini Input Length Log

```python
# gemini_service.py — _pass0_generate_blueprint ve _pass1_generate_pages'a ekle

logger.info(
    "GEMINI_INPUT_STATS",
    pass_name="PASS-0",  # veya "PASS-1"
    input_chars=len(full_prompt),
    estimated_input_tokens=round(len(full_prompt) / 4.0),
    max_output_tokens=16000,  # veya 32000
    model=self.story_model,
)
```

---

## 7. Auto-Shortener Stratejisi

### Strateji 1: STYLE-Korumalı Truncation (P0 — Hemen Uygula)

V2'deki mantığı V3 path'ine taşı:

```python
def truncate_v3_style_aware(prompt: str, max_chars: int = 2048) -> str:
    """Truncate V3 prompt preserving STYLE: block.
    
    Priority (en son kesilecek → ilk kesilecek):
    1. STYLE: block (kısaltılır, son çare silinir)
    2. Extra objects + iconic anchors (kısaltılır)
    3. Scene description (kısaltılır)
    4. CharacterBible (ASLA kesilmez)
    5. Style anchor (ASLA kesilmez)
    """
    if len(prompt) <= max_chars:
        return prompt
    
    style_marker = ", STYLE: "
    style_idx = prompt.find("STYLE: ")
    
    if style_idx > 0:
        body = prompt[:style_idx].rstrip(", ")
        style_content = prompt[style_idx:]
        
        # Body sığıyorsa, STYLE'ı kısalt
        available_for_style = max_chars - len(body) - 2  # ", " separator
        if available_for_style > 80:
            return f"{body}, {style_content[:available_for_style]}"
        elif available_for_style > 0:
            # STYLE çok kısa olacak — sadece style_anchor kalsın
            return body[:max_chars]
    
    # STYLE yok veya bulunamadı
    return truncate_safe_2d(prompt, max_chars)
```

### Strateji 2: Bileşen Bazlı Budget Allocation (P1)

Her bileşene sabit bütçe ata:

```python
TOKEN_BUDGET = 512
CHAR_BUDGET = TOKEN_BUDGET * 4  # 2048

COMPONENT_BUDGETS = {
    "style_anchor": 50,          # ~12 token — ASLA kesilmez
    "character_bible": 400,      # ~100 token — ASLA kesilmez  
    "scene_description": 400,    # ~100 token — kısaltılabilir
    "extra_objects": 80,         # ~20 token — düşürülebilir
    "iconic_anchors": 100,       # ~25 token — düşürülebilir
    "shot_plan": 150,            # ~37 token — kısaltılabilir
    "value_motif": 100,          # ~25 token — kısaltılabilir
    "emotion": 50,               # ~12 token — kısaltılabilir
    "style_block": 400,          # ~100 token — kısaltılabilir
    "suffix": 40,                # ~10 token — ASLA kesilmez
    # TOPLAM: ~1770 char (~442 token) — 512 limiti altında
}
```

`compose_enhanced_prompt()` içinde her bileşeni bütçesiyle sınırla:

```python
if len(cleaned) > COMPONENT_BUDGETS["scene_description"]:
    cleaned = truncate_safe_2d(cleaned, COMPONENT_BUDGETS["scene_description"])
```

### Strateji 3: Dinamik Token Counter (P2)

Fal.ai'nin tokenizer'ına yakın bir tahmin için `tiktoken` veya basit whitespace tokenizer:

```python
def estimate_flux_tokens(text: str) -> int:
    """Rough Flux token estimate — whitespace + punctuation split."""
    import re
    tokens = re.split(r'[\s,;.]+', text.strip())
    return len([t for t in tokens if t])
```

Bunu `compose_enhanced_prompt()` sonunda kontrol et:

```python
estimated = estimate_flux_tokens(prompt)
if estimated > 480:  # %94 of 512 — safety margin
    logger.warning("V3_TOKEN_BUDGET_HIGH", tokens=estimated, chars=len(prompt))
    prompt = truncate_v3_style_aware(prompt, max_chars=1900)  # Daha agresif kesme
```

---

## 8. Truncation Noktaları Karşılaştırma Tablosu

| Truncation Noktası | Dosya:Satır | Limit | STYLE Koruması | Log | Risk |
|---------------------|-------------|-------|----------------|-----|------|
| `gemini_service.py:2794` | V3 page loop | 2048 char | **YOK** ⚠️ | Var (uyarı) | Orta |
| `gemini_service.py:2709` | V3 cover | 2048 char | **YOK** ⚠️ | Var (uyarı) | Orta |
| `fal_ai_service.py:387` | V3 skip_compose | 2048 char | **YOK** ⚠️ | Var (uyarı) | Orta |
| `fal_ai_service.py:428` | V2 legacy | 2048 char | **YOK** | Var (uyarı) | Orta |
| `visual_prompt_composer.py:790` | V2 compose | 2048 char | **VAR** ✓ | Var | Düşük |
| Fal.ai server | API tarafı | 512 token | **YOK** | **YOK** ⚠️ | Yüksek |
| `gemini_service.py:2178` | V2 LLM output | 1200 char | **YOK** | Yok | Düşük |

---

## 9. Aksiyon Planı

| Öncelik | Aksiyon | Etki | Effort |
|---------|---------|------|--------|
| **P0** | V3 truncation'a STYLE-korumalı kesme ekle (`truncate_v3_style_aware`) | STYLE bloğu kaybını önler | 30 dk |
| **P0** | `style_block_lost` flag'ini loga ekle | Kesilme anında uyarı | 10 dk |
| **P1** | `V3_PROMPT_COMPOSED` log event ekle (bileşen bazlı uzunluklar) | Hangi bileşenin büyüttüğünü görme | 20 dk |
| **P1** | `GEMINI_INPUT_STATS` log event ekle | Gemini input boyutunu izleme | 10 dk |
| **P1** | `estimate_flux_tokens()` fonksiyonu ile pre-check | Char/token uyumsuzluğunu yakalama | 20 dk |
| **P2** | Bileşen bazlı budget allocation | Kökten çözüm — her parça sınırlı | 1 saat |
| **P2** | CharacterBible prompt_block kısaltma modu | Uzun face description → compact versiyon | 30 dk |

---

## 10. Dosya Haritası

| Dosya | Truncation Rolü |
|-------|-----------------|
| `backend/app/prompt_engine/constants.py:49-53` | `MAX_FAL_PROMPT_CHARS=2048`, `MAX_VISUAL_PROMPT_BODY_CHARS=720` |
| `backend/app/prompt_engine/prompt_sanitizer.py:237-246` | `truncate_safe_2d()` — basit kelime-sınırı kesme |
| `backend/app/prompt_engine/visual_prompt_builder.py:475-583` | `compose_enhanced_prompt()` — prompt assembly |
| `backend/app/prompt_engine/visual_prompt_composer.py:785-808` | V2 STYLE-korumalı truncation (V3'te yok!) |
| `backend/app/services/ai/gemini_service.py:2794` | V3 page truncation noktası |
| `backend/app/services/ai/gemini_service.py:2709` | V3 cover truncation noktası |
| `backend/app/services/ai/fal_ai_service.py:387` | V3 skip_compose truncation noktası |
| `backend/app/prompt_engine/blueprint_prompt.py` | PASS-0 prompt builder (~2.5K char) |
| `backend/app/prompt_engine/page_prompt.py` | PASS-1 prompt builder (~7-16K char) |

---

## 11. Özet

```
Gemini tarafı (PASS-0, PASS-1):
├─ Input limit: 1M token → kullanım %0.06–0.4 → RİSK YOK
├─ Output limit: 16K/32K token → margin var ama 22 sayfa worst case'de dar
└─ JSON truncation repair mekanizması mevcut

Fal.ai tarafı (görsel üretim):
├─ max_sequence_length = 512 token (~2048 char)
├─ Tipik V3 prompt: 1000-1200 char (~250-300 token) → Güvenli
├─ Uzun V3 prompt: 1400-1800 char (~350-450 token) → Margin düşük
├─ Worst case: 2000+ char → truncate_safe_2d devreye girer
│   └─ ⚠️ STYLE: bloğu kesilir (prompt sonunda)
│   └─ ⚠️ V3'te STYLE-korumalı truncation YOK (V2'de var!)
└─ Fal server-side 512 token kesme → LOG'A DÜŞMÜYOR!

Acil ihtiyaç:
1) V3 path'ine STYLE-korumalı truncation (V2'den taşı)
2) style_block_lost flag'i loga ekle
3) Bileşen bazlı prompt uzunluk logu
```
