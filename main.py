# Requires Python 3.9+ (ast.unparse used)
#
# Dependencies for planning (Gemini):
#   pip install -r requirements.txt
#   # google-generativeai, python-dotenv
# Set GEMINI_API_KEY in .env or the environment.
# Optional: JJAP_QUERY overrides the default planning prompt.

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    """Run scan pipeline then Gemini-backed plan generation (MVP)."""
    root_path = Path(__file__).resolve().parent
    src_path = root_path / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from jjap_cursor.core.errors import PlanningError
    from jjap_cursor.core.services.project_manager import DefaultProjectManager

    manager = DefaultProjectManager()
    manager.bootstrap(root_path)

    scan_result = manager.run("Initial Scan")
    symbols_path = (root_path / ".jjap_symbols.json").resolve()
    context_path = (root_path / ".jjap_context.json").resolve()

    if scan_result.ok and symbols_path.exists() and context_path.exists():
        print(f"[Jjap-Cursor] Symbols JSON: {symbols_path}")
        print(f"[Jjap-Cursor] Context JSON: {context_path}")
    else:
        print("[Jjap-Cursor] Scan failed or output files missing.")
        return

    query = os.environ.get(
        "JJAP_QUERY",
        "Propose a minimal plan to improve logging in the project entry flow.",
    )

    try:
        plan = manager.create_plan(query)
    except PlanningError as exc:
        print(f"[Jjap-Cursor] Planning failed: {exc}")
        return

    print("\n[Jjap-Cursor] Plan summary")
    print(f"Thought: {plan.thought}")
    for step in plan.steps:
        print(f"  {step.order}. [{step.target_file.as_posix()}] {step.description}")


if __name__ == "__main__":
    main()
