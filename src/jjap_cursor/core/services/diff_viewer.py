"""Diff Viewer module for Jjap-Cursor.

[변경 미리보기 엔진 - v8.1 전용 디프 뷰어]
# HISTORY: (AI 오답노트) [v8.0] LLM이 코드 전체를 통째로 덮어쓰는 과정에서 기존 개발자의 소중한 로직을 유실시키는 대참사 발생.
# HISTORY: -> 수술 직전 무조건 변경 사항을 인간 눈으로 강제 검증하도록 Unified Diff 시각화 부서 독립 조치 완료. (토큰 최적화용 압축본)
"""

from __future__ import annotations

import difflib

from ..types import PatchTransaction

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
# INFO: 평소에는 False로 꺼두고, 디프 렌더링 과정에서 에러 추적이 필요할 때 True로 켭니다.
DEBUG_MODE = True

# INFO: 이전 클래스 계약:
# INFO: class DiffViewer:
# INFO:     def __init__(self): ...
# INFO:     def render(self, transaction: PatchTransaction) -> None: ...
# INFO: 현재는 모듈 top-level 함수 render_patch_diff 로 전환됨.


def render_patch_diff(transaction: PatchTransaction) -> None:
    """PatchTransaction 내부의 모든 패치 요소를 순회하며 Unified Diff 프리뷰를 터미널에 출력합니다."""

    # 🎛️ On/Off 디버깅 로그 도배 규칙 준수
    if DEBUG_MODE:
        print(f"📊 [DEBUG] [DiffViewer] 디프 렌더링 엔진 가동 시작. 트랜잭션 ID: {transaction.correlation_id}")
        print(f"📊 [DEBUG] [DiffViewer] 검사 대상 패치 총 개수: {len(transaction.patches)}개")

    if not transaction.patches:
        print("\n📊 [Diff Preview] ⚠️ 알림: 이번 트랜잭션에 포함된 파일 변경 내역이 전혀 없습니다.")
        return

    print("\n🔍 ========================================================")
    print("🔍 짭커서 초정밀 수술 대기 변경 명세 (UNIFIED DIFF PREVIEW)")
    print("🔍 ========================================================")

    for idx, patch in enumerate(transaction.patches):
        file_path = patch.file_path

        if DEBUG_MODE:
            print(f"📊 [DEBUG] [DiffViewer] [{idx+1}] 순서 파일 디프 생성 중: {file_path}")

        # 1단계: 원래 파일 내용 읽기 (새로 생성되는 파일이면 빈 텍스트로 폴백 처리)
        original_text = ""
        if file_path.exists():
            try:
                original_text = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"🚨 [DiffViewer] 원본 파일 읽기 실패 ({file_path.name}): {exc}")
                original_text = patch.original  # 읽기 실패 시 AI가 준 원래 상태를 신뢰하고 진행
        else:
            if DEBUG_MODE:
                print(f"📊 [DEBUG] [DiffViewer] 신규 생성 대상 파일 감지되었습니다.")

        # 2단계: 줄바꿈 기준으로 쪼개서 difflib에 먹일 수 있게 배열로 전환
        from_lines = original_text.splitlines(keepends=True)
        to_lines = patch.updated.splitlines(keepends=True)

        # 3단계: 파이썬 순정 difflib.unified_diff 출격
        diff_generator = difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"a/{file_path.name} (ORIGINAL)",
            tofile=f"b/{file_path.name} (UPDATED)",
            lineterm="",
        )

        diff_list = list(diff_generator)

        # 4단계: 터미널에 이쁘게 출력하기
        print(f"\n📂 [파일 타겟] {file_path}")
        print("-" * 50)

        if not diff_list:
            print("  (AI가 코드를 분석했으나, 기존 소스코드와 완벽히 일치하여 변경점이 없습니다.)")
            continue

        for line in diff_list:
            # 형님이 한눈에 알아보기 편하게 줄 첫 글자 기호에 따라 직관적인 시각화 도포
            if line.startswith("+") and not line.startswith("+++"):
                print(f"  🟢 {line.rstrip()}")  # 추가된 코드는 녹색/🟢 표시
            elif line.startswith("-") and not line.startswith("---"):
                print(f"  🔴 {line.rstrip()}")  # 삭제된 코드는 빨간색/🔴 표시
            elif line.startswith("@"):
                print(f"  🔵 {line.rstrip()}")  # 위치 정보(Hunk)는 파란색/🔵 표시
            else:
                print(f"    {line.rstrip()}")   # 변경 없는 일반 주변 코드는 들여쓰기만

    print("\n🔍 ========================================================")

    if DEBUG_MODE:
        print("📊 [DEBUG] [DiffViewer] 모든 파일 패치에 대한 디프 프리뷰 렌더링이 성공적으로 종료되었습니다.")
