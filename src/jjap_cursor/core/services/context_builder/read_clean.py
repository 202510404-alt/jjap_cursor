"""Read project source files and strip INFO comments / DEBUG blocks."""

from __future__ import annotations

from pathlib import Path

DEBUG_MODE = True


def read_and_clean_file(project_root: Path, relative_path: str | Path) -> str:
    # ⚡ 형님의 초정밀 최적화 특명: # INFO: 주석뿐만 아니라 if DEBUG_MODE: 블록까지 싹둑 잘라내는 정화 장치
    # HISTORY: 긴 디버깅 로그 출문들이 AI 토큰을 낭비하던 문제를 줄 단위 상태 머신 역추적 방식을 도입해 완벽 해결.

    full_path = project_root / Path(relative_path)
    if not full_path.exists():
        if DEBUG_MODE:
            print(f"[DEBUG] ContextBuilder: ⚠️ 파일을 찾을 수 없어 빈 문자열 리턴 -> {full_path}")
        return ""

    with open(full_path, "r", encoding="utf-8") as f:
        origin_lines = f.readlines()

    cleaned_lines = []
    skipping_debug_block = False
    debug_indent_level = 0

    for line in origin_lines:
        stripped = line.strip()

        # 1. 디버깅 로그 블록의 시작 감지 (검열 개시)
        if stripped.startswith("if DEBUG_MODE:") or stripped.startswith("if self.DEBUG_MODE:"):
            skipping_debug_block = True
            # 현재 if문의 들여쓰기 깊이(공백 개수)를 구해서 블록의 경계선으로 삼습니다.
            debug_indent_level = len(line) - len(line.lstrip())
            continue

        # 2. 디버깅 로그 블록 내부를 달리는 중이라면 AI에게 안 보여주고 탈락시킴
        if skipping_debug_block:
            if stripped:  # 빈 줄이 아닐 때만 들여쓰기 검사
                current_indent = len(line) - len(line.lstrip())
                # 들여쓰기가 원래 if문 이하로 돌아왔다면 블록이 끝난 것입니다.
                if current_indent <= debug_indent_level:
                    skipping_debug_block = False
                else:
                    continue  # 디버깅 로그 내용이므로 패스!

        # 3. # INFO: 사람용 설명 주석 칼같이 도려내기
        if " # INFO:" in line:
            line = line.split(" # INFO:")[0] + "\n"

        cleaned_lines.append(line)

    return "".join(cleaned_lines)
