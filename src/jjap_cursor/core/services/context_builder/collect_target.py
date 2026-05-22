"""Collect highest-priority target file context from an edit plan."""

from __future__ import annotations

from pathlib import Path

from ...types import BudgetPriority, EditPlan, SymbolSlice
from .read_clean import read_and_clean_file
from .state import ContextBuilderState

DEBUG_MODE = True


def collect_target_context(
    state: ContextBuilderState,
    plan: EditPlan,
    user_query: str,
) -> list[SymbolSlice]:
    # INFO: AI가 수정하겠다고 지목한 1순위 핵심 파일들을 긁어모아 정밀 조각(Slice)으로 만듭니다.
    if DEBUG_MODE:
        print(f"[DEBUG] ContextBuilder: 🎯 타겟 컨텍스트 수집 시작 (계획 단계 수: {len(plan.steps)})")

    slices: list[SymbolSlice] = []
    seen_files: set[Path] = set()

    for step in plan.steps:
        target = step.target_file
        if target in seen_files:
            continue
        seen_files.add(target)

        cleaned_code = read_and_clean_file(state.project_root, target)

        slc = SymbolSlice(
            symbol_id=f"file::{target.as_posix()}",
            file_path=target,
            content=cleaned_code,
            token_cost=max(1, len(cleaned_code) // 4),
            priority="target",
        )
        slices.append(slc)

    return slices
