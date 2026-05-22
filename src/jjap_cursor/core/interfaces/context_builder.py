"""Context builder interface for dynamic budget and symbol eviction."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..types import BudgetPriority, ContextBundle, EditPlan, SymbolSlice

# INFO: 이전 ABC 계약:
# INFO: class ContextBuilder(ABC):
# INFO:     @abstractmethod
# INFO:     def set_budget(self, max_tokens: int) -> None: ...
# INFO:     @abstractmethod
# INFO:     def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]: ...
# INFO:     @abstractmethod
# INFO:     def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]: ...
# INFO:     @abstractmethod
# INFO:     def collect_facts(self, project_root: Path) -> list[str]: ...
# INFO:     @abstractmethod
# INFO:     def collect_skeletons(self, plan: EditPlan) -> list[str]: ...
# INFO:     @abstractmethod
# INFO:     def estimate_tokens(self, text: str) -> int: ...
# INFO:     @abstractmethod
# INFO:     def evict_until_within_budget(
# INFO:         self, slices: list[SymbolSlice], priority_order: list[BudgetPriority], max_tokens: int
# INFO:     ) -> list[SymbolSlice]: ...
# INFO:     @abstractmethod
# INFO:     def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle: ...
# INFO: 현재는 Protocol 구조로 전환됨 (MVP 구현 메서드 build_planning_context 추가).


@runtime_checkable
class ContextBuilder(Protocol):
    """Builds and optimizes model context using v8.0 budget policies."""

    def set_budget(self, max_tokens: int) -> None:
        """Configure maximum token budget for the next context assembly."""

    def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]:
        """Collect highest-priority target symbols tied directly to requested edits."""

    def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]:
        """Collect relational symbols through import and call-graph dependencies."""

    def collect_facts(self, project_root: Path) -> list[str]:
        """Load stable facts and approved notes from persistent project memory."""

    def collect_skeletons(self, plan: EditPlan) -> list[str]:
        """Load AST skeleton snippets for lower-priority structural context."""

    def estimate_tokens(self, text: str) -> int:
        """Estimate token cost for one text fragment or symbol payload."""

    def evict_until_within_budget(
        self,
        slices: list[SymbolSlice],
        priority_order: list[BudgetPriority],
        max_tokens: int,
    ) -> list[SymbolSlice]:
        """Evict low-priority symbols first until total token cost fits the budget."""

    def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle:
        """Build final context bundle ordered by target > related > facts > skeletons."""

    def build_planning_context(self, user_query: str) -> str:
        """Build lightweight planning context from project index artifacts."""
