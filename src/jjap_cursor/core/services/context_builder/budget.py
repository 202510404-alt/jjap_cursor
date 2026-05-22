"""Token budget helpers and low-priority context collectors."""

from __future__ import annotations

from pathlib import Path

from ...types import BudgetPriority, EditPlan, SymbolSlice
from .state import ContextBuilderState

DEBUG_MODE = True


def set_budget(state: ContextBuilderState, max_tokens: int) -> None:
    # INFO: AI가 먹을 수 있는 최대 토큰 통제 지지선을 설정합니다.
    state.max_tokens = max_tokens
    if DEBUG_MODE:
        print(f"[DEBUG] ContextBuilder: 토큰 버젯 변경됨 -> {state.max_tokens}")


def collect_facts(state: ContextBuilderState, project_root: Path) -> list[str]:
    # INFO: Phase C 전까지 MVP: 빈 facts 또는 프로젝트 루트 확인만.
    if DEBUG_MODE:
        print(f"[DEBUG] ContextBuilder: facts 수집 (MVP) root={project_root}")
    return []


def collect_skeletons(state: ContextBuilderState, plan: EditPlan) -> list[str]:
    # INFO: Phase C 전까지 MVP: 빈 skeletons 리스트.
    if DEBUG_MODE:
        print(f"[DEBUG] ContextBuilder: skeletons 수집 (MVP) steps={len(plan.steps)}")
    return []


def estimate_tokens(text: str) -> int:
    # INFO: 단순 휴리스틱 — 4 chars ≈ 1 token.
    return max(1, len(text) // 4)


def evict_until_within_budget(
    slices: list[SymbolSlice],
    priority_order: list[BudgetPriority],
    max_tokens: int,
) -> list[SymbolSlice]:
    # INFO: MVP: 토큰 합이 budget 이하가 될 때까지 priority_order 역순으로 제거.
    if DEBUG_MODE:
        print(f"[DEBUG] ContextBuilder: eviction max_tokens={max_tokens} slices={len(slices)}")

    kept = list(slices)
    while kept and sum(s.token_cost for s in kept) > max_tokens:
        removed = False
        for priority in reversed(priority_order):
            for idx in range(len(kept) - 1, -1, -1):
                if kept[idx].priority == priority:
                    kept.pop(idx)
                    removed = True
                    break
            if removed:
                break
        if not removed:
            kept.pop()
    return kept
