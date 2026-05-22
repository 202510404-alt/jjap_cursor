"""Incremental indexing sync function for Jjap-Cursor.

[장부 동기화기 - v8.2 단일 함수 엔진]
# HISTORY: (AI 오답노트) [v8.1] 매니저 클래스 내부에 통으로 섞여 있어서 스캐너가 유실되었을 때 엉뚱한 런타임 에러를 뿜음.
# HISTORY: -> 독립 함수로 찢어 가동 조건을 명확히 선언하고 오류 추적성을 극대화함.
"""

from __future__ import annotations

from pathlib import Path

from ..file_scanner import scan_project, write_scan_outputs

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True

# INFO: 이전 sync_project_index 시그니처:
# INFO: def sync_project_index(file_scanner: FileScanner | None) -> None:
# INFO:     artifacts = file_scanner.scan_project()
# INFO:     file_scanner.write_outputs(artifacts)
# INFO: 현재는 project_root 만 받아 scan_project / write_scan_outputs 함수를 직접 호출함.


def sync_project_index(project_root: Path | None) -> None:
    """AI가 헛소리하지 않도록 소스코드의 변경 사항을 미리 스캔하여 장부를 최신화하는 함수입니다."""
    if project_root is None:
        raise RuntimeError("장부 동기화 실패: project_root 가 준비되지 않았습니다.")

    artifacts = scan_project(project_root)
    write_scan_outputs(project_root, artifacts)

    if DEBUG_MODE:
        symbol_count = len(artifacts.symbol_table.get("symbols", []))
        file_count = len(artifacts.skeletons)
        print(f"🔄 [DEBUG] [sync_index] 장부 최신화 완공 (파일: {file_count}개, 심볼: {symbol_count}개)")
