import json
import sys
import argparse
from pathlib import Path

SYMBOLS_FILE = Path(".jjap_symbols.json")
CONTEXT_FILE = Path(".jjap_context.json")

def load_json(file_path: Path):
    if not file_path.exists():
        print(f"❌ Error: {file_path} not found. Please run the indexer first.")
        sys.exit(1)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def lookup_symbol(symbol_name: str):
    """특정 함수나 클래스의 시그니처와 사용처를 검색합니다."""
    data = load_json(SYMBOLS_FILE)
    symbols = data.get("symbols", [])
    
    # 부분 일치 검색 (대소문자 무시)
    results = [s for s in symbols if symbol_name.lower() in s.get("name", "").lower()]
    
    if not results:
        print(f"⚠️ 심볼 '{symbol_name}'을(를) 찾을 수 없습니다.")
        return

    print(f"🔍 '{symbol_name}' 검색 결과 ({len(results)}건 찾음):\n")
    for s in results:
        print(f"[{s.get('type', 'symbol').upper()}] {s.get('full_name', s.get('name'))}")
        print(f"  - File: {s.get('file')} (Lines: {s.get('start_line')}-{s.get('end_line')})")
        print(f"  - Signature: {s.get('name')}{s.get('signature', '()')}")
        
        used_by = s.get("used_by", [])
        if used_by:
            print(f"  - Used By: {len(used_by)} places")
            for u in used_by[:5]: # 최대 5개까지만 출력 (토큰 절약)
                print(f"    * {u}")
            if len(used_by) > 5:
                print(f"    * ... and {len(used_by) - 5} more")
        else:
            print("  - Used By: None (Not used anywhere or it's a top-level entry)")
        print("-" * 40)

def show_skeleton(file_path: str):
    """특정 파일의 뼈대(Skeleton)를 보여줍니다."""
    data = load_json(CONTEXT_FILE)
    files = data.get("files", {})
    
    # 경로 매칭 (부분 일치)
    matched_keys = [k for k in files.keys() if file_path in k]
    
    if not matched_keys:
        print(f"⚠️ 파일 경로에 '{file_path}'이(가) 포함된 파일을 찾을 수 없습니다.")
        return
        
    for key in matched_keys:
        skeleton = files[key].get("skeleton", "No skeleton available.")
        print(f"📄 [FILE SKELETON] {key}")
        print(skeleton)
        print("=" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="jjap_cursor Lookup Tool for AI Agents")
    subparsers = parser.add_subparsers(dest="command", help="명령어 선택")
    
    # symbol 검색 명령어
    parser_sym = subparsers.add_parser("symbol", help="함수나 클래스 이름으로 검색")
    parser_sym.add_argument("name", type=str, help="검색할 심볼 이름 (예: atomic_write_text)")
    
    # skeleton 검색 명령어
    parser_skel = subparsers.add_parser("skeleton", help="파일 경로로 뼈대 검색")
    parser_skel.add_argument("path", type=str, help="검색할 파일 경로 (예: io_utils.py)")
    
    args = parser.parse_args()
    
    if args.command == "symbol":
        lookup_symbol(args.name)
    elif args.command == "skeleton":
        show_skeleton(args.path)
    else:
        parser.print_help()