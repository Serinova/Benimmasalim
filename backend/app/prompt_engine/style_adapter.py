"""Backward-compatibility shim for style_adapter."""

from app.prompt_engine import adapt_style, get_style_instructions_for_prompt  # noqa: F401

_STYLE_DEFS = {}
