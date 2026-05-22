"""Project Manager module unified entrypoint using Single Function Files."""

from __future__ import annotations

from pathlib import Path
from src.jjap_cursor.core.interfaces.project_manager import ProjectManager
from src.jjap_cursor.core.interfaces.context_builder import ContextBuilder
from src.jjap_cursor.core.interfaces.gemini_client import GeminiClient

from src.jjap_cursor.core.services.project_manager.bootstrap import bootstrap_session
from src.jjap_cursor.core.services.project_manager.run_pipeline import run_jjap_pipeline
from src.jjap_cursor.core.services.file_scanner import FileScanner
from src.jjap_cursor.core.services.patch_parser import LLMPatchParser
from src.jjap_cursor.core.services.diff_viewer import DiffViewer
from src.jjap_cursor.core.services.file_writer import AtomicFileWriter


class DefaultProjectManager(ProjectManager):
    """형님의 '단일 함수 분쇄 특명'을 완수하기 위해, 내부에 단 한 줄의 자체 로직도 두지 않고 
    오직 쪼개진 단일 함수 부품들을 매핑하여 호출하는 외피(Facade) 클래스입니다.
    """

    def __init__(self, project_root: Path, gemini_client: GeminiClient, context_builder: ContextBuilder):
        self.project_root = project_root
        self._gemini = gemini_client
        self._context_builder = context_builder
        
        # 외부 부서 장비 주입
        self._file_scanner = FileScanner(project_root=project_root)
        self._patch_parser = LLMPatchParser(project_root=project_root)
        self._diff_viewer = DiffViewer()
        self._file_writer = AtomicFileWriter()

    def bootstrap(self, project_root: Path) -> None:
        # 오직 세션 환경변수 로딩 단일 함수에 위임
        bootstrap_session(project_root)
        self.project_root = project_root

    def run(self, user_query: str) -> any:
        # 오직 전체 파이프라인 실행 단일 함수에 모든 부품을 던져 위임
        return run_jjap_pipeline(
            user_query=user_query,
            project_root=self.project_root,
            gemini_client=self._gemini,
            context_builder=self._context_builder,
            file_scanner=self._file_scanner,
            patch_parser=self._patch_parser,
            diff_viewer=self._diff_viewer,
            file_writer=self._file_writer
        )