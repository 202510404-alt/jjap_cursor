"""Stub implementations for legacy GeminiClient Protocol methods (MVP)."""

from __future__ import annotations

import json

from ...types import ChatMessage, ContextBundle, EditPlan, ModelResponse


def build_plan_prompt(user_query: str) -> list[ChatMessage]:
    return [
        ChatMessage(role="user", content=user_query),
    ]


def build_execution_prompt(
    plan: EditPlan,
    context: ContextBundle,
    user_query: str,
) -> list[ChatMessage]:
    return [
        ChatMessage(role="system", content=context.system_prompt),
        ChatMessage(role="user", content=f"{user_query}\nPlan: {plan.thought}"),
    ]


def enforce_json_response(text: str) -> dict:
    return json.loads(text.strip())


def retry_on_parse_error(messages: list[ChatMessage], max_retries: int = 3) -> dict:
    raise NotImplementedError("retry_on_parse_error: use create_edit_plan loop in project_manager")
