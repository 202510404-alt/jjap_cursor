"""Patch engine interface for AST-hybrid patching and rollback safety."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from ..types import EditPlan, FilePatch, PatchTransaction, ValidationResult


class PatchEngine(ABC):
    """Applies model edits via ordered hybrid strategies under one transaction."""

    @abstractmethod
    def create_transaction(self, plan: EditPlan, workspace_root: Path) -> PatchTransaction:
        """Prepare temporary transaction state and backup paths for all target files."""

    @abstractmethod
    def transaction(self, tx: PatchTransaction) -> Iterator[PatchTransaction]:
        """Provide all-or-nothing patch scope that commits or rolls back automatically."""

    @abstractmethod
    def compute_patch_ast(self, file_path: Path, symbol_name: str, replacement: str) -> FilePatch | None:
        """Compute patch from AST node range including decorators when available."""

    @abstractmethod
    def compute_patch_heuristic(
        self,
        file_path: Path,
        symbol_name: str,
        replacement: str,
    ) -> FilePatch | None:
        """Compute indentation-scoped patch until next symbol boundary if AST misses."""

    @abstractmethod
    def compute_patch_fallback(self, file_path: Path, before: str, after: str) -> FilePatch | None:
        """Compute last-resort text search/replace patch when structured methods fail."""

    @abstractmethod
    def apply_patch(self, patch: FilePatch, tx: PatchTransaction) -> None:
        """Stage one file patch into transaction temporary state without final commit."""

    @abstractmethod
    def validate_project(self, workspace_root: Path) -> ValidationResult:
        """Run post-apply whole-project validation after all staged modifications."""

    @abstractmethod
    def commit(self, tx: PatchTransaction) -> None:
        """Finalize transaction by replacing originals with validated staged files."""

    @abstractmethod
    def rollback(self, tx: PatchTransaction, reason: str) -> None:
        """Restore backups for every touched file when any stage fails."""
