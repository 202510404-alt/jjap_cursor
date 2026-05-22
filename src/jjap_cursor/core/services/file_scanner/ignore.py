"""Gitignore-aware project file iteration for scanning."""

from __future__ import annotations

import os
from fnmatch import fnmatch
from pathlib import Path


def load_gitignore_patterns(project_root: Path) -> list[str]:
    """Parse basic .gitignore rules from project root."""
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return []

    patterns: list[str] = []
    for raw in gitignore_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        normalized = line.lstrip("/")
        if normalized:
            patterns.append(normalized)
    return patterns


def is_ignored(path: Path, project_root: Path, ignore_patterns: list[str]) -> bool:
    """Check if a path is ignored by baseline or .gitignore patterns."""
    rel = path.relative_to(project_root).as_posix()
    parts = set(path.parts)

    if ".git" in parts or "__pycache__" in parts:
        return True
    if rel.startswith("venv/") or rel.startswith(".venv/") or rel.startswith("node_modules/"):
        return True

    for pattern in ignore_patterns:
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            if rel.startswith(f"{dir_pattern}/"):
                return True
        elif "/" in pattern and fnmatch(rel, pattern):
            return True
        elif fnmatch(path.name, pattern):
            return True
    return False


def matches_directory_ignore(rel_root: str, dirname: str, ignore_patterns: list[str]) -> bool:
    """Check if a child directory matches configured ignore patterns."""
    if not ignore_patterns:
        return False
    rel_dir = f"{rel_root}/{dirname}" if rel_root else dirname
    for pattern in ignore_patterns:
        candidate = pattern.rstrip("/")
        if fnmatch(rel_dir, candidate) or fnmatch(dirname, candidate):
            return True
    return False


def iter_python_files(project_root: Path, ignore_patterns: list[str]) -> list[Path]:
    """Return Python files excluded by .gitignore-aware filtering."""
    files: list[Path] = []
    for root, dirs, filenames in os.walk(project_root):
        root_path = Path(root)
        rel_root = root_path.relative_to(project_root).as_posix() if root_path != project_root else ""

        # Hard-stop directories that must always be ignored.
        dirs[:] = [d for d in dirs if d not in {".git", "venv", "__pycache__"}]
        dirs[:] = [d for d in dirs if not matches_directory_ignore(rel_root, d, ignore_patterns)]

        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            file_path = root_path / filename
            if not is_ignored(file_path, project_root, ignore_patterns):
                files.append(file_path)
    return sorted(files)
