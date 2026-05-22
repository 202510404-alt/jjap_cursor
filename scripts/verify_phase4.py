"""Phase 4 verification script (run from repo root)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    errors: list[str] = []

    # 1) Protocol imports
    from jjap_cursor.core.interfaces import ContextBuilder, GeminiClient, PatchEngine, ProjectManager
    from typing import Protocol

    for name, obj in [
        ("ContextBuilder", ContextBuilder),
        ("GeminiClient", GeminiClient),
        ("PatchEngine", PatchEngine),
        ("ProjectManager", ProjectManager),
    ]:
        if not hasattr(obj, "_is_protocol"):
            errors.append(f"{name} is not a Protocol")

    # 2) context_builder package
    from jjap_cursor.core.services.context_builder import (
        DefaultContextBuilder,
        assemble_context,
        build_planning_context,
        ContextBuilderState,
    )
    from jjap_cursor.core.services.file_scanner import scan_project
    from jjap_cursor.core.types import EditPlan, PlanStep

    project_root = ROOT.resolve()
    scan_project(project_root)

    cb = DefaultContextBuilder(project_root)
    ctx_str = cb.build_planning_context("test query")
    assert len(ctx_str) > 0, "build_planning_context empty"

    plan = EditPlan(
        thought="test",
        steps=[
            PlanStep(order=1, target_file=Path("main.py"), description="noop"),
        ],
    )
    bundle = cb.assemble(plan, "test")
    assert bundle.target_context, "assemble produced no target_context"

    # isinstance Protocol check
    if not isinstance(cb, ContextBuilder):
        errors.append("DefaultContextBuilder does not satisfy ContextBuilder Protocol")

    # 3) gemini_client package
    from jjap_cursor.core.services.gemini_client import (
        GeminiPlanClient,
        generate_edit_plan,
        GeminiClientState,
    )

    state = GeminiClientState(api_key="")
    try:
        generate_edit_plan(state, "ctx", "q")
        errors.append("generate_edit_plan should fail without API key")
    except RuntimeError:
        pass

    gc = GeminiPlanClient(api_key="")
    if not isinstance(gc, GeminiClient):
        errors.append("GeminiPlanClient does not satisfy GeminiClient Protocol")

    required = (
        "generate_edit_plan",
        "generate_code_patch",
        "build_plan_prompt",
        "enforce_json_response",
    )
    for meth in required:
        if not hasattr(gc, meth):
            errors.append(f"GeminiPlanClient missing {meth}")

    # 4) pipeline imports
    from jjap_cursor.core.services.project_manager.run_pipeline import run_jjap_pipeline
    from jjap_cursor.core.services.project_manager.create_plan import create_edit_plan

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print("Phase4 verify OK")
    print("  Protocol:", ContextBuilder.__name__, GeminiClient.__name__)
    print("  planning_context bytes:", len(ctx_str))
    print("  assemble slices:", len(bundle.target_context))


if __name__ == "__main__":
    main()
