"""Gemini client package — function modules + GeminiPlanClient facade."""

from __future__ import annotations

import os
from typing import Any

from ...types import ChatMessage, ContextBundle, EditPlan, ModelResponse
from .constants import MODEL_NAME, PLAN_SYSTEM_INSTRUCTION, PATCH_SYSTEM_INSTRUCTION
from .generate_code_patch import generate_code_patch
from .generate_edit_plan import generate_edit_plan
from .protocol_stubs import (
    build_execution_prompt,
    build_plan_prompt,
    enforce_json_response,
    retry_on_parse_error,
)
from .state import GeminiClientState

# INFO: 이전 단일 파일 클래스 계약:
# INFO: class GeminiPlanClient:
# INFO:     def __init__(self, api_key: str | None = None) -> None: ...
# INFO:     def _ensure_model(self) -> Any: ...
# INFO:     def generate_edit_plan(
# INFO:         self, planning_context: str, user_query: str, repair_feedback: str | None = None
# INFO:     ) -> str: ...
# INFO: 현재는 gemini_client/ 서브패키지 + generate_edit_plan / generate_code_patch 함수로 전환됨.


class GeminiPlanClient:
    """Facade implementing GeminiClient Protocol via gemini_client functions."""

    def __init__(self, api_key: str | None = None) -> None:
        self._state = GeminiClientState(api_key=api_key or os.environ.get("GEMINI_API_KEY", ""))

    def _ensure_model(self) -> Any:
        from .ensure_model import ensure_model

        return ensure_model(self._state, "plan")

    def generate_edit_plan(
        self,
        planning_context: str,
        user_query: str,
        repair_feedback: str | None = None,
    ) -> str:
        return generate_edit_plan(self._state, planning_context, user_query, repair_feedback)

    def generate_code_patch(self, plan: EditPlan, context: ContextBundle) -> str:
        return generate_code_patch(self._state, plan, context)

    def build_plan_prompt(self, user_query: str) -> list[ChatMessage]:
        return build_plan_prompt(user_query)

    def request_plan(self, user_query: str) -> EditPlan:
        raise NotImplementedError("request_plan: use create_edit_plan orchestration")

    def build_execution_prompt(
        self,
        plan: EditPlan,
        context: ContextBundle,
        user_query: str,
    ) -> list[ChatMessage]:
        return build_execution_prompt(plan, context, user_query)

    def request_execution(
        self,
        plan: EditPlan,
        context: ContextBundle,
        user_query: str,
    ) -> ModelResponse:
        raise NotImplementedError("request_execution: use generate_code_patch + parse_llm_patch")

    def enforce_json_response(self, text: str) -> dict:
        return enforce_json_response(text)

    def retry_on_parse_error(self, messages: list[ChatMessage], max_retries: int = 3) -> dict:
        return retry_on_parse_error(messages, max_retries)


__all__ = [
    "MODEL_NAME",
    "PLAN_SYSTEM_INSTRUCTION",
    "PATCH_SYSTEM_INSTRUCTION",
    "GeminiClientState",
    "GeminiPlanClient",
    "generate_edit_plan",
    "generate_code_patch",
]
