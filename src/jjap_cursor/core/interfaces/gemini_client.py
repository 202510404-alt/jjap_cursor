"""Gemini client interface enforcing plan-first and strict JSON responses."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..types import ChatMessage, ContextBundle, EditPlan, ModelResponse

# INFO: 이전 ABC 계약:
# INFO: class GeminiClient(ABC):
# INFO:     @abstractmethod
# INFO:     def build_plan_prompt(self, user_query: str) -> list[ChatMessage]: ...
# INFO:     @abstractmethod
# INFO:     def request_plan(self, user_query: str) -> EditPlan: ...
# INFO:     @abstractmethod
# INFO:     def build_execution_prompt(
# INFO:         self, plan: EditPlan, context: ContextBundle, user_query: str
# INFO:     ) -> list[ChatMessage]: ...
# INFO:     @abstractmethod
# INFO:     def request_execution(
# INFO:         self, plan: EditPlan, context: ContextBundle, user_query: str
# INFO:     ) -> ModelResponse: ...
# INFO:     @abstractmethod
# INFO:     def enforce_json_response(self, text: str) -> dict: ...
# INFO:     @abstractmethod
# INFO:     def retry_on_parse_error(self, messages: list[ChatMessage], max_retries: int = 3) -> dict: ...
# INFO: 현재는 Protocol 구조로 전환됨 (MVP 파이프라인 메서드 generate_edit_plan / generate_code_patch 추가).


@runtime_checkable
class GeminiClient(Protocol):
    """Wraps Gemini API calls with strict workflow and response contracts."""

    def build_plan_prompt(self, user_query: str) -> list[ChatMessage]:
        """Create prompt messages that require THOUGHT and ordered edit plan output."""

    def request_plan(self, user_query: str) -> EditPlan:
        """Request and parse structured plan-first output for an incoming query."""

    def build_execution_prompt(
        self,
        plan: EditPlan,
        context: ContextBundle,
        user_query: str,
    ) -> list[ChatMessage]:
        """Create execution prompt combining approved plan and curated context bundle."""

    def request_execution(
        self,
        plan: EditPlan,
        context: ContextBundle,
        user_query: str,
    ) -> ModelResponse:
        """Execute plan against Gemini and parse strict JSON patch payload output."""

    def enforce_json_response(self, text: str) -> dict:
        """Validate and decode JSON-only model text, raising on any extra chatter."""

    def retry_on_parse_error(self, messages: list[ChatMessage], max_retries: int = 3) -> dict:
        """Retry API call when syntax/parsing fails, including error feedback each try."""

    def generate_edit_plan(
        self,
        planning_context: str,
        user_query: str,
        repair_feedback: str | None = None,
    ) -> str:
        """Call Gemini for plan JSON text (orchestrator handles retries)."""

    def generate_code_patch(self, plan: EditPlan, context: ContextBundle) -> str:
        """Call Gemini for patch JSON text matching parse_llm_patch schema."""
