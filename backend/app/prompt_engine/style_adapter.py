"""Style adapter — stub module.

Provides the adapt_style() function expected by
_story_writer.py (line 473).  Converts a visual_style string
into a mapping dict used by visual prompt builder/validator.

Currently a minimal stub.
"""

from __future__ import annotations

from typing import Any


def adapt_style(visual_style: str = "") -> dict[str, Any]:
    """Convert a visual style string to a structured mapping.

    Parameters
    ----------
    visual_style : str
        Free-form style description, e.g. "children's book illustration, soft colors".

    Returns
    -------
    dict[str, Any]
        Style mapping with keys like 'base_style', 'color_palette', 'medium'.
    """
    # Simple keyword extraction — will be expanded later
    style_lower = (visual_style or "").lower()

    return {
        "base_style": visual_style or "children's book illustration",
        "color_palette": "warm" if "warm" in style_lower else "vibrant",
        "medium": "digital illustration",
        "raw_style": visual_style,
    }
