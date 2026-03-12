"""Backward-compatibility shim — tüm eski import'ları yeni app.prompt'a yönlendirir.

Bu modül geçiş döneminde mevcut kodun kırılmaması için var.
Tüm servisler yeni sisteme migrate edildikten sonra silinecek.
"""

import logging as _logging

_logging.getLogger(__name__).debug("app.prompt_engine is deprecated. Use app.prompt instead.")

from app.prompt import (
    ANTI_PHOTO_FACE,
    BASE_NEGATIVE,
    BODY_PROPORTION,
    COMPOSITION_RULES,
    DEFAULT_COVER_TEMPLATE,
    DEFAULT_INNER_TEMPLATE,
    LIKENESS_HINT,
    MAX_BODY_CHARS,
    MAX_PROMPT_CHARS,
    NO_FAMILY_BANNED_WORDS_TR,
    SHARPNESS,
    STORY_NO_FIRST_DEGREE_FAMILY_TR,
    STYLES,
    BookContext,
    PromptComposer,
    PromptResult,
    StyleConfig,
    build_cover_prompt,
    build_negative,
    build_page_prompt,
    compose_story_prompt,
    normalize_clothing,
    normalize_location,
    resolve_style,
    sanitize,
    truncate_safe,
)
from app.prompt.negative_builder import BASE_NEGATIVE as NEGATIVE_PROMPT
from app.prompt.style_config import resolve_style as get_style_config

__all__ = [
    "ANTI_PHOTO_FACE",
    "BASE_NEGATIVE",
    "BODY_PROPORTION",
    "COMPOSITION_RULES",
    "DEFAULT_COVER_TEMPLATE",
    "DEFAULT_INNER_TEMPLATE",
    "LIKENESS_HINT",
    "MAX_BODY_CHARS",
    "MAX_PROMPT_CHARS",
    "NO_FAMILY_BANNED_WORDS_TR",
    "SHARPNESS",
    "STORY_NO_FIRST_DEGREE_FAMILY_TR",
    "STYLES",
    "BookContext",
    "PromptComposer",
    "PromptResult",
    "StyleConfig",
    "build_cover_prompt",
    "build_negative",
    "build_page_prompt",
    "compose_story_prompt",
    "normalize_clothing",
    "normalize_clothing_description",
    "normalize_location",
    "resolve_style",
    "sanitize",
    "truncate_safe",
    "NEGATIVE_PROMPT",
    "get_style_config",
]

# ── Eski isimlendirme uyumluluğu ─────────────────────────────────────────────
GLOBAL_NEGATIVE_PROMPT_EN = BASE_NEGATIVE
STRICT_NEGATIVE_ADDITIONS = "text overlay, logo, letters on image, head rotated"
ANTI_ANIME_NEGATIVE = "anime, cartoon, illustration, 2d, flat colors, cel shaded, manga style, animated, drawing, sketch, painted"
ANTI_REALISTIC_NEGATIVE = "photorealistic, realistic, photography, studio lighting, real person, hyperrealistic"
DEFAULT_COVER_TEMPLATE_EN = DEFAULT_COVER_TEMPLATE
DEFAULT_INNER_TEMPLATE_EN = DEFAULT_INNER_TEMPLATE
LIKENESS_HINT_WHEN_REFERENCE = LIKENESS_HINT
MAX_FAL_PROMPT_CHARS = MAX_PROMPT_CHARS
MAX_VISUAL_PROMPT_BODY_CHARS = MAX_BODY_CHARS
BODY_PROPORTION_DIRECTIVE = BODY_PROPORTION
SHARPNESS_BACKGROUND_DIRECTIVE = SHARPNESS


class VisualPromptValidationError(Exception):
    """Görsel prompt doğrulama hatası."""
    pass


class StylePuLIDConfig:
    """PuLID config uyumluluk wrapper."""
    def __init__(self, id_weight: float = 1.0, start_step: int = 1, true_cfg: float = 1.0):
        self.id_weight = id_weight
        self.start_step = start_step
        self.true_cfg = true_cfg


