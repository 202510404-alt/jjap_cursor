"""Generate code-patch JSON text from Gemini."""

from __future__ import annotations

from ...types import ContextBundle, EditPlan
from .ensure_model import ensure_model
from .state import GeminiClientState


def generate_code_patch(
    state: GeminiClientState,
    plan: EditPlan,
    context: ContextBundle,
) -> str:
    """Call Gemini for patch JSON matching parse_llm_patch schema."""
    model = ensure_model(state, "patch")

    parts: list[str] = []
    parts.append("## Approved edit plan\n")
    parts.append(f"Thought: {plan.thought}\n")
    for step in plan.steps:
        parts.append(
            f"- Step {step.order}: {step.target_file.as_posix()} — {step.description}\n"
        )

    parts.append("\n## Curated context\n")
    parts.append(context.system_prompt)
    for slc in context.target_context:
        parts.append(f"\n### File: {slc.file_path.as_posix()}\n")
        parts.append(slc.content[:8000])
        if len(slc.content) > 8000:
            parts.append("\n... (truncated)\n")

    for fact in context.facts:
        parts.append(f"\n- {fact}\n")

    for sk in context.skeletons:
        parts.append(f"\n{sk}\n")

    parts.append("\n## Instruction\n")
    parts.append(
        "Produce the patches JSON to implement the plan. "
        "Use exact old/new text blocks from the files above."
    )

    response = model.generate_content("\n".join(parts))
    text = getattr(response, "text", None) or ""
    if not text.strip():
        raise ValueError("Gemini returned empty patch response text.")
    return text.strip()
