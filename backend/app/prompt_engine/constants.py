"""Backward-compatibility shim — re-exports from app.prompt_engine.__init__.

All definitions live in app.prompt_engine.__init__ (which itself proxies app.prompt).
This module exists solely so that ``from app.prompt_engine.constants import X``
keeps working without duplicating any logic.
"""

# Re-export everything from the parent package — single source of truth
from app.prompt_engine import (  # noqa: F401
    ANTI_ANIME_NEGATIVE,
    ANTI_PHOTO_FACE,
    ANTI_REALISTIC_NEGATIVE,
    BASE_NEGATIVE,
    BODY_PROPORTION,
    BODY_PROPORTION_DIRECTIVE,
    COVER_ONLY_PHRASES,
    DEFAULT_COVER_TEMPLATE,
    DEFAULT_COVER_TEMPLATE_EN,
    DEFAULT_INNER_TEMPLATE,
    DEFAULT_INNER_TEMPLATE_EN,
    INNER_ONLY_PHRASES,
    LIKENESS_HINT,
    MAX_BODY_CHARS,
    MAX_PROMPT_CHARS,
    NEGATIVE_PROMPT,
    NO_FAMILY_BANNED_WORDS_TR,
    SHARPNESS,
    SHARPNESS_BACKGROUND_DIRECTIVE,
    STRICT_NEGATIVE_ADDITIONS,
    STYLE_NEGATIVE_DEFAULTS,
    STYLE_PULID_CONFIGS,
    STYLE_PULID_WEIGHTS,
    STYLES,
    StyleConfig,
    StylePuLIDConfig,
    get_pulid_config_for_style,
    get_pulid_weight_for_style,
    get_style_anchor,
    get_style_config,
    get_style_leading_prefix,
    get_style_negative_default,
    get_style_specific_negative,
    get_strict_negative_additions,
    resolve_style,
)

# Additional aliases only used via constants.py path
LIKENESS_HINT_WHEN_REFERENCE = LIKENESS_HINT
MAX_FAL_PROMPT_CHARS = MAX_PROMPT_CHARS
MAX_VISUAL_PROMPT_BODY_CHARS = MAX_BODY_CHARS
ANTI_PHOTO_FACE_NEGATIVE = ANTI_PHOTO_FACE
DEFAULT_STYLE = STYLES["default"]
GLOBAL_NEGATIVE_PROMPT_EN = BASE_NEGATIVE

# Cinematic pattern — used by _visual_composer
import re  # noqa: E402

CINEMATIC_LENS_TERMS: list[str] = [r"\bcinematic\b", r"\blens\b", r"\bfilm still\b"]
CINEMATIC_PATTERN = re.compile("|".join(f"({p})" for p in CINEMATIC_LENS_TERMS), re.IGNORECASE)
INNER_PAGE_STRIP_TERMS: list[str] = [r"\bChildren's\s+book\s+cover\b"]
INNER_PAGE_STRIP_PATTERN = re.compile("|".join(f"({p})" for p in INNER_PAGE_STRIP_TERMS), re.IGNORECASE)
REQUIRED_RESOLVED_PLACEHOLDERS = ("{scene_description}", "{child_name}", "{clothing_description}", "{story_title}")