STYLE_PULID_CONFIGS: dict[str, StylePuLIDConfig] = {
    s.key: StylePuLIDConfig(id_weight=s.id_weight, start_step=s.start_step, true_cfg=s.true_cfg)
    for s in STYLES.values()
}
STYLE_PULID_CONFIGS["default"] = StylePuLIDConfig(id_weight=1.0, start_step=1, true_cfg=1.0)
STYLE_PULID_CONFIGS["pixar"] = StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0)
STYLE_PULID_CONFIGS["disney"] = StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0)
STYLE_PULID_CONFIGS["3d"] = StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0)
STYLE_PULID_CONFIGS["cinematic"] = StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0)
STYLE_PULID_CONFIGS["watercolor"] = StylePuLIDConfig(id_weight=1.0, start_step=1, true_cfg=1.2)
STYLE_PULID_CONFIGS["sulu boya"] = StylePuLIDConfig(id_weight=1.0, start_step=1, true_cfg=1.2)
STYLE_PULID_CONFIGS["anime"] = StylePuLIDConfig(id_weight=1.0, start_step=0, true_cfg=1.5)
STYLE_PULID_CONFIGS["ghibli"] = StylePuLIDConfig(id_weight=1.0, start_step=0, true_cfg=1.5)
STYLE_PULID_CONFIGS["soft pastel"] = StylePuLIDConfig(id_weight=1.0, start_step=1, true_cfg=1.2)

STYLE_PULID_WEIGHTS: dict[str, float] = {k: v.id_weight for k, v in STYLE_PULID_CONFIGS.items()}
STYLE_NEGATIVE_DEFAULTS: dict[str, str] = {s.key: s.negative for s in STYLES.values()}

COVER_ONLY_PHRASES = ("book cover illustration", "title space at top", "space for title at top", "children's book cover")
INNER_ONLY_PHRASES = ("wide horizontal", "leave empty space at bottom", "empty space at bottom for captions (no text in image)")


# ── Eski fonksiyon uyumluluğu ────────────────────────────────────────────────
def get_style_specific_negative(style_modifier: str) -> str:
    s = resolve_style(style_modifier)
    return s.negative


def get_pulid_config_for_style(style_modifier: str) -> StylePuLIDConfig:
    s = resolve_style(style_modifier)
    return StylePuLIDConfig(id_weight=s.id_weight, start_step=s.start_step, true_cfg=s.true_cfg)


def get_pulid_weight_for_style(style_modifier: str) -> float:
    return resolve_style(style_modifier).id_weight


def get_style_anchor(style_modifier: str = "") -> str:
    return resolve_style(style_modifier).anchor


def get_style_leading_prefix(style_modifier: str = "") -> str:
    return resolve_style(style_modifier).leading_prefix


def get_style_negative_default(style_modifier: str = "") -> str:
    return resolve_style(style_modifier).negative


def get_strict_negative_additions(style_modifier: str = "") -> str:
    return STRICT_NEGATIVE_ADDITIONS


def build_negative_prompt(
    style_modifier: str = "",
    base_negative: str = "",
    *,
    strict: bool = False,
    style_negative_from_db: str | None = None,
    child_gender: str | None = None,
    has_reference_photo: bool = False,
) -> str:
    """Eski negatif prompt builder uyumluluğu."""
    parts = [base_negative or NEGATIVE_PROMPT]
    s = resolve_style(style_modifier)
    parts.append(style_negative_from_db or s.negative)
    if has_reference_photo:
        parts.append(ANTI_PHOTO_FACE)
    return ", ".join(p for p in parts if p)


def normalize_clothing_description(raw: str) -> str:
    return normalize_clothing(raw)


def sanitize_visual_prompt(prompt: str, max_length: int | None = None, is_cover: bool = False) -> str:
    return sanitize(prompt, is_cover=is_cover, max_length=max_length)


def truncate_safe_2d(text: str, max_length: int = 1200) -> str:
    return truncate_safe(text, max_length)


