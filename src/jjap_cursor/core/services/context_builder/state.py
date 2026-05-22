"""Mutable state for context builder operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ContextBuilderState:
    """Holds project root and token budget for context assembly."""

    project_root: Path
    max_tokens: int = 4000
