"""Gemini client interface enforcing plan-first and strict JSON responses."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import ChatMessage, ContextBundle, EditPlan, ModelResponse


class GeminiClient(ABC):
    """Wraps Gemini API calls with strict workflow and response contracts."""

    @abstractmethod
    def build_plan_prompt(self, user_query: str) -> list[ChatMessage]:
        """Create prompt messages that require THOUGHT and ordered edit plan output."""

    @abstractmethod
    def request_plan(self, user_query: str) -> EditPlan:
        """Request and parse structured plan-first output for an incoming query."""

    @abstractmethod
    def build_execution_prompt(
        self,
        plan: EditPlan,
        context: ContextBundle,
        user_query: str,
    ) -> list[ChatMessage]:
        """Create execution prompt combining approved plan and curated context bundle."""

    @abstractmethod
    def request_execution(
        self,
        plan: EditPlan,
        context: ContextBundle,
        user_query: str,
    ) -> ModelResponse:
        """Execute plan against Gemini and parse strict JSON patch payload output."""

    @abstractmethod
    def enforce_json_response(self, text: str) -> dict:
        """Validate and decode JSON-only model text, raising on any extra chatter."""

    @abstractmethod
    def retry_on_parse_error(self, messages: list[ChatMessage], max_retries: int = 3) -> dict:
        """Retry API call when syntax/parsing fails, including error feedback each try."""
