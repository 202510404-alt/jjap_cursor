"""Project Manager module unified entrypoint using Single Function Files."""

from __future__ import annotations

from pathlib import Path

from ...interfaces.project_manager import ProjectManager
from ...interfaces.context_builder import ContextBuilder
from ...interfaces.gemini_client import GeminiClient
from ...types import ValidationResult

from .bootstrap import bootstrap_session
from .run_pipeline import run_jjap_pipeline

# INFO: 이전 DefaultProjectManager 장비 주입:
# INFO:     self._file_scanner = FileScanner(project_root=project_root)
# INFO:     run_jjap_pipeline(..., file_scanner=self._file_scanner)
# INFO: 현재는 sync_project_index(project_root) 가 scan_project / write_scan_outputs 를 직접 호출함


class DefaultProjectManager(ProjectManager):
    """형님의 '단일 함수 분쇄 특명'을 완수하기 위해, 내부에 단 한 줄의 자체 로직도 두지 않고
    오직 쪼개진 단일 함수 부품들을 매핑하여 호출하는 외피(Facade) 클래스입니다.
    """

    def __init__(self, project_root: Path, gemini_client: GeminiClient, context_builder: ContextBuilder):
        self.project_root = project_root
        self._gemini = gemini_client
        self._context_builder = context_builder

    def bootstrap(self, project_root: Path) -> None:
        bootstrap_session(project_root)
        self.project_root = project_root

    def run(self, user_query: str) -> ValidationResult:
        return run_jjap_pipeline(
            user_query=user_query,
            project_root=self.project_root,
            gemini_client=self._gemini,
            context_builder=self._context_builder,
        )
