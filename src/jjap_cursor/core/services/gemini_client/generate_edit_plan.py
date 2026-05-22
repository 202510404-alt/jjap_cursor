"""Generate edit-plan JSON text from Gemini."""

from __future__ import annotations

from .ensure_model import ensure_model
from .state import GeminiClientState


def generate_edit_plan(
    state: GeminiClientState,
    planning_context: str,
    user_query: str,
    repair_feedback: str | None = None,
) -> str:
    """Call Gemini once; return model text (expected JSON). Orchestrator handles retries."""
    model = ensure_model(state, "plan")

    parts: list[str] = []
    parts.append("## Project context (for planning)\n")
    parts.append(planning_context.strip())
    parts.append("\n\n## User request\n")
    parts.append(user_query.strip())
    if repair_feedback:
        parts.append("\n\n## Previous attempt failed — fix your output\n")
        parts.append(repair_feedback.strip())

    response = model.generate_content("\n".join(parts))
    text = getattr(response, "text", None) or ""
    if not text.strip():
        raise ValueError("Gemini returned empty response text.")
    return text.strip()
