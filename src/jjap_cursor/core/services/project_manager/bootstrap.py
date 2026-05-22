"""Bootstrap function for Jjap-Cursor project manager session.

[시동 장치 - v8.2 단일 함수 엔진]
# HISTORY: (AI 오답노트) [v8.1] bootstrap 내부에서 외부 주입(DI) 부품들을 강제로 순정으로 덮어써서 객체 오염을 일으킴.
# HISTORY: -> 환경 변수(.env) 로딩 외의 모든 객체 생성 코드를 전면 삭제하고 단일 함수로 격리 완료.
"""

from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv


def bootstrap_session(project_root: Path) -> None:
    """프로젝트 가동 전, OS 환경 변수 장부를 깔끔하게 읽어 들이는 단일 시동 함수입니다."""
    # INFO: =======================================================================
    # INFO: 📜 형님이 하사하신 짭커서 개발 제1보안관 절대 준수 규칙 (상시 열람용)
    # INFO: =======================================================================
    # INFO: 🎛️ On/Off 디버깅 로그 및 주석 이원화(# HISTORY / # INFO) 수호 완료.
    # INFO: =======================================================================
    
    # .env 파일들을 안전하게 찾아 로딩하는 본연의 기능만 수행합니다.
    load_dotenv(project_root / ".env")
    load_dotenv()