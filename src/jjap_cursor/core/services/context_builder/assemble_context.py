"""Assemble final ContextBundle for execution stage."""

from __future__ import annotations

from ...types import ContextBundle, EditPlan
from .collect_related import collect_related_symbols
from .collect_target import collect_target_context
from .state import ContextBuilderState

DEBUG_MODE = True


def assemble_context(
    state: ContextBuilderState,
    plan: EditPlan,
    user_query: str,
) -> ContextBundle:
    # INFO: 정화된 핵심 코드들과 메타데이터들을 뭉쳐서 최종적으로 Gemini가 먹기 좋은 묶음 장부로 조립합니다.
    if DEBUG_MODE:
        print("[DEBUG] ContextBuilder: 📦 최종 AI 컨텍스트 보따리(ContextBundle) 조립 개시")

    target_context = collect_target_context(state, plan, user_query)
    related_symbols = collect_related_symbols(state, plan)

    skeletons_summary = []
    for slc in target_context:
        skeletons_summary.append(
            f"File: {slc.file_path}\n" + "-" * 30 + f"\n{slc.content[:200]}...\n"
        )

    return ContextBundle(
        total_tokens=sum(s.token_cost for s in target_context),
        system_prompt="당신은 로컬 소스코드를 정밀 타격 수정하는 짭커서 에이전트 엔진입니다.",
        target_context=target_context,
        related_symbols=related_symbols,
        facts=[f"사용자 요청 질의어: {user_query}"],
        skeletons=skeletons_summary,
    )
