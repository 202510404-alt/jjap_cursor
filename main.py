# Requires Python 3.9+ (ast.unparse used)
#
# Dependencies for planning (Gemini):
#   pip install -r requirements.txt
#   # google-generativeai, python-dotenv
# Set GEMINI_API_KEY in .env or the environment.
# Optional: JJAP_QUERY overrides the default planning prompt.

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    """로봇(클래스) 없이 순수 함수 기계들로만 돌아가는 완벽한 메인 조종실"""
    root_path = Path(__file__).resolve().parent
    src_path = root_path / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # 💡 [진짜 핵심 교체]: 개별 기계들을 main에서 조잡하게 돌리지 않고, 
    # Phase 5에서 완공된 '통합 파이프라인 지휘관 함수'와 필요한 알맹이 부품들을 가져옵니다.
    from jjap_cursor.core.services.project_manager.run_pipeline import run_jjap_pipeline
    from jjap_cursor.core.services.gemini_client import GeminiPlanClient
    from jjap_cursor.core.services.context_builder import DefaultContextBuilder

    print("🚀 짭커서 v8.2 함수형 엔진 가동 완료!")

    # [Step 1] 삼촌이 입력한 질문(명령어) 환경 변수에서 안전하게 수령하기
    query = os.environ.get(
        "JJAP_QUERY",
        "Propose a minimal plan to improve logging in the project entry flow.",
    )

    # [Step 2] 기계 가동에 필요한 진짜 실무 AI 부품과 소스코드 수집기 부품 생성하기
    # (기존 불량 main.py에 완전히 누락되어 있던 핵심 일꾼 객체들입니다!)
    gemini_client = GeminiPlanClient()
    context_builder = DefaultContextBuilder(root_path)

    # [Step 3] ❌ 예전의 2개짜리 불량 함수 대신, 완벽한 통합 지휘관 함수를 실행합니다!
    try:
        print(f"[Jjap-Cursor] 통합 파이프라인 지휘관 가동 시작 (질문: '{query}')")
        
        # 🎯 실제 설계도 규칙대로 (질문, 폴더주소, AI부품, 수집기부품) 4개를 정확하게 찔러넣어 줍니다.
        result = run_jjap_pipeline(
            user_query=query,
            project_root=root_path,
            gemini_client=gemini_client,
            context_builder=context_builder
        )
        print(f"\n[Jjap-Cursor] 👑 파이프라인 가동 대성공! 결과 도장: {result}")
        
    except Exception as exc:
        print(f"[Jjap-Cursor] 🚨 실행 중 예상치 못한 치명적 오류 발생: {exc}")
        return


if __name__ == "__main__":
    main()