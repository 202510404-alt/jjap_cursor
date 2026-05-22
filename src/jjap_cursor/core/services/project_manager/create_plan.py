"""AI Edit Plan generation function with 3-step self-repair loop.

[기획서 수령처 - v8.2 단일 함수 엔진]
# HISTORY: (AI 오답노트) [v8.1] Gemini가 뱉은 마크다운(```json)을 정화하지 못해 json.loads() 단계에서 무조건 터지던 버그 발생.
# HISTORY: -> 독립 함수로 격리하고 공용 TextSanitizer 방어벽을 완벽 장착하여 지뢰 원천 봉쇄 성공.
"""

from __future__ import annotations

import json
from pathlib import Path

from ...errors import PlanningError
from ...interfaces.context_builder import ContextBuilder
from ...interfaces.gemini_client import GeminiClient
from ..text_sanitizer import clean_markdown
from ..plan_validator import validate_plan_schema

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True


def create_edit_plan(
    user_query: str,
    gemini_client: GeminiClient | None,
    context_builder: ContextBuilder | None
) -> dict:
    """Gemini에게 질문을 던져 기획서 장부를 받아오고, 깨끗하게 소독 및 검사하여 파이썬 딕셔너리로 반환합니다."""
    if context_builder is None or gemini_client is None:
        raise RuntimeError("기획서 생성 실패: 핵심 AI 엔진 부품이 주입되지 않았습니다.")

    planning_ctx = context_builder.build_planning_context(user_query)
    last_error: str | None = None

    # 🔄 형님이 설계하신 무결점 3회 자율 복구 오뚝이 루프 기동
    for i in range(3):
        try:
            raw = gemini_client.generate_edit_plan(
                planning_context=planning_ctx,
                user_query=user_query,
                repair_feedback=last_error,  
            )
            
            # ⚡ [지뢰 해결]: 찢어놓은 청소부 부서(TextSanitizer)로 마크다운 오염물 즉시 도려내기!
            cleaned_json_str = clean_markdown(raw)
            data = json.loads(cleaned_json_str)
            
            # ⚡ [지뢰 해결]: 찢어놓은 영양사 부서(PlanValidator)로 심층 스키마 현미경 검사!
            validate_plan_schema(data)
            return data
            
        except (json.JSONDecodeError, ValueError, TypeError, RuntimeError) as exc:
            last_error = f"[Attempt {i+1}/3] {type(exc).__name__}: {exc}"
            if DEBUG_MODE:
                print(f"⚠️ [DEBUG] [create_plan] 기획서 오염 감지. 자율 수리 루프 재기동 원인: {exc}")

    raise PlanningError(f"최종 기획서 생성 실패 (3회 복구 루프 소진). 마지막 에러 내용: {last_error}")