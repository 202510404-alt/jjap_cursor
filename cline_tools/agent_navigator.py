import json
import sys
import re
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# =====================================================================
# 🧠 CORE INTELLIGENCE: MULTI-TARGET CODE SLICE LOADER
# =====================================================================
class SemanticNavigator:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.symbols_path = root_dir / ".jjap_symbols.json"
        self.symbols_data = self._load_database()

    def _load_database(self):
        if not self.symbols_path.exists():
            return {"symbols": []}
        try:
            with open(self.symbols_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"symbols": []}

    def extract_multi_slices(self, raw_prompt: str):
        """
        [Multi-Target Protocol Parser]
        형님이 입력한 프롬프트에서 '파일경로:시작줄-끝줄' 또는 '파일경로:줄번호' 규격을 
        정규식으로 전부 추출하여, 요청된 순서대로 코드를 줄줄이 엮어서 반환합니다.
        """
        # 정규식 패턴: 파일 주소(확장자 포함) : 시작줄 - 끝줄 (또는 단일 줄)
        pattern = r"([a-zA-Z0-9_\-\./]+)\s*:\s*(\d+)(?:\s*-\s*(\d+))?"
        
        matches = re.findall(pattern, raw_prompt)
        results = []
        
        if not matches:
            return results

        for idx, match in enumerate(matches, start=1):
            file_rel_path = match[0].strip()
            start_line = int(match[1])
            end_line = int(match[2]) if match[2] else start_line # 끝줄 없으면 단일줄 처리
            
            full_file_path = self.root_dir / file_rel_path
            sliced_code = ""
            
            if full_file_path.exists():
                try:
                    with open(full_file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    # 파이썬 인덱스 보정 및 범위 제한 안전장치
                    max_lines = len(lines)
                    s_idx = max(0, start_line - 1)
                    e_idx = min(max_lines, end_line)
                    
                    target_lines = lines[s_idx:e_idx]
                    
                    for l_num, line in enumerate(target_lines, start=start_line):
                        sliced_code += f"{l_num:4d} | {line}"
                    
                    if not target_lines:
                        sliced_code = f"⚠️ 지정한 라인 범위가 파일의 총 라인수({max_lines})를 벗어났습니다."
                except Exception as e:
                    sliced_code = f"⚠️ 소스코드 로드 실패: {e}"
            else:
                sliced_code = f"⚠️ 실제 디스크에 파일이 존재하지 않습니다: {file_rel_path}"

            results.append({
                "req_num": idx,
                "file": file_rel_path,
                "line_range": f"{start_line} ~ {end_line}",
                "code": sliced_code
            })
            
        return results


# =====================================================================
# 🎨 UI ARCHITECTURE LAYER (MULTI-LINE TEXT INPUT ENGINE)
# =====================================================================
class JjapCursorNavigatorUI:
    def __init__(self, root, navigator: SemanticNavigator):
        self.root = root
        self.navigator = navigator
        self.root.title("🏗️ Jjap-Cursor 핀포인트 멀티 컨텍스트 수집기")
        self.root.geometry("1100x800")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self._build_ui_layout()

    def _build_ui_layout(self):
        # 상단: 멀티라인 프롬프트 입력창 영역
        top_frame = ttk.LabelFrame(self.root, text="🤖 에이전트 컨텍스트 요청 프로토콜 입력 (줄바꿈으로 연속 요청 가능)", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.prompt_text = tk.Text(top_frame, height=5, font=("Consolas", 10), bg="#2d2d2d", fg="#ffffff", insertbackground="white")
        self.prompt_text.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5)
        
        # 예시 기본 텍스트 삽입
        default_protocol = (
            "src/jjap_cursor/core/services/project_manager.py:81-120\n"
            "src/jjap_cursor/core/utils/io_utils.py:9-25"
        )
        self.prompt_text.insert("1.0", default_protocol)
        
        self.search_btn = ttk.Button(top_frame, text="연속 코드\n추출 가동", command=self.trigger_multi_extraction)
        self.search_btn.pack(side=tk.RIGHT, padx=5, fill=tk.Y)

        # 하단 전체: 추출된 소스코드가 줄줄이 이어지는 메인 보드
        main_frame = ttk.LabelFrame(self.root, text="📝 [Code Slice Loader] 추출 결과 (연속된 컨텍스트 스트림)", padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.code_display = tk.Text(main_frame, font=("Consolas", 10), wrap=tk.NONE, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        
        x_scroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.code_display.xview)
        y_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.code_display.yview)
        self.code_display.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        
        self.code_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 최하단 상태창
        self.status_label = ttk.Label(self.root, text=" 준비 완료 - 프로토콜 규격 요청 대기 중...", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def trigger_multi_extraction(self):
        """입력된 모든 규격 라인을 파싱하여 결과를 우측 뷰어에 줄줄이 결합 출력합니다."""
        raw_prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not raw_prompt:
            messagebox.showwarning("입력 누락", "요청할 파일 주소와 줄 범위를 입력해 주세요.")
            return
        
        self.code_display.delete("1.0", tk.END)
        
        # 멀티 슬라이스 엔진 구동
        extracted_slices = self.navigator.extract_multi_slices(raw_prompt)
        
        # ⭐ 형님이 오더 내리신 프로토콜 규격 불일치 방어벽 구역!
        if not extracted_slices:
            # 1. 보기 서러운 텍스트 에러 대신 눈에 확 띄는 팝업창을 띄워 올바른 가이드를 제시합니다.
            guide_message = (
                "❌ 올바른 프로토콜 규격이 아닙니다!\n\n"
                "추출을 위해 아래 예시처럼 '파일주소:시작줄-끝줄' 형태로 정확히 입력해 주세요.\n\n"
                "💡 [입력 규격 예시]\n"
                "• 범위 지정형 -> src/jjap_cursor/core/services/project_manager.py:40-80\n"
                "• 단일선 지정형 -> src/jjap_cursor/core/utils/io_utils.py:15\n\n"
                "※ 엔터(줄바꿈)를 치면 위 규격대로 여러 파일을 동시에 연속 추출할 수 있습니다."
            )
            messagebox.showerror("프로토콜 규격 오류", guide_message)
            
            # 2. 결과 디스플레이 창에도 명확하게 에러 상태 가이드를 잔상으로 남겨둡니다.
            self.code_display.insert(tk.END, "❌ 추출 실패: 프로토콜 매칭 기포가 발견되지 않았습니다.\n상단 팝업창의 주소 입력 예시를 확인하신 뒤 다시 기동해 주십시오.")
            self.status_label.config(text=" ❌ 프로토콜 규격 불일치 - 가이드 팝업 호출됨.")
            return

        # 결과 조각들을 스트림 형식으로 이어서 출력
        for slc in extracted_slices:
            stream_header = (
                f"# ==========================================================\n"
                f"# [요청 {slc['req_num']}] TARGET: {slc['file']} ({slc['line_range']}라인)\n"
                f"# ==========================================================\n"
            )
            self.code_display.insert(tk.END, stream_header)
            self.code_display.insert(tk.END, slc["code"])
            self.code_display.insert(tk.END, "\n\n") # 조각 간의 간격 구분
            
        self.status_label.config(text=f" ✅ 성공: 총 {len(extracted_slices)}개의 코드 컨텍스트 스트림을 한 번에 결합 완료했습니다.")


if __name__ == "__main__":
    # 스크립트 실행 위치 기준 루트 처리
    script_path = Path(__file__).parent.resolve()
    project_root = script_path.parent if script_path.name == "cline_tools" else script_path
    
    # 엔진 및 UI 구동
    navigator_engine = SemanticNavigator(project_root)
    root_window = tk.Tk()
    app = JjapCursorNavigatorUI(root_window, navigator_engine)
    root_window.mainloop()