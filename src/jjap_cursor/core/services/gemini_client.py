"""Gemini inference client for plan-first JSON generation (v8.0).

Dependencies (install via pip):
    pip install google-generativeai python-dotenv
"""

from __future__ import annotations

import os
from typing import Any

MODEL_NAME = "gemini-2.5-flash"

_PLAN_SYSTEM_INSTRUCTION = """You are a Senior Software Engineer.

Your task is to produce an edit plan for the user's request.

Output ONLY valid JSON. No markdown fences, no prose before or after the JSON.

The JSON MUST match this exact schema (keys required):
{
  "thought": "Concise execution summary only. Never reveal internal chain-of-thought.",
  "affected_files": ["path.py"],
  "steps": [{"title": "step name", "description": "detail"}]
}

Rules:
- "thought": one concise string summarizing what will be done.
- "affected_files": non-empty array of project-relative file paths (use forward slashes).
- "steps": non-empty array; each item MUST have non-empty "title" and "description" strings.
"""


class GeminiPlanClient:
    """Inference-only client: calls Gemini and returns raw JSON text from the model."""

    def __init__(self, api_key: str | None = None) -> None:
        """Configure API key; prefers explicit key, then env GEMINI_API_KEY."""
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is not None:
            return self._model
        if not self._api_key:
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

        genai.configure(api_key=self._api_key)
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

        self._model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=_PLAN_SYSTEM_INSTRUCTION,
            generation_config=gen_config,
        )
        return self._model

    def generate_edit_plan(
        self,
        planning_context: str,
        user_query: str,
        repair_feedback: str | None = None,
    ) -> str:
        """Call Gemini once; return model text (expected JSON). Orchestrator handles retries."""
        model = self._ensure_model()

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
