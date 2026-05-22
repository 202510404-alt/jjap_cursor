"""Main orchestration pipeline function for Jjap-Cursor request lifecycle.

[최종 파이프라인 결재관 - v8.2 단일 함수 엔진]
# HISTORY: (AI 오답노트) [v8.1] 클래스 안에서 지가 조립하고 지가 검사하고 다 하려다 스키마 오염으로 폭발함.
# HISTORY: -> 오직 부품들의 실행 순서 조율 및 사용자 승인 도장만 찍는 '순수 총괄 지휘관' 단일 함수로 완전 해탈 완료.
"""

from __future__ import annotations

from pathlib import Path

from ...interfaces.context_builder import ContextBuilder
from ...interfaces.gemini_client import GeminiClient
from ...types import ContextBundle, EditPlan, ValidationResult, PatchTransaction

# 🪓 분쇄 격리시킨 단일 함수 형제들 전격 영입!
from .bootstrap import bootstrap_session
from .sync_index import sync_project_index
from .create_plan import create_edit_plan
from .plan_payload_mapper import map_payload_to_edit_plan

# 🪓 3대 실무 부서 (v8.2 함수형) 영입!
from ..patch_parser import parse_llm_patch
from ..diff_viewer import render_patch_diff
from ..file_writer import apply_patch_transaction

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True

# INFO: 이전 run_jjap_pipeline 시그니처 (클래스 주입):
# INFO: def run_jjap_pipeline(..., patch_parser: LLMPatchParser, diff_viewer: DiffViewer, file_writer: AtomicFileWriter) -> ValidationResult
# INFO:     patch_parser.parse(raw_patch_response)
# INFO:     diff_viewer.render(transaction)
# INFO:     file_writer.apply(transaction)
# INFO: 현재는 parse_llm_patch / render_patch_diff / apply_patch_transaction 함수 직접 호출로 전환됨.


def run_jjap_pipeline(
    user_query: str,
    project_root: Path,
    gemini_client: GeminiClient,
    context_builder: ContextBuilder,
) -> ValidationResult:
    """형님이 하사하신 초정밀 8단계 무결점 오케스트레이션 파이프라인을 단일 함수로 총괄 집도합니다."""
    try:
        if DEBUG_MODE:
            print(f"👑 [DEBUG] [run_pipeline] 파이프라인 가동. 요청명: '{user_query}'")

        # [Step 1] 인덱스 동기화 (단일 함수 호출)
        sync_project_index(project_root)

        # [Step 2] Planning Stage (단일 함수 호출)
        print("🧠 [Step 2] 플래닝 에이전트 가동: 설계도(Plan) 제작 중...")
        plan_data = create_edit_plan(user_query, gemini_client, context_builder)
        edit_plan: EditPlan = map_payload_to_edit_plan(plan_data, project_root)

        # [Step 3] Context 정화 및 압축 (외부 주입 엔진 사용)
        print("🎯 [Step 3] 컨텍스트 엔진 가동: 알짜배기 소스코드 정화 및 실전 압축 중...")
        context_bundle: ContextBundle = context_builder.assemble(plan=edit_plan, user_query=user_query)

        # [Step 4] Execution Stage (Editor 모델 패치 요청)
        print("⚡ [Step 4] 에디터 에이전트 집도 시작: 코드 수정 패치 생성 중...")
        raw_patch_response = gemini_client.generate_code_patch(edit_plan, context_bundle)

        # [Step 5] Single Parsing Gate 통과 (전담 함수 사용)
        print("🛡️ [Step 5] 단일 파싱 검증 게이트 통과 중...")
        transaction: PatchTransaction = parse_llm_patch(project_root, raw_patch_response)

        # [Step 6] Unified Diff Preview (디자이너 함수 사용)
        print("\n🔍 [Step 6] === UNIFIED DIFF PREVIEW ===")
        render_patch_diff(transaction)

        # [Step 7] User Gate (CLI 승인 받기)
        answer = input("\n👉 형님, 위 패치 내역을 파일 시스템에 진짜 반영할까요? (y/N): ")
        if answer.strip().lower() not in ["y", "yes"]:
            print("\n🚫 형님, 요청에 따라 패치 적용을 긴급 취소하고 상황을 종료합니다.")
            return ValidationResult(ok=False, errors=["User cancelled patch application."])

        # [Step 8] Transaction Apply & Atomic Write (원자적 쓰기 함수 사용)
        print("\n💾 [Step 8] 무결성 수술실 입장: OS 레벨 원자적 쓰기 및 트랜잭션 반영 시작...")
        write_result = apply_patch_transaction(transaction)

        if not write_result.ok:
            return write_result

        print("🎉 ✅ [수술 대성공] 형님, 요청하신 소스코드 패치가 무결하게 반영되었습니다!")
        return ValidationResult(ok=True, errors=[])

    except Exception as exc:
        if DEBUG_MODE:
            print(f"👑 [DEBUG] [run_pipeline] 하부 파이프라인 엔진 대붕괴 발생! 범인 검거: {exc}")
        return ValidationResult(ok=False, errors=[str(exc)])
