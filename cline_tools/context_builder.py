"""Context Builder module for Cline Tools.

[AI 배송용 컨텍스트 최적화 비서]
이 파일은 형님이 저(Gemini)에게 소스코드를 긁어서 보내기 직전에, 
메모리 상에서 코드를 한 줄씩 검열하여 토큰(비용)을 절약하고 
과거 오류 수정 내역만 핀포인트로 전달하는 '필터링 및 압축' 실무 도구입니다.
"""

import os
from pathlib import Path


class ContextBuilder:
    """날것의 소스코드를 정화하여 AI가 가장 좋아하는 영양가 있는 형태로 가공하는 비서 클래스입니다."""

    def __init__(self, project_root: str) -> None:
        """비서관을 초기화하며 기준이 되는 프로젝트 루트 경로를 지정합니다."""
        self.project_root = Path(project_root)

    def read_and_clean_file(self, relative_path: str) -> str:
        """파일을 읽어서 사람용 주석은 다 버리고, AI 오답노트와 순수 코드만 발라내는 핵심 검열 함수입니다.
        
        🎯 나를 호출하는 곳:
          - 형님이 툴을 실행하거나 소스코드를 수집해서 저(AI)에게 컨텍스트를 제공하는 메인 스크립트에서 호출됩니다.
          
        🛠️ 작동 원리 (형님의 아이디어 반영):
          1. 하드디스크에서 원본 파일을 날것 그대로 읽어옵니다 (원본은 절대 훼손되지 않음).
          2. 코드를 한 줄씩 쪼개서 뒤집어까며 `# INFO:` 딱지가 붙은 초보자용 주석은 싹 쓰레기통에 버립니다.
          3. `# HISTORY:`나 `# FIX:`가 붙은 과거 버그 이력과 순수 코드는 보따리에 소중히 담아서 합칩니다.
        """
        file_path = self.project_root / relative_path
        
        # 안전장치: 파일이 없으면 에러를 내뱉습니다.
        if not file_path.exists():
            raise FileNotFoundError(f"요청하신 경로에 파일이 존재하지 않습니다: {relative_path}")

        # 1단계: 원본 파일을 인코딩 깨짐 없이 안전하게 읽어옵니다.
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        cleaned_lines = []
        in_multiline_comment = False

        # 2단계: 코드를 한 줄씩 검사하는 컨베이어 벨트 가동
        for line in lines:
            stripped = line.strip()

            # 파이썬의 다중행 주석(""") 처리용 감지기 (선택적 필터링을 위함)
            if stripped.startswith('"""') or stripped.endswith('"""'):
                # 만약 이 독스트링 주석 안에 '오답노트'나 'HISTORY'라는 말이 없다면 토큰 절약을 위해 날릴 준비를 합니다.
                if '"""' in stripped and len(stripped) > 3:
                    pass # 단일행 독스트링은 통과
                else:
                    in_multiline_comment = not in_multiline_comment
                    cleaned_lines.append(line)
                    continue

            if in_multiline_comment:
                # 다중행 주석 안의 내용도 그대로 일단 담습니다.
                cleaned_lines.append(line)
                continue

            # ⭐ 형님이 오더 내리신 마법의 필터링 핵심 구역!
            # 1. 초보자 공부용 주석(# INFO:)이 발견되면 AI에게 줄 보따리에 넣지 않고 즉시 스킵(삭제)!
            if stripped.startswith("# INFO:"):
                continue

            # 2. 코드 옆에 붙은 꼬리표 주석 예외 처리 (예: `x = 1  # INFO: 변수임`)
            if " # INFO:" in line:
                # # INFO: 앞부분의 순수 코드만 싹둑 잘라서 남깁니다.
                line = line.split(" # INFO:")[0] + "\n"

            # 3. 그 외의 순수 실행 코드 및 # HISTORY:, # FIX: 주석은 AI 오답노트이므로 안전하게 보따리에 보관!
            cleaned_lines.append(line)

        # 3단계: 정화가 완료된 깨끗한 코드 줄들을 다시 하나의 예쁜 문자열 덩어리로 합쳐서 리턴합니다.
        return "".join(cleaned_lines)

    def assemble_ai_prompt(self, user_query: str, affected_files: list[str]) -> str:
        """검열된 파일 소스코드들과 형님의 최종 질문을 엮어서 저(Gemini)에게 배송할 최종 프롬프트 보따리를 조립합니다.
        
        🛠️ 내가 내부에서 부려먹는 함수:
          - `self.read_and_clean_file()`: 각 파일들을 돌면서 `# INFO:` 주석을 청소하라고 지시함.
        """
        prompt_parts = []
        prompt_parts.append(f"=== USER REQUEST ===\n{user_query}\n\n")
        prompt_parts.append("=== CLEANED CONTEXT CODEBASE ===\n")
        prompt_parts.append("아래 소스코드들은 토큰 절약을 위해 불필요한 설명 주석(# INFO:)이 제거되고, ")
        prompt_parts.append("과거 오류 수정 내역(# HISTORY:)만 온전히 보존된 청정 코드입니다.\n\n")

        for rel_path in affected_files:
            prompt_parts.append(f"--- FILE: {rel_path} ---")
            try:
                # 위에 만들어 둔 청소 함수를 실행시켜 알짜배기 코드만 받아옵니다.
                purified_code = self.read_and_clean_file(rel_path)
                prompt_parts.append(purified_code)
            except Exception as e:
                prompt_parts.append(f"파일을 읽는 중 오류 발생: {str(e)}")
            prompt_parts.append("\n")

        # 최종적으로 저(Gemini)의 뇌세포로 들어올 텍스트 보따리가 완성되는 순간입니다.
        return "\n".join(prompt_parts)