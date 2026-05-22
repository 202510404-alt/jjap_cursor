"""Map validated plan JSON to python strong-typed EditPlan entity.

[기획서 바느질공 - v8.2 단일 함수 엔진]
# HISTORY: (AI 오답노트) [v8.1] 매니저 내부에 중복된 경로 검사 코드가 수동으로 돌아가서 DRY 원칙을 위배함.
# HISTORY: -> 전문 보안관(PathValidator)을 전격 고용하여 경로 검증 책임을 100% 이양함.
"""

from __future__ import annotations

from pathlib import Path
from ...types import EditPlan, PlanStep
from ..path_validator import validate_and_resolve


def map_payload_to_edit_plan(data: dict, project_root: Path) -> EditPlan:
    """순수 JSON 기획 장부를 읽어, 안전 검증된 절대 경로가 장착된 EditPlan 객체로 팩킹합니다."""
    resolved_paths: list[Path] = []
    for rel_path in data["affected_files"]:
        # ⚡ [지뢰 해결]: 매니저 내부 중복 로직 전면 삭제 후, 경비원에게 안전한 절대 경로 정산 위임!
        resolved_paths.append(validate_and_resolve(project_root, str(rel_path).strip()))

    steps_out: list[PlanStep] = []
    for idx, step in enumerate(data["steps"]):
        title = str(step.get("title", "수정")).strip()
        desc = str(step.get("description", "")).strip()
        
        # 순회하며 타겟 파일 매칭
        target_file = resolved_paths[idx % len(resolved_paths)]
        combined_desc = f"{title}: {desc}"
        
        steps_out.append(
            PlanStep(order=idx + 1, target_file=target_file, description=combined_desc)
        )

    return EditPlan(thought=str(data["thought"]).strip(), steps=steps_out)