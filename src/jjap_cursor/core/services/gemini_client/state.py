"""Mutable state for Gemini client (API key and cached model)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeminiClientState:
    """Holds API credentials and lazily initialized GenerativeModel."""

    api_key: str
    _plan_model: Any = field(default=None, repr=False)
    _patch_model: Any = field(default=None, repr=False)
