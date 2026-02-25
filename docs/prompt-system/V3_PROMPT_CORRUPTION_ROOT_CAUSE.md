# V3 Prompt Bozulmaları — Kök Neden Analizi

> **Tarih:** 2026-02-18  
> **Kapsam:** "a glowing ancient symbolm", "Ia glowing…", kopuk tırnaklar, yarım cümleler

---

## 1. Executive Summary

Prompt bozulmalarının **5 bağımsız kök nedeni** tespit edildi. Hepsi aynı dosyadan kaynaklanır:

| Sıra | Kök Neden | Bozulma Örneği | Dosya:Satır |
|------|-----------|----------------|-------------|
| **RC-1** | Tırnak sonrası Türkçe ek yutulmuyor | `a glowing ancient symbolm` | `visual_prompt_builder.py:124` |
| **RC-2** | Tırnak öncesi word boundary yok | `Ia glowing ancient symbol` | `visual_prompt_builder.py:124` |
| **RC-3** | Greedy `\w*` önceki kelimeyi yutuyor | `a decorated with carved patterns on a wall` | `visual_prompt_builder.py:132` |
| **RC-4** | `truncate_safe_2d` cümle ortasından kesiyor | `a 4-year-old child named Bora wi` | `prompt_sanitizer.py:237` |
| **RC-5** | Çoklu replacement zincirinde artık parça | `a glowing ancient symbol, a decorative symbol` | chain interaction |

**Ortak kaynak:** `_TEXT_QUOTE_PATTERNS` regex dizisi (`visual_prompt_builder.py:122-150`)

---

## 2. Sanitizer Zinciri (Çalışma Sırası)

`compose_enhanced_prompt()` fonksiyonunda (`:503-581`) sanitizer'lar bu sırayla çalışır:

```
LLM raw_prompt
  │
  ├─ Step 1: _strip_existing_composition()     ← kompozisyon talimatları silme
  ├─ Step 2: _strip_existing_character()        ← karakter tanımı silme
  ├─ Step 3: _kids_safe_rewrite()               ← tehlikeli içerik yeniden yazma
  ├─ Step 4: _strip_embedded_text()             ← ⚠️ BOZULMA BURADAN GELİYOR
  ├─ Step 5: _strip_no_text_suffix()            ← "no text" suffix silme
  │
  ├─ [... prompt assembly: style_anchor + bible + cleaned + anchors + ...]
  │
  ├─ Step 6: _remove_shot_conflict()            ← kadraj çelişki silme
  ├─ Step 7: _sanitize_v3_prompt_text()         ← ⚠️ KISMİ TEMİZLEME
  ├─ Step 8: _ensure_suffix()                   ← "no text, no watermark, no logo"
  ├─ Step 9: _sanitize_v3_prompt_text()         ← 2. pass
  └─ Step 10: _ensure_suffix()                  ← final suffix
```

---

## 3. Kök Neden Detayları

### RC-1: "a glowing ancient symbolm" — Türkçe Ek Yapışması

**Regex (`:124`):**
```python
re.compile(
    r"""(?:the\s+word\s+|saying\s+|reads?\s+|written\s+)?"""
    r"""['"\u2018\u2019\u201C\u201D]"""
    r"""([^'"\u2018\u2019\u201C\u201D]{1,40})"""
    r"""['"\u2018\u2019\u201C\u201D]""",
    re.I,
)
# Replacement: "a glowing ancient symbol"
```

**Sorun:** Türkçe'de tırnak içindeki kelimelere possesif/durum ekleri tırnağın **dışında** yapışır:

| LLM Çıktısı | Regex Eşleşmesi | Sonuç |
|-------------|-----------------|-------|
| `'Sabır'mızı keşfettik` | `'Sabır'` eşleşir | `a glowing ancient symbolmızı keşfettik` |
| `"Cesaret"le dolu` | `"Cesaret"` eşleşir | `a glowing ancient symbolle dolu` |
| `'Güç'ün kaynağı` | `'Güç'` eşleşir | `a glowing ancient symbolün kaynağı` |
| `"Özgüven"i buldu` | `"Özgüven"` eşleşir | `a glowing ancient symboli buldu` |