def compose_visual_prompt(
    scene_description: str,
    *,
    style_text: str = "",
    is_cover: bool = False,
    story_title: str = "",
    clothing_description: str = "",
    child_name: str = "",
    child_age: int = 6,
    child_gender: str = "",
    face_reference_url: str = "",
    template_en: str | None = None,
    base_negative: str = "",
    style_negative_from_db: str | None = None,
    **kwargs,
) -> tuple[str, str]:
    """Eski compose_visual_prompt uyumluluğu — yeni sisteme yönlendirir."""
    effective_style = style_text or kwargs.get("style_prompt_en", "") or kwargs.get("style_modifier", "")
    leading_prefix_override = kwargs.get("leading_prefix_override")
    style_block_override = kwargs.get("style_block_override")

    resolved = resolve_style(effective_style)

    if leading_prefix_override or style_block_override:
        resolved = StyleConfig(
            key=resolved.key,
            anchor=resolved.anchor,
            leading_prefix=leading_prefix_override or resolved.leading_prefix,
            style_block=style_block_override or resolved.style_block,
            cover_prefix=resolved.cover_prefix,
            cover_suffix=resolved.cover_suffix,
            inner_prefix=resolved.inner_prefix,
            inner_suffix=resolved.inner_suffix,
            negative=resolved.negative,
            id_weight=resolved.id_weight,
            start_step=resolved.start_step,
            true_cfg=resolved.true_cfg,
        )

    ctx = BookContext(
        child_name=child_name,
        child_age=child_age,
        child_gender=child_gender,
        style=resolved,
        style_modifier_raw=effective_style,
        character_description=kwargs.get("character_description", ""),
        clothing_description=clothing_description,
        hair_description=kwargs.get("hair_description", ""),
        face_reference_url=face_reference_url,
        story_title=story_title,
    )
    composer = PromptComposer(
        ctx,
        cover_template=template_en if is_cover else None,
        inner_template=template_en if not is_cover else None,
    )
    if is_cover:
        result = composer.compose_cover(scene_description)
    else:
        result = composer.compose_page(scene_description, page_number=1)
    return result.prompt, result.negative_prompt


def get_display_visual_prompt(prompt: str, *args, **kwargs) -> str:
    """Admin panelde görüntüleme için prompt."""
    return prompt[:500] + "..." if len(prompt) > 500 else prompt


def render_template(template: str, **kwargs) -> str:
    """Template render uyumluluğu."""
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def personalize_style_prompt(style_modifier: str, child_name: str = "", child_age: int = 6, child_gender: str = "", **kwargs) -> str:
    """Stil prompt'unu kişiselleştirir."""
    if not style_modifier:
        return style_modifier
    result = style_modifier
    if child_name and "{child_name}" in result:
        result = result.replace("{child_name}", child_name)
    if "{child_age}" in result:
        result = result.replace("{child_age}", str(child_age))
    if child_gender and "{child_gender}" in result:
        result = result.replace("{child_gender}", child_gender)
    return result


# ── Stub dataclass/fonksiyonlar — eski V3 pipeline bileşenleri ───────────────
class FluxPromptBuilder:
    """V3 FluxPromptBuilder uyumluluk wrapper'ı."""
    @staticmethod
    def get_style_config(style_modifier: str = "") -> StyleConfig:
        return resolve_style(style_modifier)

    @staticmethod
    def build_cover_prompt(ctx, title: str = "") -> str:
        """Legacy cover prompt builder — full style + composition."""
        style_modifier = getattr(ctx, "style_modifier", "") or getattr(ctx, "visual_style", "") or ""
        child_name = getattr(ctx, "child_name", "")
        child_gender = getattr(ctx, "child_gender", "")
        clothing = getattr(ctx, "clothing_prompt", "") or getattr(ctx, "clothing_description", "")
        face_url = getattr(ctx, "child_face_url", "")

        hair = getattr(ctx, "hair_style", "") or getattr(ctx, "hair_description", "")
        book_ctx = BookContext.build(
            child_name=child_name or "",
            child_age=getattr(ctx, "child_age", 7),
            child_gender=child_gender or "",
            style_modifier=style_modifier,
            clothing_description=clothing,
            hair_description=hair,
            face_reference_url=face_url,
            story_title=title,
        )
        composer = PromptComposer(book_ctx)
        result = composer.compose_cover(f"A magical children's book cover for '{title}'" if title else "A magical adventure scene")
        return result.prompt

    @staticmethod
    def convert_tags_to_natural(prompt: str) -> str:
        return prompt


