"""Collect related symbols from call-graph (MVP stub)."""

from __future__ import annotations

from ...types import EditPlan, SymbolSlice
from .state import ContextBuilderState

DEBUG_MODE = True


def collect_related_symbols(
    state: ContextBuilderState,
    plan: EditPlan,
) -> list[SymbolSlice]:
    # INFO: 주변부 의존성이나 스켈레톤 지도를 분석하는 구역입니다. v8.1 명세에 따라 구조를 보존합니다.
    # HISTORY: 1차 MVP 단계에서는 빈 결괏값 구조만 유지하고 Phase C 증분 인덱서 결합 시 내부를 구체화하도록 기동 연기함.
    if DEBUG_MODE:
        print("[DEBUG] ContextBuilder: 🔗 주변 의존성 심볼 분석 중... (현재는 MVP 단계로 스킵)")
    return []
