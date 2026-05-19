"""Concrete project manager service implementation."""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv  # type: ignore[import-untyped]

from ..errors import PlanningError
from ..interfaces.project_manager import ProjectManager
from ..types import ContextBundle, EditPlan, ModelResponse, PlanStep, ValidationResult
from .context_builder import DefaultContextBuilder
from .file_scanner import FileScanner
from .gemini_client import GeminiPlanClient


class DefaultProjectManager(ProjectManager):
    """Default project manager that wires scanner, context, and Gemini planning."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize manager with optional project root."""
        self.project_root = project_root
        self.file_scanner: FileScanner | None = None
        self.context_builder: DefaultContextBuilder | None = None
        self._gemini: GeminiPlanClient | None = None

    def bootstrap(self, project_root: Path) -> None:
        """Initialize project session state and core services."""
        load_dotenv(project_root / ".env")
        load_dotenv()

        self.project_root = project_root
        self.file_scanner = FileScanner(project_root=project_root)
        self.context_builder = DefaultContextBuilder(project_root=project_root)
        self._gemini = GeminiPlanClient()

    def sync_index_if_needed(self) -> None:
        """Run lazy incremental indexing for changed files before AI interaction."""
        return None

    def create_plan(self, user_query: str) -> EditPlan:
        """Generate a plan-first edit blueprint with targets and execution order."""
        if self.context_builder is None or self._gemini is None or self.project_root is None:
            raise RuntimeError("ProjectManager is not bootstrapped.")

        planning_ctx = self.context_builder.build_planning_context(user_query)
        last_error: str | None = None

        for _ in range(3):
            try:
                raw = self._gemini.generate_edit_plan(
                    planning_context=planning_ctx,
                    user_query=user_query,
                    repair_feedback=last_error,
                )
                data = json.loads(raw)
                self._validate_plan_schema(data)
                return self._plan_payload_to_edit_plan(data)
            except (json.JSONDecodeError, ValueError, TypeError, RuntimeError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"

        raise PlanningError(
            f"Plan generation failed after 3 attempts. Last error: {last_error}"
        )

    def build_context(self, plan: EditPlan, user_query: str) -> ContextBundle:
        """Assemble budget-constrained context using symbol-level prioritization."""
        if self.context_builder is None:
            raise RuntimeError("ProjectManager is not bootstrapped.")
        return self.context_builder.assemble(plan=plan, user_query=user_query)

    def execute_plan(self, plan: EditPlan, context: ContextBundle) -> ModelResponse:
        """Request model output for the approved plan and prepared context."""
        raise NotImplementedError("Execution client is not connected yet.")

    def preview_diff(self, response: ModelResponse) -> str:
        """Produce unified diff preview for explicit user consent."""
        raise NotImplementedError("Diff preview is not connected yet.")

    def apply_with_transaction(self, response: ModelResponse) -> ValidationResult:
        """Apply generated edits through transaction-safe patching and validation."""
        raise NotImplementedError("Patch engine is not connected yet.")

    def run(self, user_query: str) -> ValidationResult:
        """Execute one full user request lifecycle from plan to final validation."""
        # TODO: Separate scanning/bootstrap lifecycle from conversational execution flow.
        if self.file_scanner is None or self.project_root is None:
            raise RuntimeError("ProjectManager is not bootstrapped.")

        artifacts = self.file_scanner.scan_project()
        self.file_scanner.write_outputs(artifacts)

        symbol_count = len(artifacts.symbol_table.get("symbols", []))
        file_count = len(artifacts.skeletons)
        print("[Jjap-Cursor] Atomic write enabled: true")
        print(f"[Jjap-Cursor] Indexed files: {file_count}, symbols: {symbol_count}")
        print("[Jjap-Cursor] Incremental metadata generated: SHA256 + mtime")

        return ValidationResult(ok=True, errors=[])

    @staticmethod
    def _validate_plan_schema(data: object) -> None:
        """Validate Gemini JSON plan; raises ValueError on violation (triggers retry)."""
        if not isinstance(data, dict):
            raise ValueError("Root JSON must be an object.")

        thought = data.get("thought")
        if not isinstance(thought, str) or not thought.strip():
            raise ValueError('"thought" must be a non-empty string.')

        files = data.get("affected_files")
        if not isinstance(files, list) or len(files) == 0:
            raise ValueError('"affected_files" must be a non-empty array.')
        for item in files:
            if not isinstance(item, str) or not item.strip():
                raise ValueError('"affected_files" entries must be non-empty strings.')

        steps = data.get("steps")
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError('"steps" must be a non-empty array.')
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f'"steps[{idx}]" must be an object.')
            title = step.get("title")
            desc = step.get("description")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f'"steps[{idx}].title" must be a non-empty string.')
            if not isinstance(desc, str) or not desc.strip():
                raise ValueError(f'"steps[{idx}].description" must be a non-empty string.')

    def _plan_payload_to_edit_plan(self, data: dict) -> EditPlan:
        """Map validated JSON to EditPlan (orchestration-only; no model calls)."""
        root = self.project_root
        if root is None:
            raise RuntimeError("Project root is not set.")

        resolved: list[Path] = []
        for rel in data["affected_files"]:
            resolved.append(self._safe_project_path(str(rel).strip()))

        steps_out: list[PlanStep] = []
        for idx, step in enumerate(data["steps"]):
            title = str(step["title"]).strip()
            desc = str(step["description"]).strip()
            target = resolved[idx % len(resolved)]
            combined = f"{title}: {desc}"
            steps_out.append(
                PlanStep(order=idx + 1, target_file=target, description=combined)
            )

        return EditPlan(thought=str(data["thought"]).strip(), steps=steps_out)

    def _safe_project_path(self, rel: str) -> Path:
        """Resolve a user/model path strictly under project root."""
        candidate = (self.project_root / rel).resolve()
        root_r = self.project_root.resolve()
        try:
            candidate.relative_to(root_r)
        except ValueError as exc:
            raise ValueError(f"Path escapes project root: {rel!r}") from exc
        return candidate