**Mekanizma:** Regex kapanış tırnağından sonraki Türkçe eki `[mınıüeale...]` **tüketmez**. Replacement string "a glowing ancient symbol" kapanış tırnağının hemen yerine gelir, Türkçe ek yapışık kalır.

**Minimum Repro:**
```python
import re
pattern = re.compile(r"""['"]([^'"]{1,40})['"]""")
result = pattern.sub("a glowing ancient symbol", "'Sabır'mızı")
# result = "a glowing ancient symbolmızı"  ← BOZUK
```

---

### RC-2: "Ia glowing ancient symbol" — Eksik Word Boundary

**Sorun:** Aynı regex'te açılış tırnağından **önce** word boundary (`\b`) veya space zorunluluğu yok.

| LLM Çıktısı | Regex Eşleşmesi | Sonuç |
|-------------|-----------------|-------|
| `I"Cesaret" yazdı` | `"Cesaret"` eşleşir | `Ia glowing ancient symbol yazdı` |
| `bI'Sabır' dedi` | `'Sabır'` eşleşir | `bIa glowing ancient symbol dedi` |
| `child discovers"courage"` | `"courage"` eşleşir | `child discoversa glowing ancient symbol` |

**Mekanizma:** Tırnak öncesinde boşluk olmadığında, önceki karakterle replacement string bitiştirme olur.

**Minimum Repro:**
```python
import re
pattern = re.compile(r"""['"]([^'"]{1,40})['"]""")
result = pattern.sub("a glowing ancient symbol", 'discovers"courage"here')
# result = "discoversa glowing ancient symbolhere"  ← BOZUK
```

---

### RC-3: Greedy `\w*` Önceki Kelimeyi Yutuyor

**Regex (`:132`):**
```python
re.compile(
    r"\b\w*\s*(?:written|engraved|inscribed|etched)\s+on\b",
    re.I,
)
# Replacement: "decorated with carved patterns on"
```

**Sorun:** `\b\w*` ifadesi, "written" kelimesinden **önceki kelimeyi de** yakalar:

| LLM Çıktısı | Regex Eşleşmesi | Sonuç |
|-------------|-----------------|-------|
| `a stone written on the wall` | `stone written on` eşleşir | `a decorated with carved patterns on the wall` |
| `message engraved on the pillar` | `message engraved on` eşleşir | `decorated with carved patterns on the pillar` |

**Mekanizma:** `\w*` sıfır veya daha fazla kelime karakteriyle eşleşir. `\b\w*` bir kelime sınırından başlayıp önceki tam kelimeyi tüketir.

**Minimum Repro:**
```python
import re
pattern = re.compile(r"\b\w*\s*(?:written)\s+on\b", re.I)
result = pattern.sub("decorated with carved patterns on", "a stone written on the wall")
# result = "a decorated with carved patterns on the wall"  ← "stone" silindi, gramer bozuldu
```

---

### RC-4: `truncate_safe_2d` Cümle Ortasından Kesiyor

**Dosya:** `prompt_sanitizer.py:237`

```python
def truncate_safe_2d(text: str, max_length: int = 1200) -> str:
    cut = s[:max_length + 1].rsplit(" ", 1)[0]  # kelime sınırında kes
```

**Sorun:** Kelime sınırında kesiyor ama **cümle/clause sınırını** dikkate almıyor. Son kelime yarım kalan bir ifadenin parçası olabilir.

| Durum | Sonuç |
|-------|-------|
| `... child is wearing a cozy adventure jacket wi` | "wi" kelimesi → "with" kesilmiş |
| `... STYLE: soft pastel, warm col` | "col" → "colors" kesilmiş |

`MAX_FAL_PROMPT_CHARS = 2048` limitinde kesilme riski düşük ama uzun stili/CharacterBible prompt'larında gerçekleşebilir.

---

### RC-5: Zincir Etkileşim — Çoklu Replacement Artığı

**Senaryo:** Aynı prompt'ta birden fazla `_TEXT_QUOTE_PATTERNS` eşleşmesi:

```
LLM: "the child reads 'Sabır' and sees the word 'Güç' written on the stone"

Pass 1 (pattern[0]): 'Sabır' → "a glowing ancient symbol"
Pass 2 (pattern[0]): 'Güç' → "a glowing ancient symbol"  
Pass 3 (pattern[4]): "reads a glowing ancient symbol" → "showing a mysterious glyph"
Pass 4 (pattern[1]): "word a glowing ancient symbol written on" → "decorated with a carved icon"

Result: "the child showing a mysterious glyph and sees decorated with a carved icon the stone"
```

