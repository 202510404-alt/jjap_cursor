import os
from pathlib import Path
from dataclasses import dataclass
from ..interfaces.context_builder import ContextBuilder
from ..types import BudgetPriority, ContextBundle, EditPlan, SymbolSlice

# 🎛️ 규칙 1: On/Off 디버깅 로그 도배를 위한 스위치 장착
DEBUG_MODE = True

class DefaultContextBuilder(ContextBuilder):
    # INFO: 형님이 주신 외부 클라인 툴즈의 초정밀 주석 검열 엔진을 이식한 짭커서 공식 컨텍스트 비서입니다.
    # INFO: 하드디스크의 소스코드를 읽을 때 # INFO: 주석과 if DEBUG_MODE: 로그 구역을 완전히 증발시킵니다.

    def __init__(self, project_root: Path) -> None:
        # INFO: 프로젝트의 최상위 경로를 주입받아 비서관 활동을 시작합니다.
        self.project_root = Path(project_root)
        self.max_tokens = 4000  # 기본 버젯 설정
        if DEBUG_MODE:
            print(f"[DEBUG] ContextBuilder: 초기화 완료. 프로젝트 루트 -> {self.project_root}")

    def set_budget(self, max_tokens: int) -> None:
        # INFO: AI가 먹을 수 있는 최대 토큰 통제 지지선을 설정합니다.
        self.max_tokens = max_tokens
        if DEBUG_MODE:
            print(f"[DEBUG] ContextBuilder: 토큰 버젯 변경됨 -> {self.max_tokens}")

    def _read_and_clean_file(self, relative_path: str) -> str:
        # ⚡ 형님의 초정밀 최적화 특명: # INFO: 주석뿐만 아니라 if DEBUG_MODE: 블록까지 싹둑 잘라내는 정화 장치
        # HISTORY: 긴 디버깅 로그 출문들이 AI 토큰을 낭비하던 문제를 줄 단위 상태 머신 역추적 방식을 도입해 완벽 해결.
        
        full_path = self.project_root / relative_path
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

    def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]:
        # INFO: AI가 수정하겠다고 지목한 1순위 핵심 파일들을 긁어모아 정밀 조각(Slice)으로 만듭니다.
        if DEBUG_MODE:
            print(f"[DEBUG] ContextBuilder: 🎯 타겟 컨텍스트 수집 시작 (계획 단계 수: {len(plan.steps)})")
            
        slices = []
        # 중복 로드를 방지하기 위한 안전 장부
        seen_files = set()
        
        for step in plan.steps:
            if step.file_path in seen_files:
                continue
            seen_files.add(step.file_path)
            
            # 외부 툴 방식의 정화 장치 가동!
            cleaned_code = self._read_and_clean_file(step.file_path)
            
            # jjap_types.py 내부의 SymbolSlice 데이터 규격에 맞춰 안전하게 포장
            slc = SymbolSlice(
                symbol_id=f"file::{step.file_path}",
                content=cleaned_code,
                priority=BudgetPriority.HIGH,
                file_path=Path(step.file_path)
            )
            slices.append(slc)
            
        return slices

    def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]:
        # INFO: 주변부 의존성이나 스켈레톤 지도를 분석하는 구역입니다. v8.1 명세에 따라 구조를 보존합니다.
        # HISTORY: 1차 MVP 단계에서는 빈 결괏값 구조만 유지하고 Phase C 증분 인덱서 결합 시 내부를 구체화하도록 기동 연기함.
        if DEBUG_MODE:
            print("[DEBUG] ContextBuilder: 🔗 주변 의존성 심볼 분석 중... (현재는 MVP 단계로 스킵)")
        return []

    def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle:
        # INFO: 정화된 핵심 코드들과 메타데이터들을 뭉쳐서 최종적으로 Gemini가 먹기 좋은 묶음 장부로 조립합니다.
        if DEBUG_MODE:
            print("[DEBUG] ContextBuilder: 📦 최종 AI 컨텍스트 보따리(ContextBundle) 조립 개시")
            
        target_context = self.collect_target_context(plan, user_query)
        related_symbols = self.collect_related_symbols(plan)
        
        # 주석과 로그가 지워진 순수 수술 도면 뼈대(Skeleton) 텍스트를 구성
        skeletons_summary = []
        for slc in target_context:
            skeletons_summary.append(f"File: {slc.file_path}\n" + "-"*30 + f"\n{slc.content[:200]}...\n")

        # 🎯 규칙 3: types.py의 ContextBundle 명세서 필드명 구조를 100% 준수하여 리턴
        return ContextBundle(
            total_tokens=0,  # 외부 토큰 카운터 결합 전 임시 세팅
            system_prompt="당신은 로컬 소스코드를 정밀 타격 수정하는 짭커서 에이전트 엔진입니다.",
            target_context=target_context,
            related_symbols=related_symbols,
            facts=[f"사용자 요청 질의어: {user_query}"],
            skeletons=skeletons_summary
        )