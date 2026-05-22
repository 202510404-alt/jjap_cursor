"""Patch engine interface for AST-hybrid patching and rollback safety."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..types import EditPlan, FilePatch, PatchTransaction, ValidationResult

# INFO: 이전 ABC 계약:
# INFO: class PatchEngine(ABC):
# INFO:     @abstractmethod
# INFO:     def create_transaction(self, plan: EditPlan, workspace_root: Path) -> PatchTransaction: ...
# INFO:     @abstractmethod
# INFO:     def transaction(self, tx: PatchTransaction) -> Iterator[PatchTransaction]: ...
# INFO:     @abstractmethod
# INFO:     def compute_patch_ast(self, file_path: Path, symbol_name: str, replacement: str) -> FilePatch | None: ...
# INFO:     @abstractmethod
# INFO:     def compute_patch_heuristic(
# INFO:         self, file_path: Path, symbol_name: str, replacement: str
# INFO:     ) -> FilePatch | None: ...
# INFO:     @abstractmethod
# INFO:     def compute_patch_fallback(self, file_path: Path, before: str, after: str) -> FilePatch | None: ...
# INFO:     @abstractmethod
# INFO:     def apply_patch(self, patch: FilePatch, tx: PatchTransaction) -> None: ...
# INFO:     @abstractmethod
# INFO:     def validate_project(self, workspace_root: Path) -> ValidationResult: ...
# INFO:     @abstractmethod
# INFO:     def commit(self, tx: PatchTransaction) -> None: ...
# INFO:     @abstractmethod
# INFO:     def rollback(self, tx: PatchTransaction, reason: str) -> None: ...
# INFO: 현재는 Protocol 구조로 전환됨 (구현체는 Phase A 체크리스트 — Planned)


@runtime_checkable
class PatchEngine(Protocol):
    """Applies model edits via ordered hybrid strategies under one transaction."""

    def create_transaction(self, plan: EditPlan, workspace_root: Path) -> PatchTransaction:
        """Prepare temporary transaction state and backup paths for all target files."""

    def transaction(self, tx: PatchTransaction) -> Iterator[PatchTransaction]:
        """Provide all-or-nothing patch scope that commits or rolls back automatically."""

    def compute_patch_ast(self, file_path: Path, symbol_name: str, replacement: str) -> FilePatch | None:
        """Compute patch from AST node range including decorators when available."""

    def compute_patch_heuristic(
        self,
        file_path: Path,
        symbol_name: str,
        replacement: str,
    ) -> FilePatch | None:
        """Compute indentation-scoped patch until next symbol boundary if AST misses."""

    def compute_patch_fallback(self, file_path: Path, before: str, after: str) -> FilePatch | None:
        """Compute last-resort text search/replace patch when structured methods fail."""

    def apply_patch(self, patch: FilePatch, tx: PatchTransaction) -> None:
        """Stage one file patch into transaction temporary state without final commit."""

    def validate_project(self, workspace_root: Path) -> ValidationResult:
        """Run post-apply whole-project validation after all staged modifications."""

    def commit(self, tx: PatchTransaction) -> None:
        """Finalize transaction by replacing originals with validated staged files."""

    def rollback(self, tx: PatchTransaction, reason: str) -> None:
        """Restore backups for every touched file when any stage fails."""