Birbirini tetikleyen replacement'lar, anlamsız ifade birikimine yol açar.

**Özel vaka: `_sanitize_v3_prompt_text` kısmi fix'i:**

```python
# Sadece "a glowing ancient symbols" (çoğul) fix'i var:
out = re.sub(r"\ba\s+glowing\s+ancient\s+symbols\b", "glowing ancient symbols", out, flags=re.I)
```

Ama `symbolm`, `symbolün`, `symbolle`, `symbolın` gibi Türkçe ek yapışmaları yakalanmıyor.

---

## 4. Tetiklenme Koşulları

### Ne Zaman Tetiklenir?

| Koşul | Sıklık | Hangi RC |
|-------|--------|----------|
| LLM Türkçe tırnaklı kelime ürettiğinde | **Yüksek** — Gemini sıklıkla `'Sabır'`, `"Cesaret"` gibi Türkçe tırnaklı değer kelimeleri üretir | RC-1, RC-2 |
| LLM "written on" / "engraved on" kullandığında | Orta — antik lokasyonlarda (Göbeklitepe, Efes) sık | RC-3 |
| Prompt 2048 karakteri aştığında | Düşük — ama uzun stiller + CharacterBible ile olası | RC-4 |
| Birden fazla tırnaklı ifade aynı promptta | Orta — eğitim değeri + lokasyon ismi birlikte | RC-5 |

### Deterministic mi?

**Evet.** Tüm bozulmalar **deterministic regex substitution** sonucu oluşur. Aynı LLM çıktısı → aynı bozulma. LLM çıktısı değişmediği sürece, sonuç her zaman aynıdır.

### Hangi Sayfalarda?

Bozulma, LLM'in tırnaklı Türkçe kelime veya "written/engraved" ifade kullandığı **herhangi bir** sayfada olabilir. Özellikle:
- **Değer sayfaları** (cesaret, özgüven kelimeleri tırnak içinde): Sayfa 3-5, 15-18
- **Kültürel keşif sayfaları** (yazıtlar, kabartmalar): Orta sayfalar (8-14)
- **Kapanış sayfası** (ders/mesaj cümleleri): Son 2-3 sayfa

---

## 5. Patch Planı

### Fix-1: `_TEXT_QUOTE_PATTERNS[0]` — Türkçe Ek + Boundary

**Mevcut (`:124`):**
```python
(re.compile(r"""(?:the\s+word\s+|saying\s+|reads?\s+|written\s+)?['"\u2018\u2019\u201C\u201D]([^'"\u2018\u2019\u201C\u201D]{1,40})['"\u2018\u2019\u201C\u201D]""", re.I),
 "a glowing ancient symbol"),
```

**Önerilen:**
```python
(re.compile(
    r"""(?:^|(?<=\s))"""                          # ← boundary: satır başı veya boşluk sonrası
    r"""(?:the\s+word\s+|saying\s+|reads?\s+|written\s+)?"""
    r"""['"\u2018\u2019\u201C\u201D]"""
    r"""([^'"\u2018\u2019\u201C\u201D]{1,40})"""
    r"""['"\u2018\u2019\u201C\u201D]"""
    r"""(?:['\u2019]?[a-zA-ZçğıöşüÇĞİÖŞÜ]{0,5})?""",  # ← Türkçe ek tüketme (max 5 char)
    re.I,
), "a glowing ancient symbol"),
```

**Değişiklikler:**
1. `(?:^|(?<=\s))` — Açılış tırnağından önce boşluk veya satır başı zorunlu → RC-2 fix
2. `(?:['\u2019]?[a-zA-ZçğıöşüÇĞİÖŞÜ]{0,5})?` — Kapanış tırnağından sonra opsiyonel Türkçe ek (apostrophe + max 5 harf) → RC-1 fix

---

### Fix-2: `_TEXT_QUOTE_PATTERNS[2]` — Greedy `\w*` Kaldırma

**Mevcut (`:132`):**
```python
(re.compile(r"\b\w*\s*(?:written|engraved|inscribed|etched)\s+on\b", re.I),
 "decorated with carved patterns on"),
```

