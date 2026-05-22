"""Jjap-Cursor Total Control Launchpad.

[짭커서 통합 기동 사령탑]
이 스크립트는 형님이 파일 하나만 눌러도 백그라운드 자동 감시망(Watcher)을 은밀하게 가동하고,
동시에 에이전트 네비게이터(agent_navigator.py) GUI 창을 전면에 띄워주는 원터치 마스터 버튼입니다.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 🎯 1. 경로 정의 (절대 경로 보장)
ROOT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
WATCHER_SCRIPT = ROOT_DIR / "cline_tools" / "jjap_watcher.py"
NAVIGATOR_SCRIPT = ROOT_DIR / "cline_tools" / "agent_navigator.py"


def main():
    print("======================================================================")
    print("🔥 [Jjap-Cursor Launchpad] 짭커서 통합 마스터 사령탑 기동 시작!")
    print(f"📂 프로젝트 루트: {ROOT_DIR}")
    print("======================================================================")

    # 🚨 가상환경 파이썬 검문
    if not VENV_PYTHON.exists():
        print(f"❌ 에러: 가상환경 파이썬을 찾을 수 없습니다! ({VENV_PYTHON})")
        print("💡 해결책: 가상환경(.venv)이 생성되어 있는지 확인해 주세요.")
        input("\n종료하려면 엔터를 누르십시오...")
        return

    # 📡 1단계: 실시간 백그라운드 워처(jjap_watcher.py) 은밀하게 기동
    print("➡️ 1단계: 실시간 백그라운드 자동 감시망(Watcher) 투입 중...")
    
    # 💡 stdout/stderr를 PIPE로 격리하지 않고 완전히 독립된 프로세스로 분리합니다.
    # 윈도우 환경에서 터미널 창을 공유하면서도 GUI를 방해하지 않게 설계했습니다.
    watcher_process = subprocess.Popen(
        [str(VENV_PYTHON), str(WATCHER_SCRIPT)],
        cwd=str(ROOT_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # 시그널 분리용 안전핀
    )
    
    # 워처가 안전하게 자리를 잡을 수 있도록 0.5초 대기 시동 걸어주기
    time.sleep(0.5)
    print("✅ [SUCCESS] 감시망이 백그라운드 메모리에 안착했습니다.")

    # 🧠 2단계: 에이전트 네비게이터(agent_navigator.py) GUI 창 띄우기
    print("➡️ 2단계: 세맨틱 네비게이터 검색기(GUI) 전면 배치 중...")
    print("💡 [안내] 검색기 창을 닫으면 백그라운드 감시망도 함께 안전하게 종료됩니다.")
    print("----------------------------------------------------------------------")
    
    try:
        # GUI 프로세스는 메인 스레드에서 직접 실행하여 창이 켜져 있는 동안 터미널을 유지합니다.
        subprocess.run(
            [str(VENV_PYTHON), str(NAVIGATOR_SCRIPT)],
            cwd=str(ROOT_DIR),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 [사용자 중단] 터미널에서 종료 신호를 수신했습니다.")
    except Exception as e:
        print(f"\n❌ [런타임 사고] 검색기 실행 중 오류 발생: {e}")
    finally:
        # 🧼 3단계: 청소 작전 (GUI 창이 닫히면 백그라운드 워처도 같이 사살)
        print("----------------------------------------------------------------------")
        print("🧼 3단계: 검색기 종료 감지 -> 백그라운드 감시망 자원 회수(종료) 중...")
        try:
            watcher_process.terminate()
            watcher_process.wait(timeout=3)
            print("✅ [CLEANUP] 백그라운드 프로세스가 안전하게 전원 종료되었습니다.")
        except Exception:
            # 이미 꺼졌거나 버티는 경우 강제 진압
            watcher_process.kill()
            print("⚡ [FORCE KILL] 프로세스를 강제 종료 처리했습니다.")
            
    print("======================================================================")
    print("🏁 [Jjap-Cursor] 마스터 사령탑 철수 완료. 깔끔하게 정리되었습니다!")
    print("======================================================================")


if __name__ == "__main__":
    main()