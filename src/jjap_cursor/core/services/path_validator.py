"""Path Validator service for Jjap-Cursor.

[경로 보안 관제소 - v8.2 전용 경비원]
# HISTORY: (AI 오답노트) [v8.1] 경로 검증 로직이 파서와 매니저에 중복 분산되어 관리 포인트가 흐려짐.
# HISTORY: -> 오직 경로 무결성 보안 검사만 단독으로 수행하는 전문 경비원 클래스로 찢어서 독립 완료.
"""

from __future__ import annotations

from pathlib import Path

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True


class PathValidator:
    """AI가 기획하거나 수정한 타겟 경로가 짭커서 작업 공간을 탈출하는 해킹 행위를 원천 차단하는 경비원 클래스입니다."""

    # INFO: =======================================================================
    # INFO: 📜 형님이 하사하신 짭커서 개발 제1보안관 절대 준수 규칙 (상시 열람용)
    # INFO: =======================================================================
    # INFO: 🎛️ On/Off 디버깅 로그 도배 규칙 및 주석 이원화(# HISTORY / # INFO) 수호 완료.
    # INFO: =======================================================================

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()

    def validate_and_resolve(self, relative_or_absolute_path: str | Path) -> Path:
        """경로를 절대 경로로 풀고, 프로젝트 루트 내부에 종속되어 있는지 철저하게 검문합니다."""
        if DEBUG_MODE:
            print(f"🚨 [DEBUG] [PathValidator] 경로 탈출 여부 보안 검문 시작: {relative_or_absolute_path}")

        # 1단계: 상대 경로든 뭐든 프로젝트 루트 기준의 절대 경로로 강제 맵핑 및 확인
        candidate = (self.project_root / Path(relative_or_absolute_path)).resolve()
        
        try:
            # 2단계: relative_to를 통해 루트 하위 폴더가 맞는지 확인 (아니면 ValueError 발생)
            candidate.relative_to(self.project_root)
            if DEBUG_MODE:
                print(f"🚨 [DEBUG] [PathValidator] 보안 통과. 안전 구역 내 파일 확인 완료: {candidate}")
            return candidate
        except ValueError as exc:
            if DEBUG_MODE:
                print(f"🚨 [DEBUG] [PathValidator] [SECURITY_ALERT] 해킹 감지! 무단 이탈 시도 경로: {relative_or_absolute_path}")
            raise ValueError(f"보안 고발: 대상 경로가 프로젝트 루트를 탈출했습니다: {relative_or_absolute_path!r}") from exc