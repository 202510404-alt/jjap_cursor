"""Scan all eligible Python files and build skeleton/symbol artifacts."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .ignore import iter_python_files, load_gitignore_patterns
from .skeleton import extract_skeleton
from .symbols import extract_symbols, populate_used_by
from .types import ScanArtifacts


def scan_project(project_root: Path) -> ScanArtifacts:
    """Scan all eligible Python files and return generated artifacts."""
    ignore_patterns = load_gitignore_patterns(project_root)
    skeletons: dict[str, str] = {}
    symbols: list[dict[str, Any]] = []

    for file_path in iter_python_files(project_root, ignore_patterns):
        source = file_path.read_text(encoding="utf-8")
        module = ast.parse(source)
        rel_path = file_path.relative_to(project_root).as_posix()

        skeletons[rel_path] = extract_skeleton(module)
        symbols.extend(extract_symbols(module, rel_path))

    populate_used_by(symbols)
    return ScanArtifacts(skeletons=skeletons, symbol_table={"symbols": symbols})
