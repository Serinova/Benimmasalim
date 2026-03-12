"""Core project-wide constants.

Central source of truth for magic numbers and fallback values.
Import from here rather than hardcoding.
"""

# ---------------------------------------------------------------------------
# Page count
# ---------------------------------------------------------------------------
# Used as the **last-resort** fallback when neither the Scenario, linked Product,
# nor the explicit Product provides a page count.  Every call-site that previously
# hardcoded ``16`` now references this constant, making the fallback transparent
# and easy to change in one place.
DEFAULT_FALLBACK_PAGE_COUNT: int = 16
