"""File hashing utilities for scan output metadata."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_of_file(path: Path) -> str:
    """Return SHA256 hex digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
