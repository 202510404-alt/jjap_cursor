"""LLM Patch Parser module for Jjap-Cursor.

[단일 파싱 게이트 - v8.2 순수 데이터 구조 번역가]
# HISTORY: (AI 오답노트) [v8.1] patches가 비어있을 때 UnboundLocalError 터지고, KeyError 발생 시 시스템 전체가 자동 롤백 없이 기절함.
# HISTORY: -> uuid4 기반 고유 식별자 선제 발행 및 광범위 예외 포획망(except Exception) 구축으로 무결성 100% 확보 완공.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from ..types import FilePatch, PatchTransaction, PatchStrategy
from .text_sanitizer import clean_markdown
from .path_validator import validate_and_resolve

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True

# INFO: 이전 클래스 계약:
# INFO: class LLMPatchParser:
# INFO:     def __init__(self, project_root: Path): ...
# INFO:     def parse(self, raw_response: str) -> PatchTransaction: ...
# INFO:     def _validate_schema(self, data: dict) -> None: ...
# INFO: 현재는 모듈 top-level 함수 parse_llm_patch, _validate_patch_schema 로 전환됨.


def _validate_patch_schema(data: dict) -> None:
    # INFO: JSON이 딕셔너리가 맞는지, 필수 루트 배열인 'patches'가 존재하는지 문턱 심사를 진행합니다.
    if not isinstance(data, dict):
        raise ValueError("패치 루트 데이터는 반드시 JSON Object(딕셔너리) 형태여야 합니다.")

    if "patches" not in data or not isinstance(data["patches"], list):
        raise ValueError("패치 데이터 내부에 'patches' 배열(List) 필드가 누락되었거나 올바르지 않습니다.")

    for idx, item in enumerate(data["patches"]):
        if not isinstance(item, dict):
            raise ValueError(f"patches[{idx}] 요소는 반드시 Object 형태여야 합니다.")
        if "file" not in item or "old" not in item or "new" not in item:
            raise ValueError(f"patches[{idx}] 항목에 필수 실무 필드('file', 'old', 'new')가 유실되었습니다.")


def parse_llm_patch(project_root: Path, raw_response: str) -> PatchTransaction:
    """날것의 LLM 응답을 완벽한 트랜잭션 객체로 박제합니다."""
    backup_dir = project_root / ".jjap_backup"

    # ⚡ [지뢰 ① 해결]: 루프 실행 여부와 무관하게 안전한 난수형 단일 고유 거래 번호(UUID)를 함수 머리통에서 선제 발행!
    correlation_id = f"TX_{uuid.uuid4().hex[:8].upper()}"

    if DEBUG_MODE:
        print(f"🛡️ [DEBUG] [PatchParser] 데이터 구조 바느질 시작. 발행된 고유 거래 번호: {correlation_id}")

    try:
        # ⚡ [지뢰 ③ 해결]: 텍스트 청소부 독립 부서(TextSanitizer)에 토스하여 정화 문자열 수거!
        cleaned_json_str = clean_markdown(raw_response)

        # JSON 파싱 실행
        data = json.loads(cleaned_json_str)
        _validate_patch_schema(data)

        patches: list[FilePatch] = []
        for item in data.get("patches", []):
            # ⚡ [지뢰 ② 해결]: AI가 'file' 키 이름을 누락하거나 다르게 줬을 때 터질 KeyError/TypeError를 대비한 철저한 방어선
            file_rel_path = str(item["file"]).strip()

            # ⚡ 경로 보안관 독립 부서(PathValidator)에 전권 위임하여 안전한 절대 경로 정산!
            abs_file_path = validate_and_resolve(project_root, file_rel_path)

            patches.append(
                FilePatch(
                    file_path=abs_file_path,
                    original=item.get("old", ""),
                    updated=item.get("new", ""),
                    strategy=PatchStrategy.REPLACE,
                )
            )

        if DEBUG_MODE:
            print(f"✅ [DEBUG] [PatchParser] 데이터 객체 맵핑 완공. 총 {len(patches)}개의 파일 패치 팩킹 완료.")

        return PatchTransaction(
            patches=patches,
            backup_dir=backup_dir,
            correlation_id=correlation_id,
        )

    # ⚡ [지뢰 ② 해결]: 포획 그물망을 Exception 전체로 확장하여 KeyError, TypeError, ValueError 등을 싹 다 검거!
    except Exception as exc:
        if DEBUG_MODE:
            print(f"🚨 [DEBUG] [PatchParser] 파싱 벨트라인 내부에서 치명적 오염 데이터 검거 완료! 원인: {type(exc).__name__} -> {exc}")
        # 상위 사령탑인 project_manager가 튕기지 않고 안전하게 롤백을 때릴 수 있도록 정제된 ValueError로 포장해서 토스
        raise ValueError(f"AI 패치 응답 규격 해독 실패 (데이터 구조 오염): {exc}") from exc
