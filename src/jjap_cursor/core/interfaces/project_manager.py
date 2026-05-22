"""Project manager interface for orchestration workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..types import ContextBundle, EditPlan, ModelResponse, ValidationResult

# INFO: 이전 ABC 계약:
# INFO: class ProjectManager(ABC):
# INFO:     @abstractmethod
# INFO:     def bootstrap(self, project_root: Path) -> None: ...
# INFO:     @abstractmethod
# INFO:     def sync_index_if_needed(self) -> None: ...
# INFO:     @abstractmethod
# INFO:     def create_plan(self, user_query: str) -> EditPlan: ...
# INFO:     @abstractmethod
# INFO:     def build_context(self, plan: EditPlan, user_query: str) -> ContextBundle: ...
# INFO:     @abstractmethod
# INFO:     def execute_plan(self, plan: EditPlan, context: ContextBundle) -> ModelResponse: ...
# INFO:     @abstractmethod
# INFO:     def preview_diff(self, response: ModelResponse) -> str: ...
# INFO:     @abstractmethod
# INFO:     def apply_with_transaction(self, response: ModelResponse) -> ValidationResult: ...
# INFO:     @abstractmethod
# INFO:     def run(self, user_query: str) -> ValidationResult: ...
# INFO: 현재는 Protocol 구조로 전환됨


@runtime_checkable
class ProjectManager(Protocol):
    """Orchestrates the end-to-end plan, context, generation, and patch flow."""

    def bootstrap(self, project_root: Path) -> None:
        """Initialize project session state and core services."""

    def sync_index_if_needed(self) -> None:
        """Run lazy incremental indexing for changed files before AI interaction."""

    def create_plan(self, user_query: str) -> EditPlan:
        """Generate a plan-first edit blueprint with targets and execution order."""

    def build_context(self, plan: EditPlan, user_query: str) -> ContextBundle:
        """Assemble budget-constrained context using symbol-level prioritization."""

    def execute_plan(self, plan: EditPlan, context: ContextBundle) -> ModelResponse:
        """Request model output for the approved plan and prepared context."""

    def preview_diff(self, response: ModelResponse) -> str:
        """Produce unified diff preview for explicit user consent."""

    def apply_with_transaction(self, response: ModelResponse) -> ValidationResult:
        """Apply generated edits through transaction-safe patching and validation."""

    def run(self, user_query: str) -> ValidationResult:
        """Execute one full user request lifecycle from plan to final validation."""
