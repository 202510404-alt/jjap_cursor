"""Scan artifact types for file_scanner package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ScanArtifacts:
    """Container for scan outputs produced from Python source files."""

    skeletons: dict[str, str]
    symbol_table: dict[str, list[dict[str, Any]]]
