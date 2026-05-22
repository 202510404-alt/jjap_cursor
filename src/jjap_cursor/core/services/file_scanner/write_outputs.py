"""Write scan artifacts to v8.0 context files in project root."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...utils.io_utils import atomic_write_text

from .hash_utils import sha256_of_file
from .types import ScanArtifacts


def write_scan_outputs(project_root: Path, artifacts: ScanArtifacts) -> None:
    """Write scanner outputs to v8.0 context files in project root."""
    symbols_path = project_root / ".jjap_symbols.json"
    context_path = project_root / ".jjap_context.json"

    symbol_payload = json.dumps(artifacts.symbol_table, ensure_ascii=False, indent=2)
    atomic_write_text(symbols_path, symbol_payload)

    file_metadata: dict[str, dict[str, Any]] = {}
    for rel_path, skeleton in artifacts.skeletons.items():
        abs_path = project_root / rel_path
        file_metadata[rel_path] = {
            "hash": sha256_of_file(abs_path),
            "mtime": int(abs_path.stat().st_mtime),
            "skeleton": skeleton,
        }

    context_payload = {
        "files": file_metadata,
        "global_symbols": [s["symbol_id"] for s in artifacts.symbol_table["symbols"]],
    }
    context_json = json.dumps(context_payload, ensure_ascii=False, indent=2)
    atomic_write_text(context_path, context_json)