class PromptContext:
    """Eski PromptContext uyumluluk stub'ı."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CompanionSpec:
    """Yardımcı karakter bilgisi."""
    def __init__(self, name: str = "", species: str = "", appearance: str = ""):
        self.name = name
        self.species = species
        self.appearance = appearance


class OutfitSpec:
    """Kıyafet bilgisi."""
    def __init__(self, description_en: str = "", hair_style_en: str = ""):
        self.description_en = description_en
        self.hair_style_en = hair_style_en


class CharacterBible:
    def __init__(self, **kwargs):
        self.child_name = kwargs.get("child_name", "")
        self.child_age = kwargs.get("child_age", 6)
        self.child_gender = kwargs.get("child_gender", "erkek")
        self.child_description = kwargs.get("child_description", "")
        self.fixed_outfit = kwargs.get("fixed_outfit", "")
        self.hair_style = kwargs.get("hair_style", "")
        self.outfit_en = kwargs.get("fixed_outfit", "")
        _name = self.child_name or "child"
        _age = self.child_age
        self.identity_anchor = f"a {_age}-year-old child named {_name}"
        self.identity_anchor_minimal = f"{_name}, {_age}yo"
        self.appearance_tokens = kwargs.get("child_description", "")
        self.negative_tokens = ""
        _parts = [self.identity_anchor]
        if self.hair_style:
            _parts.append(f"with {self.hair_style}")
        if self.fixed_outfit:
            _parts.append(f"wearing {self.fixed_outfit}")
        self.prompt_block = ", ".join(_parts)
        self.prompt_block_for_pulid = self.prompt_block
        _comp_name = kwargs.get("companion_name", "")
        if _comp_name:
            self.companion = CompanionSpec(
                name=_comp_name,
                species=kwargs.get("companion_species", ""),
                appearance=kwargs.get("companion_appearance", ""),
            )
        else:
            self.companion = None


class ScenarioBible:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class StyleMapping:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "default")
        self.anchor = kwargs.get("anchor", "")
        self.negative = kwargs.get("negative", "")
        for k, v in kwargs.items():
            setattr(self, k, v)


class StoryValidationReport:
    def __init__(self):
        self.issues = []
        self.failures = []
        self.is_valid = True
        self.all_passed = True


class VisualValidationReport:
    def __init__(self):
        self.passed = True
        self.issues = []
        self.auto_fixed = []


class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.passed = True
        self.messages = []
        self.auto_fixed = []


def build_character_bible(**kwargs) -> CharacterBible:
    return CharacterBible(**kwargs)


def get_scenario_bible(*args, **kwargs) -> ScenarioBible:
    return ScenarioBible()


def normalize_location_key_for_anchors(location: str) -> str:
    return (location or "").lower().strip()


def adapt_style(visual_style: str = "", *args, **kwargs) -> StyleMapping:
    s = resolve_style(visual_style)
    return StyleMapping(name=s.key, anchor=s.anchor, negative=s.negative)


def get_style_instructions_for_prompt(*args, **kwargs) -> str:
    return ""


def build_blueprint_task_prompt(*args, **kwargs) -> str:
    return ""


def build_page_task_prompt(
    *,
    blueprint_json: dict | None = None,
    child_name: str = "",
    child_age: int = 7,
    child_description: str = "",
    visual_style: str = "",
    style_instructions: str = "",
    location_display_name: str = "",
    location_constraints: str = "",
    magic_items: list | None = None,
    page_count: int = 16,
    skip_visual_prompts: bool = False,
    companion_info: str = "",
    **_kwargs,
) -> str:
    """Build the PASS-1 task prompt for story page generation.

    Constructs a detailed prompt that includes the blueprint and all context
    needed for Gemini to generate full story pages with Turkish text and
    optionally English visual prompts.
    
    Args:
        skip_visual_prompts: If True, only generate text_tr (no image_prompt_en)
    """
    import json as _json

    magic_str = ""
    if magic_items:
        magic_str = f"\nSihirli eşyalar: {', '.join(magic_items)}"

    location_str = ""
    if location_constraints:
        location_str = f"\nLOKASYON REHBERİ (Aşağıdaki detaylardan sahneye uygun olanları seçip görsel tanıma yedir):\n{location_constraints}"

    blueprint_str = ""
    if blueprint_json:
        try:
            blueprint_str = _json.dumps(blueprint_json, ensure_ascii=False, indent=2)
        except Exception:
            blueprint_str = str(blueprint_json)

    # Two-phase generation: story text only or full (text + visual prompts)
    if skip_visual_prompts:
        output_format = f"""### ÇIKTI FORMATI
Tam olarak {page_count} sayfa üret. JSON array formatında:
```json
[
  {{
    "page": 1,
    "text_tr": "Türkçe hikaye metni (50-100 kelime, çocuğa uygun, akıcı)"
  }},
  ...
]
```"""
        rules = f"""### KURALLAR
