"""Build planning-stage context string from index artifacts."""

from __future__ import annotations

import json

from .state import ContextBuilderState

DEBUG_MODE = True


def build_planning_context(state: ContextBuilderState, user_query: str) -> str:
    """Assemble text context from .jjap_context.json and .jjap_symbols.json for plan generation."""
    parts: list[str] = []
    parts.append("## User request\n")
    parts.append(user_query.strip())

    context_path = state.project_root / ".jjap_context.json"
    symbols_path = state.project_root / ".jjap_symbols.json"

    if context_path.exists():
        try:
            context_data = json.loads(context_path.read_text(encoding="utf-8"))
            parts.append("\n\n## Project file skeletons (from .jjap_context.json)\n")
            files = context_data.get("files", {})
            for rel_path, meta in sorted(files.items()):
                skeleton = str(meta.get("skeleton", "")).strip()
                if skeleton:
                    parts.append(f"### {rel_path}\n{skeleton}\n")
        except (json.JSONDecodeError, OSError) as exc:
            if DEBUG_MODE:
                print(f"[DEBUG] ContextBuilder: .jjap_context.json 읽기 실패: {exc}")

    if symbols_path.exists():
        try:
            symbols_data = json.loads(symbols_path.read_text(encoding="utf-8"))
            symbols = symbols_data.get("symbols", [])
            parts.append("\n\n## Symbol index summary (from .jjap_symbols.json)\n")
            for entry in symbols[:80]:
                sid = entry.get("symbol_id", "")
                sig = entry.get("signature", "")
                parts.append(f"- {sid} {sig}\n")
            if len(symbols) > 80:
                parts.append(f"... and {len(symbols) - 80} more symbols\n")
        except (json.JSONDecodeError, OSError) as exc:
            if DEBUG_MODE:
                print(f"[DEBUG] ContextBuilder: .jjap_symbols.json 읽기 실패: {exc}")

    if DEBUG_MODE:
        print(f"[DEBUG] ContextBuilder: planning context length={len(''.join(parts))}")

    return "\n".join(parts)
