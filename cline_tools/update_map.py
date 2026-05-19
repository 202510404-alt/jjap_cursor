import json
from pathlib import Path

def update_map():
    context_file = Path(".jjap_context.json")
    symbols_file = Path(".jjap_symbols.json")
    output_file = Path("CODEBASE_MAP.md")
    
    if not context_file.exists() or not symbols_file.exists():
        print("❌ Error: 인덱서 데이터 파일(.jjap_context 또는 .jjap_symbols)이 없습니다.")
        print("💡 해결책: 인덱서(indexer.py)를 먼저 실행한 뒤 이 스크립트를 돌리세요.")
        return

    # 1. 최신 데이터 로드
    with open(context_file, "r", encoding="utf-8") as f:
        context_data = json.load(f).get("files", {})
        
    with open(symbols_file, "r", encoding="utf-8") as f:
        symbols_list = json.load(f).get("symbols", [])

    # 2. 에이전트 분석을 돕기 위해 파일별 심볼 및 관계 매핑 구조 생성
    symbols_by_file = {}
    for s in symbols_list:
        file_path = s.get("file")
        if file_path not in symbols_by_file:
            symbols_by_file[file_path] = []
        symbols_by_file[file_path].append(s)

    # 3. CODEBASE_MAP.md 최종 렌더링
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🏗️ 짭커서 프로젝트 CODEBASE MAP\n\n")
        f.write(f"현재 인덱싱된 총 파일 수: **{len(context_data)}개**\n\n")
        
        # 📂 모듈 인덱스 구역
        f.write("## 🗂️ [Module Index]\n")
        for path in sorted(context_data.keys()):
            f.write(f"- `{path}`\n")
        
        # 💀 뼈대 및 의존성 관계 상세 구역
        f.write("\n## 💀 [Skeleton & Dependency 명세서]\n")
        for path, info in sorted(context_data.items()):
            f.write(f"### 📄 {path}\n")
            
            # 해당 파일에 속한 상세 심볼(클래스/함수)의 호출 관계 먼저 요약
            file_symbols = symbols_by_file.get(path, [])
            if file_symbols:
                f.write("#### 🔍 내부 심볼 및 의존성 관계:\n")
                for s in file_symbols:
                    f.write(f"- **[{s['type'].upper()}]** `{s['full_name']}` (Line: {s['start_line']}~{s['end_line']})\n")
                    if s.get("calls"):
                        f.write(f"  - 🔗 *Calls (호출하는 것)*: `{', '.join(s['calls'])}`\n")
                    if s.get("used_by"):
                        f.write(f"  - 🎯 *Used By (나를 부르는 곳)*: `{', '.join(s['used_by'])}`\n")
                f.write("\n")

            # 실제 코드 뼈대(Skeleton) 출력
            skeleton_text = info.get("skeleton", "").strip()
            if skeleton_text:
                f.write("#### 🧱 Code Skeleton:\n")
                f.write("```python\n")
                f.write(f"{skeleton_text}\n")
                f.write("```\n\n")
            else:
                f.write("*선언된 클래스나 함수가 없는 파일이거나 모듈입니다.*\n\n")
                
            f.write("-" * 50 + "\n\n")

    print(f"✅ [SUCCESS] V2 인덱스 정밀 데이터를 결합하여 {output_file.name} 업데이트 완료!")

if __name__ == "__main__":
    update_map()