1. HER sayfa için {child_name} isimli çocuğu merkeze al
2. text_tr: Türkçe, akıcı, çocuk diline uygun, 50-100 kelime
3. Blueprint'teki scene_goal, role, emotional_state alanlarını kullan
4. Sayfa 1 hikayenin GİRİŞ sahnesini içerir (kapak/karşılama sayfalarından SONRAKİ ilk hikaye sayfası)
5. Son sayfa ({page_count}) için mutlu bir kapanış yaz

⛔ page 0 DÖNDÜRME! Kapak sayfası (page 0) SİSTEM tarafından ayrıca üretilir. Sen SADECE page 1'den page {page_count}'e kadar üret.
TAM OLARAK {page_count} SAYFA ÜRET. Daha az veya fazla sayfa YASAK."""
    else:
        output_format = f"""### ÇIKTI FORMATI
Tam olarak {page_count} sayfa üret. JSON array formatında:
```json
[
  {{
    "page": 1,
    "text_tr": "Türkçe hikaye metni (50-100 kelime, çocuğa uygun, akıcı)",
    "image_prompt_en": "Kısa görsel sahne tanımı. Çocuğun saç/göz/ten rengini kendin UYDURMA ama Görünüm bilgisindeki tanımı AYNEN kullan. SADECE EYLEM VE MEKAN. LOKASYONU (örn: {location_display_name}) HER SAYFADA MUTLAKA BELİRT."
  }},
  ...
]
```"""
        rules = f"""### KURALLAR
1. HER sayfa için {child_name} isimli çocuğu merkeze al
2. text_tr: Türkçe, akıcı, çocuk diline uygun, 50-100 kelime
3. image_prompt_en: Kısa görsel sahne tanımı. Çocuğun saç/göz/ten rengini kendin UYDURMA — Görünüm bilgisinde verilmişse AYNEN kullan, verilmemişse HİÇ YAZMA. Kıyafet bilgisini de kendin uydurma. METİN İLE BİREBİR UYUMLU OLSUN (ör. metinde kelebek varsa promptta kesinlikle butterfly olmalı). SADECE YAPTIĞI EYLEMİ VE MEKANI YAZ.
4. Blueprint'teki scene_goal, role, emotional_state alanlarını kullan
5. LOKASYON DEVAMLILIĞI (ÇOK ÖNEMLİ): {location_display_name or "hikaye ortamı"} — Yapay zeka her resmi bağımsız çizer. Bu yüzden HER SAYFANIN `image_prompt_en` kısmında {location_display_name or "hikaye ortamı"} mekanını KESİNLİKLE tekrar et. DİKKAT: Çocuğun mekanla ilişkisini mantıklı kur! Dışarıdaysa "in front of...", içerisindeyse "inside the ancient stone walls of...", tepesindeyse "on the balcony of..." gibi konumunu netleştir ki absürt görüntüler oluşmasın.
6. Sayfa 1 hikayenin GİRİŞ sahnesini içerir (kapak/karşılama sayfalarından SONRAKİ ilk hikaye sayfası)
7. Son sayfa ({page_count}) için mutlu bir kapanış yaz

⛔ page 0 DÖNDÜRME! Kapak sayfası (page 0) SİSTEM tarafından ayrıca üretilir. Sen SADECE page 1'den page {page_count}'e kadar üret.
TAM OLARAK {page_count} SAYFA ÜRET. Daha az veya fazla sayfa YASAK."""

    companion_str = ""
    if companion_info:
        companion_str = f"\n\n### Yardımcı Karakter (Companion)\n{companion_info}\n⚠️ Bu karakterin görünümü TÜM SAYFALARDA AYNI OLMALI. Renk, boyut ve tür DEĞİŞMEYECEK."

    return f"""## GÖREV: Hikaye Sayfaları Üret

### Çocuk Bilgileri
- İsim: {child_name}
- Yaş: {child_age}
{f"- Görünüm: {child_description}" if child_description else ""}
{f"- Konum/Lokasyon: {location_display_name}" if location_display_name else ""}
{magic_str}{companion_str}

### Görsel Stil
{visual_style or "Çocuk kitabı illüstrasyon stili"}
{style_instructions or ""}
{location_str}

### Hikaye İskeleti (Blueprint)
```json
{blueprint_str}
```

{output_format}

