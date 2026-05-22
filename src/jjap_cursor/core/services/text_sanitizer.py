"""Text Sanitizer utility for Jjap-Cursor.

[공용 텍스트 정화 장치 - v8.2 전용 청소부]
# HISTORY: (AI 오답노트) [v8.1] 마크다운 정화 코드가 파서 내부에 갇혀있어서, project_manager의 create_plan 단계에서 JSON이 깨지는 버그 방치됨.
# HISTORY: -> 전역에서 재사용 가능한 독립 유틸리티로 완전히 살점을 찢어 격리 조치 완료.
"""

from __future__ import annotations

import re

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True

# INFO: 이전 클래스 계약:
# INFO: class TextSanitizer:
# INFO:     @staticmethod
# INFO:     def clean_markdown(text: str) -> str: ...
# INFO: 현재는 모듈 top-level 함수 clean_markdown 으로 전환됨.


def clean_markdown(text: str) -> str:
    """날것의 AI 텍스트 응답을 받아 순수한 JSON 형태의 문자열만 핀포인트로 발라냅니다."""
    text_stripped = text.strip()

    if DEBUG_MODE:
        print(f"🧹 [DEBUG] [TextSanitizer] 정화 공정 가동. 입력 텍스트 길이: {len(text_stripped)}")

    # ```json [내용] ``` 구조를 발라내는 초정밀 정규식 가동
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text_stripped)
    if match:
        if DEBUG_MODE:
            print("🧹 [DEBUG] [TextSanitizer] 표준 ```json 마크다운 패턴 검지 및 정화 성공.")
        return match.group(1).strip()

    # 혹시 json 표시 없이 그냥 ``` [내용] ``` 만 썼을 때의 Fallback 안전망
    match_fallback = re.search(r"```\s*([\s\S]*?)\s*```", text_stripped)
    if match_fallback:
        if DEBUG_MODE:
            print("🧹 [DEBUG] [TextSanitizer] 폴백 ``` 일반 마크다운 패턴 검지 및 정화 성공.")
        return match_fallback.group(1).strip()

    if DEBUG_MODE:
        print("🧹 [DEBUG] [TextSanitizer] 마크다운 감싸기 기호가 없는 순수 텍스트 상태로 판단되어 그대로 통과시킵니다.")
    return text_stripped
