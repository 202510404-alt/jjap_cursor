"""Plan Validator service for Jjap-Cursor.

[기획서 심층 검문소 - v8.2 전용 영양사]
# HISTORY: (AI 오답노트) [v8.1] steps가 배열인지만 보고 내부를 검사 안 해서, [null]이나 오염 데이터가 침투 시 하부 파이프라인이 연쇄 크래시 나던 버그 방치됨.
# HISTORY: -> 오직 기획서 스키마 무결성만 현미경 심사하는 독립 부서로 찢어서 격리 완료.
"""

from __future__ import annotations

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True


class PlanValidator:
    """Gemini가 뱉어낸 JSON 기획서 규격을 솜방망이가 아닌 철퇴로 심사하는 전문 검문소 클래스입니다."""

    # INFO: =======================================================================
    # INFO: 📜 형님이 하사하신 짭커서 개발 제1보안관 절대 준수 규칙 (상시 열람용)
    # INFO: =======================================================================
    # INFO: 형님의 3대 절대 규칙(# HISTORY, # INFO, DEBUG_MODE 원터치 차단막) 완벽 수호 완료.
    # INFO: =======================================================================

    @staticmethod
    def validate_plan_schema(data: object) -> None:
        """기획서 데이터를 현미경 검사하여 1바이트라도 오염 발견 시 ValueError를 던져 자율 수리 루프를 깨웁니다."""
        if DEBUG_MODE:
            print("🧠 [DEBUG] [PlanValidator] 기획서 스키마 심층 문턱 검사 가동.")

        if not isinstance(data, dict):
            raise ValueError("기획서 루트 데이터는 반드시 JSON Object(딕셔너리) 형태여야 합니다.")

        thought = data.get("thought")
        if not isinstance(thought, str) or not thought.strip():
            raise ValueError('기획 장부의 필수 필드인 "thought"(작업 생각)가 유실되었거나 문자열이 아닙니다.')

        files = data.get("affected_files")
        if not isinstance(files, list) or len(files) == 0:
            raise ValueError('기획 장부의 필수 필드인 "affected_files"(영향받는 파일 목록)이 비어있거나 배열이 아닙니다.')

        steps = data.get("steps")
        if not isinstance(steps, list) or len(steps) == 0:
            raise ValueError('기획 장부의 필수 필드인 "steps"(수정 단계 목록)가 비어있거나 배열이 아닙니다.')

        # ⚡ [지뢰 ③ 완벽 해결]: 내부 요소까지 돋보기 들고 심층 순회 검사!
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"기획서 steps[{idx}] 항목이 올바른 Object 형태가 아닙니다. 오염 데이터 감지됨.")
            
            title = step.get("title")
            if title is not None and not isinstance(title, (str, int)):
                raise ValueError(f"기획서 steps[{idx}]의 title 필드 타입이 문자열이 아닙니다.")
                
            desc = step.get("description")
            if desc is not None and not isinstance(desc, (str, int)):
                raise ValueError(f"기획서 steps[{idx}]의 description 필드 타입이 문자열이 아닙니다.")

        if DEBUG_MODE:
            print("🧠 [DEBUG] [PlanValidator] 기획서 심층 무결성 검사 무사 통과. 청정 데이터 판정 완료.")