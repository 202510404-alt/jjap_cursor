"""Jjap-Cursor Codebase Real-time Auto Watcher.

[백그라운드 자동화 감시 사령탑 - 절대 경로 물리 로드 버전]
# INFO: 파이썬의 import 검색 알고리즘을 우회하고, 하드디스크의 해당 파일을 핀포인트 타격 로드합니다.

======================================================================================
🗺️ [PRO_LEVEL] CLINE TOOLS 실시간 파이프라인 작동 순서 가이드 (형님 전용)
======================================================================================
1. 소스코드 변경 감지 🔔
   - 형님이 코드를 수정하고 [Ctrl + S]를 누르면, watchdog(PollingObserver)이 신호를 정밀 포착!
   
2. 필터 검문소 통과 🎯 (process_event)
   - 가상환경(.venv), 결과물(.json, .md) 등을 걸러내고 오직 진짜 소스코드(src/*.py, main.py)만 통과시킵니다.
   
3. 파이프라인 트리거 🔄 (run_pipeline) - 내부 순서 3단계:
   
   [Step 3-1] 메모리 청소 (sys.modules 초기화)
      - 파이썬이 "나 이미 이거 불러왔는데?" 하고 재활용하는 걸 막기 위해 기존 캐시를 강제로 찢어버립니다.
      
   [Step 3-2] 인덱서 강제 가동 (cline_tools/indexer.py)
      - 'AdvancedIndexerV2'를 실시간 로드한 뒤 형님의 진짜 메인 무기인 `scan_project()`를 원격 호출!
      - 결과물 발행: 프로젝트 전체를 전수 조사하여 `.jjap_context.json`과 `.jjap_symbols.json` 장부 갱신.
      
   [Step 3-3] 시각화 맵 최신화 (cline_tools/update_map.py)
      - 앞서 만들어진 최신 JSON 장부들을 바느질하여 사람이 읽기 가장 편한 `CODEBASE_MAP.md`를 발행.
      
4. 동기화 완료 및 대기 ✨
   - AI(Gemini)와 형님이 최신 무기를 바로 사용할 수 있도록 준비를 마치고 다음 [Ctrl + S]를 추적 감시합니다.
======================================================================================
"""

import os
import sys
import time
import importlib.util
from pathlib import Path

# 🚨 윈도우 파일 시스템 버퍼 배송사고 철통 방어용 폴링 옵저버 징집
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

DEBUG_MODE = True

# 🎯 [경로 안전 구역 확보]
CURRENT_DIR = Path(__file__).parent.resolve()
if CURRENT_DIR.name == "cline_tools":
    PROJECT_ROOT = CURRENT_DIR.parent.resolve()
else:
    PROJECT_ROOT = CURRENT_DIR


