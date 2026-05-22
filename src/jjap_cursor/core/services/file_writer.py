"""Atomic File Writer module for Jjap-Cursor.

[무결성 수술실 - v8.1 전용 파일 원자적 저장 및 롤백 엔진]
# HISTORY: (AI 오답노트) [v8.0] 파일 저장 도중에 스크립트가 튕기거나 에러가 나면 코드가 반만 저장되어 소스코드가 깨지는 대참사 발생.
# HISTORY: -> 임시 파일 완공 후 os.replace() 스왑 및 에러 시 자동 롤백 하드웨어 장치 독립 조치 완료. (토큰 최적화용 압축본)
"""

from __future__ import annotations

import os
import py_compile
import shutil
from pathlib import Path

from ..types import PatchTransaction, ValidationResult

# 🎛️ [절대 규칙] 원터치 디버깅 로그 스위치 장착
DEBUG_MODE = True

# INFO: 이전 클래스 계약:
# INFO: class AtomicFileWriter:
# INFO:     def __init__(self): ...
# INFO:     def apply(self, transaction: PatchTransaction) -> ValidationResult: ...
# INFO:     def _validate_syntax(self, file_path: Path) -> None: ...
# INFO:     def _rollback(self, applied_files: list[tuple[Path, Path | None]]) -> None: ...
# INFO: 현재는 모듈 top-level 함수 apply_patch_transaction, _validate_syntax, _rollback 로 전환됨.


def _validate_syntax(file_path: Path) -> None:
    """수술실 사후 건강검진 - 파이썬 코드가 문법적으로 정상인지 불시 검문합니다."""
    if file_path.suffix == ".py":
        if DEBUG_MODE:
            print(f"💾 [DEBUG] [FileWriter] [사후검진] 파이썬 컴파일 정적 검사 시작: {file_path.name}")
        # 파이썬 순정 바이트코드 컴파일러 가동하여 문법 오타 검사
        py_compile.compile(str(file_path), doraise=True)
        if DEBUG_MODE:
            print(f"💾 [DEBUG] [FileWriter] [사후검진] 문법 무결성 인증 통과 완료.")


def _rollback(applied_files: list[tuple[Path, Path | None]]) -> None:
    """대피소 폴더에서 원본을 가져와 무결하게 롤백(Rollback)을 수행합니다."""
    print("🚑 [Rollback] 타임머신 가동: 수술 직전 상태로 코드를 되돌립니다...")

    for file_path, backup_path in reversed(applied_files):
        try:
            if backup_path and backup_path.exists():
                # 백업본이 존재하면 원본 경로에 그대로 다시 스왑 복원
                shutil.copy2(backup_path, file_path)
                if DEBUG_MODE:
                    print(f"🚑 [DEBUG] [FileWriter] [Rollback] 복구 완료: {file_path.name}")
                # 사용 완료된 백업 파일 청소
                backup_path.unlink()
            else:
                # 백업본이 없다는 건 애초에 없던 신규 파일이란 뜻이므로 삭제 조치
                if file_path.exists():
                    file_path.unlink()
                    if DEBUG_MODE:
                        print(f"🚑 [DEBUG] [FileWriter] [Rollback] 신규 생성 파일 삭제 완료: {file_path.name}")
        except Exception as rollback_exc:
            print(f"🚨 [FileWriter] 롤백 처리 도중 추가 연쇄 오류 발생 (치명적): {rollback_exc}")


def apply_patch_transaction(transaction: PatchTransaction) -> ValidationResult:
    """백업 디렉토리를 확보하고, 원자적 쓰기 공정을 거쳐 최종 패치를 파일 시스템에 각인시킵니다."""

    # 🎛️ On/Off 디버깅 로그 촘촘히 도배 시작 (cite 오타 수정 완료)
    if DEBUG_MODE:
        print(f"💾 [DEBUG] [FileWriter] 원자적 디스크 쓰기 미션 돌입. 트랜잭션 ID: {transaction.correlation_id}")
        print(f"💾 [DEBUG] [FileWriter] 백업 타겟 폴더 지정: {transaction.backup_dir}")

    applied_files: list[tuple[Path, Path | None]] = []  # 롤백을 대비해 (원본경로, 백업경로) 쌍을 기록하는 장부
    backup_dir = transaction.backup_dir

    try:
        # 1단계: 수술 전 안전 백업 디렉토리 생성
        backup_dir.mkdir(parents=True, exist_ok=True)

        for idx, patch in enumerate(transaction.patches):
            file_path = patch.file_path

            if DEBUG_MODE:
                print(f"💾 [DEBUG] [FileWriter] [{idx+1}] 패치 수술 대상 검전 완료: {file_path}")

            # 2단계: 기존 파일이 존재하면 백업실로 안전하게 격리 대피 (Rollback 대비)
            if file_path.exists():
                # 백업 파일명 꼬이지 않게 유니크하게 생성 (파일명.bak)
                backup_file_path = backup_dir / f"{file_path.name}_{transaction.correlation_id}.bak"
                shutil.copy2(file_path, backup_file_path)
                applied_files.append((file_path, backup_file_path))
                if DEBUG_MODE:
                    print(f"💾 [DEBUG] [FileWriter] 원본 파일 대피 완료: {file_path.name} -> {backup_file_path.name}")
            else:
                # 신규 파일인 경우 롤백 시 파일 삭제를 하도록 에어백(None) 장착
                applied_files.append((file_path, None))
                if DEBUG_MODE:
                    print(f"💾 [DEBUG] [FileWriter] 신규 생성 대상 파일이므로 백업을 건너뜁니다.")

            # 3단계: 원본 위에 바로 낙서 안 함! 임시 파일(.tmp_xxxx)에 먼저 작성 (Atomic Write)
            tmp_file_path = file_path.with_suffix(f".tmp_{transaction.correlation_id}")
            if DEBUG_MODE:
                print(f"💾 [DEBUG] [FileWriter] 샌드박스 임시 파일 생성 완료: {tmp_file_path.name}")

            # 임시 파일에 새 코드 작성
            tmp_file_path.write_text(patch.updated, encoding="utf-8")

            # 4단계: 디스크 디스크립터 물리 동기화 (OS 버퍼에 갇혀있지 않고 하드에 진짜 박히도록 강제 호출)
            with open(tmp_file_path, "a", encoding="utf-8") as f:
                os.fsync(f.fileno())

            # 5단계: OS 최하단 단일 원자적 명령어로 눈 깜짝할 새 스왑! (os.replace)
            os.replace(tmp_file_path, file_path)
            if DEBUG_MODE:
                print(f"💾 [DEBUG] [FileWriter] OS 레벨 원자적 스왑 스위칭 성공: {file_path.name}")

            # 6단계: 사후 건강검진 (Validation) 기동! 수술 끝난 소스코드 문법이 깨졌는지 체크
            _validate_syntax(file_path)

        print("🎉 [FileWriter] 모든 패치 트랜잭션이 완벽하게 디스크에 하드 코딩되었습니다!")
        return ValidationResult(ok=True, errors=[])

    except Exception as exc:
        if DEBUG_MODE:
            print(f"\n🚨 [DEBUG] [FileWriter] 수술 도중 비상 상황 검지됨! 원인: {exc}")
        _rollback(applied_files)
        return ValidationResult(ok=False, errors=[f"원자적 파일 쓰기 실패로 긴급 복구되었습니다. 원인: {exc}"])
