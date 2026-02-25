"""Backward-compatibility shim for constants — doğrudan app.prompt'tan import eder."""
from app.prompt.negative_builder import ANTI_PHOTO_FACE, BASE_NEGATIVE
from app.prompt.sanitizer import MAX_BODY_CHARS, MAX_PROMPT_CHARS
from app.prompt.style_config import STYLES, StyleConfig, resolve_style
from app.prompt.templates import (
    BODY_PROPORTION,
    DEFAULT_COVER_TEMPLATE,
    DEFAULT_INNER_TEMPLATE,
    LIKENESS_HINT,
    SHARPNESS,
)

NEGATIVE_PROMPT = BASE_NEGATIVE
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

COVER_ONLY_PHRASES = ("book cover illustration", "title space at top", "space for title at top", "children's book cover")
INNER_ONLY_PHRASES = ("wide horizontal", "leave empty space at bottom", "empty space at bottom for captions (no text in image)")

DEFAULT_STYLE = STYLES["default"]
STYLE_NEGATIVE_DEFAULTS: dict[str, str] = {s.key: s.negative for s in STYLES.values()}

ANTI_PHOTO_FACE_NEGATIVE = ANTI_PHOTO_FACE

# Cinematic pattern for backward compat
import re

CINEMATIC_LENS_TERMS: list[str] = [r"\bcinematic\b", r"\blens\b", r"\bfilm still\b"]
CINEMATIC_PATTERN = re.compile("|".join(f"({p})" for p in CINEMATIC_LENS_TERMS), re.IGNORECASE)
INNER_PAGE_STRIP_TERMS: list[str] = [r"\bChildren's\s+book\s+cover\b"]
INNER_PAGE_STRIP_PATTERN = re.compile("|".join(f"({p})" for p in INNER_PAGE_STRIP_TERMS), re.IGNORECASE)
REQUIRED_RESOLVED_PLACEHOLDERS = ("{scene_description}", "{child_name}", "{clothing_description}", "{story_title}")


class StylePuLIDConfig:
    def __init__(self, id_weight: float = 1.0, start_step: int = 1, true_cfg: float = 1.0):
        self.id_weight = id_weight
        self.start_step = start_step
        self.true_cfg = true_cfg


STYLE_PULID_CONFIGS: dict[str, StylePuLIDConfig] = {}
for _s in STYLES.values():
    STYLE_PULID_CONFIGS[_s.key] = StylePuLIDConfig(id_weight=_s.id_weight, start_step=_s.start_step, true_cfg=_s.true_cfg)
STYLE_PULID_CONFIGS.update({
    "disney": StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0),
    "3d": StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0),
    "cinematic": StylePuLIDConfig(id_weight=1.0, start_step=2, true_cfg=1.0),
    "sulu boya": StylePuLIDConfig(id_weight=1.3, start_step=1, true_cfg=1.2),
    "suluboya": StylePuLIDConfig(id_weight=1.3, start_step=1, true_cfg=1.2),
    "ghibli": StylePuLIDConfig(id_weight=1.2, start_step=0, true_cfg=1.5),
    "soft pastel": StylePuLIDConfig(id_weight=1.3, start_step=1, true_cfg=1.2),
    "yumusak pastel": StylePuLIDConfig(id_weight=1.3, start_step=1, true_cfg=1.2),
})

STYLE_PULID_WEIGHTS: dict[str, float] = {k: v.id_weight for k, v in STYLE_PULID_CONFIGS.items()}


def get_style_specific_negative(style_modifier: str) -> str:
    return resolve_style(style_modifier).negative


def get_pulid_config_for_style(style_modifier: str) -> StylePuLIDConfig:
    s = resolve_style(style_modifier)
    return StylePuLIDConfig(id_weight=s.id_weight, start_step=s.start_step, true_cfg=s.true_cfg)


def get_pulid_weight_for_style(style_modifier: str) -> float:
    return resolve_style(style_modifier).id_weight


def get_style_config(style_modifier: str = "") -> StyleConfig:
    return resolve_style(style_modifier)


def get_style_anchor(style_modifier: str = "") -> str:
    return resolve_style(style_modifier).anchor


def get_style_leading_prefix(style_modifier: str = "") -> str:
    return resolve_style(style_modifier).leading_prefix


def get_style_negative_default(style_modifier: str = "") -> str:
    return resolve_style(style_modifier).negative


def get_strict_negative_additions(style_modifier: str = "") -> str:
    return STRICT_NEGATIVE_ADDITIONS