**Önerilen:**
```python
(re.compile(r"\b(?:written|engraved|inscribed|etched)\s+on\b", re.I),
 "decorated with carved patterns on"),
```

**Değişiklik:** `\w*\s*` prefix kaldırıldı → önceki kelime artık yutulmuyor.

---

### Fix-3: `_sanitize_v3_prompt_text` — Türkçe Ek Temizleyici Ekleme

**Mevcut (`:199`):**
```python
out = re.sub(r"\ba\s+glowing\s+ancient\s+symbols\b", "glowing ancient symbols", out, flags=re.I)
```

**Önerilen (genişletilmiş):**
```python
# Türkçe ek yapışması temizleyici — "a glowing ancient symbolm", "symbolün", "symbolle" vb.
out = re.sub(
    r"\ba\s+glowing\s+ancient\s+symbol[a-zA-ZçğıöşüÇĞİÖŞÜ]+\b",
    "a glowing ancient symbol",
    out,
    flags=re.I,
)
# Çoğul fix (mevcut)
out = re.sub(r"\ba\s+glowing\s+ancient\s+symbols\b", "glowing ancient symbols", out, flags=re.I)
out = re.sub(r"\ba\s+decorative\s+symbols\b", "decorative symbols", out, flags=re.I)

# "Ia glowing" / "discoversa glowing" — replacement'a yapışmış prefix
out = re.sub(r"(\S)(a\s+glowing\s+ancient\s+symbol)", r"\1 \2", out)
```

---

### Fix-4: Post-Sanitizer Validation — "Forbidden Token Linter"

Yeni fonksiyon önerisi:

```python
# visual_prompt_builder.py'ye eklenecek

_CORRUPTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Türkçe ek yapışması
    (re.compile(r"symbol[a-zçğıöşü]{1,6}\b", re.I), "RC-1: TR suffix on 'symbol'"),
    # Boundary-less replacement concat
    (re.compile(r"\S(?:a glowing ancient symbol)", re.I), "RC-2: missing space before replacement"),
    # Double replacement artifact
    (re.compile(r"a glowing ancient symbol.*a glowing ancient symbol", re.I), "RC-5: double replacement"),
    # Orphan single-char words (truncation artifact)
    (re.compile(r"\b[a-z]\s*$", re.I), "RC-4: truncation artifact"),
    # Broken article
    (re.compile(r"\ba\s+decorated\s+with\s+carved\s+patterns\s+on\s+a\b", re.I), "RC-3: greedy prefix ate word"),
]


def lint_prompt_corruption(prompt: str) -> list[str]:
    """Detect known corruption patterns in a composed prompt.
    
    Returns list of warning strings (empty = clean).
    """
    warnings: list[str] = []
    for pattern, description in _CORRUPTION_PATTERNS:
        if pattern.search(prompt):
            match_text = pattern.search(prompt).group()[:60]
            warnings.append(f"{description}: '{match_text}'")
    return warnings
```

---

### Fix-5: `truncate_safe_2d` — Clause-Aware Truncation

**Mevcut (`:237`):**
```python
def truncate_safe_2d(text: str, max_length: int = 1200) -> str:
    cut = s[:max_length + 1].rsplit(" ", 1)[0]
```

**Önerilen:**
```python
def truncate_safe_2d(text: str, max_length: int = 1200) -> str:
    if not text or len(text) <= max_length:
        return text
    s = text.strip()
    
    # Prefer cutting at clause boundary (comma, period) within last 100 chars
    search_zone = s[max(0, max_length - 100): max_length]
    last_clause = max(search_zone.rfind(", "), search_zone.rfind(". "))
    
    if last_clause > 0:
        cut_point = max(0, max_length - 100) + last_clause + 2  # after ", " or ". "
        return s[:cut_point].rstrip(" ,.")
    
    # Fallback: word boundary
    cut = s[:max_length + 1].rsplit(" ", 1)[0] if " " in s[:max_length + 1] else s[:max_length]
    rest = s[len(cut):].lstrip()
    if cut.endswith("2") and rest.lower().startswith("d"):
        cut = cut + rest[0]
    return cut
```

---

## 6. Test Planı

### Unit Test: RC-1 — Türkçe Ek Yapışması

