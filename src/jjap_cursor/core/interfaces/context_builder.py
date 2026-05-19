"""Context builder interface for dynamic budget and symbol eviction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..types import BudgetPriority, ContextBundle, EditPlan, SymbolSlice


class ContextBuilder(ABC):
    """Builds and optimizes model context using v8.0 budget policies."""

    @abstractmethod
    def set_budget(self, max_tokens: int) -> None:
        """Configure maximum token budget for the next context assembly."""

    @abstractmethod
    def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]:
        """Collect highest-priority target symbols tied directly to requested edits."""

    @abstractmethod
    def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]:
        """Collect relational symbols through import and call-graph dependencies."""

    @abstractmethod
    def collect_facts(self, project_root: Path) -> list[str]:
        """Load stable facts and approved notes from persistent project memory."""

    @abstractmethod
    def collect_skeletons(self, plan: EditPlan) -> list[str]:
        """Load AST skeleton snippets for lower-priority structural context."""

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token cost for one text fragment or symbol payload."""

    @abstractmethod
    def evict_until_within_budget(
        self,
        slices: list[SymbolSlice],
        priority_order: list[BudgetPriority],
        max_tokens: int,
    ) -> list[SymbolSlice]:
        """Evict low-priority symbols first until total token cost fits the budget."""

    @abstractmethod
    def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle:
        """Build final context bundle ordered by target > related > facts > skeletons."""
