"""Concrete service implementations for core modules.

[물리적 코드 정밀 대조 완료 v8.2]
삼촌이 직접 제공해주신 각 패키지별 실제 구현 코드와 
main.py의 가동 형태를 실시간 돋보기 검증하여 완성한 무결점 대문 안내판입니다.
"""

from __future__ import annotations

# =====================================================================
# 📦 1. Phase 1 & 2 유틸리티 및 중간 로직 (services/ 바로 밑의 파일들)
# =====================================================================
from .text_sanitizer import clean_markdown
from .plan_validator import validate_plan_schema
from .path_validator import validate_and_resolve
from .patch_parser import parse_llm_patch
from .diff_viewer import render_patch_diff
from .file_writer import apply_patch_transaction

# =====================================================================
# 📂 2. file_scanner/ 패키지 출구에서 부품 수령
# =====================================================================
from .file_scanner import scan_project, write_scan_outputs, ScanArtifacts

# =====================================================================
# 📂 3. context_builder/ 패키지 출구에서 부품 수령
# =====================================================================
from .context_builder import assemble_context, build_planning_context

# =====================================================================
# 📂 4. gemini_client/ 패키지 출구에서 부품 수령 (클래스 껍데기 포함 확인됨)
# =====================================================================
from .gemini_client import generate_edit_plan, generate_code_patch, GeminiPlanClient, MODEL_NAME

# =====================================================================
# 📂 5. project_manager/ 패키지 하위의 순수 단일 함수 형제들
# =====================================================================
from .project_manager.bootstrap import bootstrap_session
from .project_manager.sync_index import sync_project_index
from .project_manager.create_plan import create_edit_plan
from .project_manager.run_pipeline import run_jjap_pipeline


# 💡 외부(main.py 등)에서 "services.함수명"으로 완벽히 뽑아 쓸 수 있도록 도장 찍은 허가 명단
__all__ = [
    # 유틸 및 패치 엔진 명단
    "clean_markdown",
    "validate_plan_schema",
    "validate_and_resolve",
    "parse_llm_patch",
    "render_patch_diff",
    "apply_patch_transaction",
    
    # 스캐너 패키지 명단
    "ScanArtifacts",
    "scan_project",
    "write_scan_outputs",
    
    # 컨텍스트 빌더 패키지 명단
    "assemble_context",
    "build_planning_context",
    
    # 제미나이 클라이언트 패키지 명단
    "GeminiPlanClient",
    "generate_edit_plan",
    "generate_code_patch",
    "MODEL_NAME",
    
    # 프로젝트 매니저 핵심 실무 단일 함수 체인 명단
    "bootstrap_session",
    "sync_project_index",
    "create_edit_plan",
    "run_jjap_pipeline",
]