{rules}"""


def enhance_all_pages(*args, **kwargs):
    from app.prompt_engine.visual_prompt_builder import enhance_all_pages as _real_enhance
    return _real_enhance(*args, **kwargs)


def build_enhanced_negative(*args, **kwargs) -> str:
    return NEGATIVE_PROMPT


def compose_enhanced_prompt(*args, **kwargs) -> str:
    return ""


def extract_visual_beat(*args, **kwargs):
    return None


def lint_prompt_corruption(*args, **kwargs) -> list:
    return []


def run_qa_checks(*args, **kwargs) -> dict:
    return {"passed": True, "issues": []}


LOCATION_ANCHORS: dict = {}
BLUEPRINT_SYSTEM_PROMPT = ""
PAGE_GENERATION_SYSTEM_PROMPT = """Sen ödüllü bir çocuk kitabı yazarı ve illüstrasyon yönetmenisin.

Görevin:
1. Verilen hikaye iskeletini (blueprint) kullanarak tam hikaye sayfaları üretmek
2. Her sayfa için Türkçe hikaye metni (text_tr) yazmak
3. Her sayfa için görsel sahne tanımı (image_prompt_en) oluşturmak (Gemini Imagen 3 için kısa ve öz)

TÜRKÇE METİN KURALLARI:
- 5-7 yaş çocuklarına uygun, sade Türkçe kullan
- Her cümle kısa ve anlaşılır olsun
- Çocuğun duygularını ve keşiflerini ön plana çıkar
- Her sayfada aksiyonu ilerlet, tekrar etme
- SUBLİMİNAL DEĞER AKTARIMI (CRITICAL): Çocuğa özgüven, cesaret, empati gibi değerleri ASLA doğrudan öğüt vererek ("şunu öğrenmeli", "böyle yapmalı", "anlamıştı") anlatma. Mesajları YALNIZCA karakterin cesur eylemleri, metaforlar ve hikayenin doğal akışı üzerinden, dolaylı (subliminal) bir dille hissettir.

GÖRSEL SAHNE TANIMLARI (İngilizce, Gemini Imagen 3 için kısa ve öz):
- LOKASYON DEVAMLILIĞI: Yapay zeka her resmi sıfırdan çizer. Bu yüzden ANA LOKASYONU (örneğin Galata Kulesi, Kapadokya vb.) her sayfanın `image_prompt_en` kısmında tekrar et. DİKKAT: Çocuğun mekanla ilişkisini doğru kur! Dışarıdaysa "in front of Galata Tower", içerisindeyse "inside the ancient stone walls of Galata Tower", tepesindeyse "on the balcony of Galata Tower" gibi detaylandır ki mekanın içinde tekrar aynı mekan mantıksızlığı (inception) oluşmasın.
- METİN VE GÖRSEL UYUMU (CRITICAL): `text_tr` metninde hangi hayvanlar, eşyalar veya olaylar varsa, `image_prompt_en` kısmında KESİNLİKLE onlara yer ver. (Örn: Metinde "kartal" diyorsa, görsel tanımında "butterfly" veya alakasız şeyler YAZMA, kesinlikle "eagle" yaz).
- Çocuğun NE YAPTIĞINI netleştir (eylem/action odaklı). SADECE EYLEM VE MEKAN BELİRT.
- Ortamı (arka plan, ışık, renkler) tanımla
- Sihirli unsurları veya önemli objeleri dahil et
- KARAKTER TUTARLILIĞI: Çocuğun saç rengini, göz rengini, ten rengini kendin UYDURMA. Eğer "Çocuk Bilgileri" bölümünde Görünüm bilgisi verilmişse o bilgiyi HER SAYFADA AYNEN kullan. Verilmemişse hiç yazma — sistem sonradan ekleyecek. Kıyafet bilgisini de kendin uydurma.
- YARDIMCI KARAKTER TUTARLILIĞI: Eğer bir yardımcı karakter (companion) tanımlanmışsa, bu karakterin rengini, boyutunu ve türünü TÜM SAYFALARDA AYNI yaz. Kendin değiştirme."""


# Enum/dataclass stubs for backward compatibility
class ShotPlan:
    pass

class ShotType:
    pass

class CameraAngle:
    pass

class ActionType:
    pass

class VisualBeat:
    pass

class VisualValidationResult:
    def __init__(self):
        self.is_valid = True
        self.passed = True
        self.messages = []
        self.auto_fixed = []
