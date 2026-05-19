"""Project manager interface for orchestration workflow."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..types import ContextBundle, EditPlan, ModelResponse, ValidationResult


class ProjectManager(ABC):
    """Orchestrates the end-to-end plan, context, generation, and patch flow."""

    @abstractmethod
    def bootstrap(self, project_root: Path) -> None:
        """Initialize project session state and core services."""

    @abstractmethod
    def sync_index_if_needed(self) -> None:
        """Run lazy incremental indexing for changed files before AI interaction."""

    @abstractmethod
    def create_plan(self, user_query: str) -> EditPlan:
        """Generate a plan-first edit blueprint with targets and execution order."""

    @abstractmethod
    def build_context(self, plan: EditPlan, user_query: str) -> ContextBundle:
        """Assemble budget-constrained context using symbol-level prioritization."""

    @abstractmethod
    def execute_plan(self, plan: EditPlan, context: ContextBundle) -> ModelResponse:
        """Request model output for the approved plan and prepared context."""

    @abstractmethod
    def preview_diff(self, response: ModelResponse) -> str:
        """Produce unified diff preview for explicit user consent."""

    @abstractmethod
    def apply_with_transaction(self, response: ModelResponse) -> ValidationResult:
        """Apply generated edits through transaction-safe patching and validation."""

    @abstractmethod
    def run(self, user_query: str) -> ValidationResult:
        """Execute one full user request lifecycle from plan to final validation."""