```python
import pytest
from app.prompt_engine.visual_prompt_builder import _strip_embedded_text

class TestStripEmbeddedText:
    """RC-1: Turkish suffix after closing quote must be consumed."""

    @pytest.mark.parametrize("input_text,should_not_contain", [
        ("'Sabır'mızı keşfettik", "symbolm"),
        ("'Cesaret'le dolu", "symbolle"),
        ("'Güç'ün kaynağı", "symbolün"),
        ('"Özgüven"i buldu', "symboli"),
        ("'Sabır'ın gücü", "symbolın"),
    ])
    def test_turkish_suffix_not_leaked(self, input_text, should_not_contain):
        result = _strip_embedded_text(input_text)
        assert should_not_contain not in result, (
            f"Turkish suffix leaked: '{should_not_contain}' found in '{result}'"
        )

    @pytest.mark.parametrize("input_text", [
        "'Sabır' ve 'Cesaret' birlikte",
        "'Güç' keşfedildi",
        '"Merak" çok önemli',
    ])
    def test_replacement_contains_symbol(self, input_text):
        result = _strip_embedded_text(input_text)
        assert "glowing ancient symbol" in result or "decorative" in result
```

### Unit Test: RC-2 — Boundary-less Concat

```python
class TestBoundaryConcat:
    """RC-2: No character should directly precede 'a glowing'."""

    @pytest.mark.parametrize("input_text,should_not_contain", [
        ('I"Cesaret" yazdı', "Ia glowing"),
        ('discovers"courage"here', "discoversa"),
        ("bir'kelime'dir", "bira glowing"),
    ])
    def test_no_boundary_concat(self, input_text, should_not_contain):
        result = _strip_embedded_text(input_text)
        assert should_not_contain not in result, (
            f"Boundary-less concat: '{should_not_contain}' found in '{result}'"
        )
```

### Unit Test: RC-3 — Greedy Prefix

```python
class TestGreedyPrefix:
    """RC-3: Word before 'written on' must not be consumed."""

    def test_stone_written_on(self):
        result = _strip_embedded_text("a stone written on the wall")
        assert "stone" not in result or "a stone" not in result
        # "written on" replaced but "a stone" should NOT disappear
        # After fix: "a stone decorated with carved patterns on the wall"
```

### Unit Test: RC-4 — Truncation

```python
from app.prompt_engine.prompt_sanitizer import truncate_safe_2d

class TestTruncation:
    """RC-4: Truncation should prefer clause boundaries."""

    def test_clause_boundary_preferred(self):
        text = "scene in valley, child exploring, warm golden light, fairy chimneys visible"
        result = truncate_safe_2d(text, max_length=50)
        # Should cut at a comma, not mid-word
        assert result.endswith(("light", "exploring", "valley"))
        assert not result.endswith(("ligh", "explor", "valle"))

    def test_2d_not_split(self):
        text = "beautiful 2D illustration of a valley"
        result = truncate_safe_2d(text, max_length=12)
        assert "2D" in result
```

### Integration Test: Full Sanitizer Chain

```python
from app.prompt_engine.visual_prompt_builder import (
    _strip_existing_composition,
    _strip_existing_character,
    _kids_safe_rewrite,
    _strip_embedded_text,
    _sanitize_v3_prompt_text,
)

def _full_chain(raw: str) -> str:
    """Simulate compose_enhanced_prompt's sanitizer chain."""
    out = _strip_existing_composition(raw)
    out = _strip_existing_character(out)
    out = _kids_safe_rewrite(out)
    out = _strip_embedded_text(out)
    out = _sanitize_v3_prompt_text(out)
    return out

class TestFullChain:
    """Integration: full sanitizer chain produces no corruption."""

    CORRUPTIONS = [
        "symbolm", "symbolün", "symbolle", "symbolın", "symboli",
        "Ia glowing", "discoversa", "bIa",
    ]

    @pytest.mark.parametrize("raw", [
        "child discovers 'Sabır'mızı in the ancient temple",
        "I'Cesaret' is written on the stone",
        "'Güç'ün and 'Merak'ın symbols glow",
        'the message "Özgüven"i buldu is engraved on the wall',
        "a stone written on the pillar with 'Sabır'",
    ])
    def test_no_corruption_tokens(self, raw):
        result = _full_chain(raw)
        for corruption in self.CORRUPTIONS:
            assert corruption not in result, (
                f"Corruption '{corruption}' found in result: '{result}'"
            )
```

