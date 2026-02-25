"""Build/runtime metadata helpers."""

from __future__ import annotations

import os
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def get_commit_hash() -> str:
    """Return commit hash from env or git, best-effort."""
    for key in ("COMMIT_SHA", "GIT_COMMIT", "SHORT_SHA", "K_REVISION"):
        val = (os.getenv(key) or "").strip()
        if val:
            return val

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=1.0,
        )
        git_sha = out.decode("utf-8", errors="ignore").strip()
        if git_sha:
            return git_sha
    except Exception:
        pass

    return "unknown"