def import_file_directly(module_name: str, file_path: Path):
    """sys.path고 나발이고 하드디스크에 있는 파일을 무조건 다이렉트로 강제 주입하는 함수"""
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"❌ {file_path} 규격을 파싱할 수 없습니다.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class CodebaseChangeHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_triggered = 0.0
        self.debounce_interval = 0.5

    def log_debug(self, msg: str):
        if DEBUG_MODE:
            print(f"📡 [DEBUG] {msg}")

    def process_event(self, event):
        if event.is_directory:
            return

        src_path = event.src_path
        self.log_debug(f"🔔 OS 신호 수신 성공! -> 이벤트: {event.event_type} | 파일명: {Path(src_path).name}")

        try:
            modified_path = Path(src_path).resolve()
        except Exception as e:
            self.log_debug(f"❌ 경로 resolve 실패 (무시함): {e}")
            return
        
        # 🎯 [필터 통제]
        blacklisted_dirs = [".venv", ".git", "__pycache__", "cline_tools"]
        if any(p in modified_path.parts for p in blacklisted_dirs):
            self.log_debug(f"    ⏩ 탈락 사유: 제외 대상 폴더 포함 ({[p for p in blacklisted_dirs if p in modified_path.parts]})")
            return
            
        if modified_path.suffix in [".json", ".md"]:
            self.log_debug(f"    ⏩ 탈락 사유: 산출물 파일 확장자 제외 ({modified_path.suffix})")
            return

        is_in_src = "src" in modified_path.parts and modified_path.suffix == ".py"
        is_main_py = modified_path.name == "main.py"

        if not (is_in_src or is_main_py):
            self.log_debug(f"    ⏩ 탈락 사유: 감시 영역 밖의 파일 (src 폴더 내부가 아니거나 main.py가 아님)")
            return

        current_time = time.time()
        time_diff = current_time - self.last_triggered
        if time_diff < self.debounce_interval:
            self.log_debug(f"    ⏩ 탈락 사유: 디바운싱 버퍼 컷! ({time_diff:.2f}초 경과)")
            return
            
        self.last_triggered = current_time

        try:
            relative_display = modified_path.relative_to(PROJECT_ROOT)
        except ValueError:
            relative_display = modified_path

        print(f"\n🎯 [필터 최종 통과!!] 감시망 정밀 포착 성공: {relative_display}")
        self.run_pipeline()

    def on_modified(self, event): self.process_event(event)
    def on_created(self, event):  self.process_event(event)
    def on_moved(self, event):
        move_event = type('DummyEvent', (object,), {'is_directory': event.is_directory, 'src_path': event.dest_path, 'event_type': 'moved_target'})()
        self.process_event(move_event)

    def run_pipeline(self):
        print("🔄 [자동 가동] 파이프라인 정렬 및 메모리 캐시 리프레시 시작...")
        try:
            # 🚨 [가짜 모듈 영구 추방] 캐시 삭제
            for mod in ['indexer', 'update_map']:
                if mod in sys.modules:
                    del sys.modules[mod]

            # 🎯 1단계: 하드디스크 물리 경로에서 인덱서 직접 강제 징집 (indexer.py 작동 시작)
            indexer_path = CURRENT_DIR / "indexer.py"
            indexer_module = import_file_directly("indexer", indexer_path)
            print(f"  ➡️ 1/2 단계: AdvancedIndexerV2 강제 로드! (물리 경로 명중: {indexer_path})")
            
            # 클래스 인스턴스화
            indexer_obj = indexer_module.AdvancedIndexerV2(PROJECT_ROOT)
            
            # 🔥 [완벽 핀포인트 개조] 형님의 진짜 메인 함수인 scan_project를 영순위로 장착!
            if hasattr(indexer_obj, 'scan_project'):
                indexer_obj.scan_project()         # 🎯 아귀가 딱 들어맞는 진짜 무기 가동! (.jjap_context.json 등 발행)
            elif hasattr(indexer_obj, 'index_project'):
                indexer_obj.index_project()
            elif hasattr(indexer_obj, 'index_project_structure'):
                indexer_obj.index_project_structure()
            else:
                # 🛠️ 전부 없을 때의 최후의 보루
                methods = [m for m in dir(indexer_obj) if not m.startswith('_')]
                raise AttributeError(f"형님! 인덱서 클래스 내부에 인덱싱 함수가 없습니다! 현재 존재하는 메서드 목록: {methods}")
            
            # 🎯 2단계: 업데이트 맵 강제 징집 (update_map.py 작동 시작)
            update_map_path = CURRENT_DIR / "update_map.py"
            update_map_module = import_file_directly("update_map", update_map_path)
            print("  ➡️ 2/2 단계: CODEBASE_MAP.md 장부 최신화 중...")
            
            update_map_module.update_map()        # 🎯 엮어낸 장부들로 마크다운 지도 최종 드로잉!
            
            print("✅ [동기화 완료] 모든 JSON 장부와 마크다운 맵이 최신 상태로 바느질되었습니다!")
            print("✨ [검색기 연동] 실시간 데이터 로드 및 새로고침 완료!\n")
            
        except Exception as e:
            print(f"❌ [에러 발생] 파이프라인 구동 중 사고 발생: {e}")
            import traceback
            if DEBUG_MODE:
                traceback.print_exc()


def main():
    print("=" * 70)
    print("🚀 [Jjap-Cursor Watcher] 실시간 백그라운드 감시망 기동!")
    print(f"📂 감시 대상 진짜 루트 절대 경로: {PROJECT_ROOT}")
    print(f"⚙️  초정밀 디버깅 모드 상태: {'🔴 ON (도배 중)' if DEBUG_MODE else '⚪ OFF'}")
    
    print("\n💡 소스코드를 수정하고 저장(Ctrl+S)하면 진행 상황이 실시간 출력됩니다.")
    print("🛑 중단하려면 터미널에서 Ctrl + C 를 누르십시오.")
    print("=" * 70)

    event_handler = CodebaseChangeHandler()
    observer = Observer()
    
    observer.schedule(event_handler, path=str(PROJECT_ROOT), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n🛑 [감시 중단] 안전하게 백그라운드 감시 전원을 종료합니다.")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()