### Lint Test: Post-Composition Validation

```python
class TestPromptLinter:
    """Forbidden token linter catches known corruption patterns."""

    def test_clean_prompt_passes(self):
        clean = "soft pastel, 4-year-old boy, a glowing ancient symbol, fairy chimneys"
        warnings = lint_prompt_corruption(clean)
        assert len(warnings) == 0

    def test_turkish_suffix_detected(self):
        dirty = "child sees a glowing ancient symbolmızı"
        warnings = lint_prompt_corruption(dirty)
        assert any("RC-1" in w for w in warnings)

    def test_boundary_concat_detected(self):
        dirty = "child discoversa glowing ancient symbol"
        warnings = lint_prompt_corruption(dirty)
        assert any("RC-2" in w for w in warnings)
```

---

## 7. Uygulama Öncelikleri

| Öncelik | Fix | Etki | Effort |
|---------|-----|------|--------|
| **P0** | Fix-1: Türkçe ek + boundary regex | En sık görülen 2 bozulmayı (RC-1, RC-2) kökten çözer | 30 dk |
| **P0** | Fix-3: `_sanitize_v3_prompt_text` savunma katmanı | Fix-1 uygulanmasa bile mevcut bozulmaları yakalar | 15 dk |
| **P1** | Fix-2: Greedy `\w*` kaldırma | RC-3 çözümü — "written on" sayfalarında gramer düzeltme | 10 dk |
| **P1** | Fix-4: `lint_prompt_corruption()` fonksiyonu | Gelecekteki bozulmaları erken tespit, log'a uyarı | 30 dk |
| **P2** | Fix-5: Clause-aware truncation | Nadir durumlarda cümle ortası kesilmeyi önler | 20 dk |

**Toplam Tahmini Effort:** ~2 saat (test dahil)

---

## 8. Dosya Haritası

| Dosya | Rolü | İlgili RC |
|-------|------|-----------|
| `backend/app/prompt_engine/visual_prompt_builder.py:122-150` | `_TEXT_QUOTE_PATTERNS` — bozulmanın kaynağı | RC-1, RC-2, RC-3, RC-5 |
| `backend/app/prompt_engine/visual_prompt_builder.py:161-173` | `_strip_embedded_text()` — quote stripper | RC-1, RC-2 |
| `backend/app/prompt_engine/visual_prompt_builder.py:176-211` | `_sanitize_v3_prompt_text()` — kısmi temizleyici | RC-1 (kısmi fix mevcut) |
| `backend/app/prompt_engine/visual_prompt_builder.py:475-583` | `compose_enhanced_prompt()` — zincir orkestrasyon | Tüm RC'ler |
| `backend/app/prompt_engine/prompt_sanitizer.py:237-246` | `truncate_safe_2d()` — kesme fonksiyonu | RC-4 |
| `backend/app/prompt_engine/visual_prompt_builder.py:65-113` | `_UNSAFE_VISUAL_PATTERNS` — kids-safe rewrite | Bağımsız (bozulma üretmiyor) |

---

## 9. Özet

```
"a glowing ancient symbolm" bozulmasının hikayesi:

1. LLM üretir: "child discovers 'Sabır'mızı in the ancient temple"
                                  ^^^^^^^^^ Türkçe: tırnak içi "Sabır" + dışı "mızı" eki

2. _strip_embedded_text() çalışır:
   Regex: ['"]...['"]{1,40}['"]
   Match: 'Sabır' (tırnak dahil)
   Replace: "a glowing ancient symbol"
   Sonuç: "child discovers a glowing ancient symbolmızı in the ancient temple"
                                                ^^^^^ Türkçe ek yapışık kaldı!

3. _sanitize_v3_prompt_text() çalışır:
   Fix regex: "a glowing ancient symbols" → ✓ düzeltir
   Ama: "a glowing ancient symbolmızı" → ✗ YAKALAMAZ

4. Final prompt Fal.ai'ye gider: "...a glowing ancient symbolmızı..."
                                                              ^^^ BOZUK
```

**Çözüm:** Regex'e (1) boundary lookbehind, (2) Türkçe ek lookahead tüketme ekle + savunma katmanı olarak `_sanitize_v3_prompt_text`'i genişlet.
