"""Context builder package — function modules + DefaultContextBuilder facade."""

from __future__ import annotations

from pathlib import Path

from ...types import BudgetPriority, ContextBundle, EditPlan, SymbolSlice
from .assemble_context import assemble_context
from .budget import (
    collect_facts,
    collect_skeletons,
    estimate_tokens,
    evict_until_within_budget,
    set_budget,
)
from .collect_related import collect_related_symbols
from .collect_target import collect_target_context
from .planning_context import build_planning_context
from .state import ContextBuilderState

DEBUG_MODE = True

# INFO: 이전 단일 파일 클래스 계약:
# INFO: class DefaultContextBuilder(ContextBuilder):
# INFO:     def __init__(self, project_root: Path) -> None: ...
# INFO:     def set_budget(self, max_tokens: int) -> None: ...
# INFO:     def _read_and_clean_file(self, relative_path: str) -> str: ...
# INFO:     def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]: ...
# INFO:     def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]: ...
# INFO:     def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle: ...
# INFO: 현재는 context_builder/ 서브패키지 + assemble_context 등 함수로 전환됨.


class DefaultContextBuilder:
    """Facade implementing ContextBuilder Protocol via context_builder functions."""

    def __init__(self, project_root: Path) -> None:
        self._state = ContextBuilderState(project_root=Path(project_root))
        if DEBUG_MODE:
            print(f"[DEBUG] ContextBuilder: 초기화 완료. 프로젝트 루트 -> {self._state.project_root}")

    @property
    def project_root(self) -> Path:
        return self._state.project_root

    def set_budget(self, max_tokens: int) -> None:
        set_budget(self._state, max_tokens)

    def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]:
        return collect_target_context(self._state, plan, user_query)

    def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]:
        return collect_related_symbols(self._state, plan)

    def collect_facts(self, project_root: Path) -> list[str]:
        return collect_facts(self._state, project_root)

    def collect_skeletons(self, plan: EditPlan) -> list[str]:
        return collect_skeletons(self._state, plan)

    def estimate_tokens(self, text: str) -> int:
        return estimate_tokens(text)

    def evict_until_within_budget(
        self,
        slices: list[SymbolSlice],
        priority_order: list[BudgetPriority],
        max_tokens: int,
    ) -> list[SymbolSlice]:
        return evict_until_within_budget(slices, priority_order, max_tokens)

    def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle:
        return assemble_context(self._state, plan, user_query)

    def build_planning_context(self, user_query: str) -> str:
        return build_planning_context(self._state, user_query)


__all__ = [
    "ContextBuilderState",
    "DefaultContextBuilder",
    "assemble_context",
    "build_planning_context",
    "collect_target_context",
    "collect_related_symbols",
]
