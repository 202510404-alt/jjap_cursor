"""Lazy Gemini model initialization."""

from __future__ import annotations

from typing import Any, Literal

from .constants import MODEL_NAME, PATCH_SYSTEM_INSTRUCTION, PLAN_SYSTEM_INSTRUCTION
from .state import GeminiClientState

ModelKind = Literal["plan", "patch"]


def ensure_model(state: GeminiClientState, kind: ModelKind) -> Any:
    """Return cached GenerativeModel for plan or patch, creating on first use."""
    cached = state._plan_model if kind == "plan" else state._patch_model
    if cached is not None:
        return cached

    if not state.api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to .env or the environment "
            "(see requirements: python-dotenv, google-generativeai)."
        )
    try:
        import google.generativeai as genai
    except ImportError as exc:  # pragma: no cover - env dependent
        raise RuntimeError(
            "google-generativeai is not installed. Run: pip install google-generativeai"
        ) from exc

    genai.configure(api_key=state.api_key)
    system_instruction = PLAN_SYSTEM_INSTRUCTION if kind == "plan" else PATCH_SYSTEM_INSTRUCTION
    try:
        from google.generativeai import types as genai_types

        gen_config = genai_types.GenerationConfig(
            temperature=0.1,
            response_mime_type="application/json",
        )
    except Exception:  # pragma: no cover - version fallback
        gen_config = {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        }

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction,
        generation_config=gen_config,
    )
    if kind == "plan":
        state._plan_model = model
    else:
        state._patch_model = model
    return model
