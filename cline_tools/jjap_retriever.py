import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

class JjapRetriever:
    """
    Roo Code를 위한 Context Surgeon V2.
    1. Exact Match 우선 탐색 (Disambiguation 해결)
    2. 라인 단위 Truncation (코드 파손 방지)
    3. 엄격한 스키마 계약 (Indexer V2 전제)
    """
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.symbols_file = self.project_root / ".jjap_symbols.json"
        self.max_context_lines = 300
        self.symbols_db = self._load_symbols()

    def _load_symbols(self) -> List[Dict[str, Any]]:
        if self.symbols_file.exists():
            try:
                with open(self.symbols_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("symbols", [])
            except Exception as e:
                print(f"⚠️ 스키마 로드 실패: {e}")
        return []

    def retrieve_symbol(self, query: str) -> str:
        """심볼 검색 및 정밀 문맥 조립"""
        # [지피티 지적 1 해결] 심볼 식별 최적화 (Exact -> Partial -> Fallback)
        target = self._find_best_match(query)
        
        if not target:
            return f"❌ '{query}'와 일치하는 심볼을 찾을 수 없습니다. (ID 또는 Name을 확인하세요)"

        file_rel_path = target.get('file')
        file_path = self.project_root / file_rel_path
        if not file_path.exists():
            return f"❌ 파일을 찾을 수 없습니다: {file_rel_path}"

        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # [Surgery 시작]
        context = []
        context.append(f"### [RETRIEVED CONTEXT: {target['symbol_id']}] ###")
        
        # 1. Imports (상단 50줄)
        context.append("\n# --- Imports ---")
        context.extend([line.strip() for line in all_lines[:50] if line.strip().startswith(('import ', 'from '))])
        context.append("    ...")

        # 2. Parent Context (Class Header)
        if target.get('parent'):
            parent = next((s for s in self.symbols_db if s['name'] == target['parent'] and s['file'] == target['file']), None)
            if parent:
                p_start = parent['range'][0]
                context.append(f"\n# --- Class: {target['parent']} ---")
                context.append(all_lines[p_start-1].rstrip())
                context.append("    \"\"\" (Internal methods hidden) \"\"\"")

        # 3. Target Snippet (Range 준수)
        start, end = target['range']
        context.append(f"\n# --- Target: {target['name']} (Lines {start}-{end}) ---")
        # 인덱스 범위 안전하게 가져오기
        snippet = all_lines[max(0, start-1) : min(len(all_lines), end)]
        context.extend([line.rstrip() for line in snippet])

        # [지피티 지적 2 해결] 라인 단위 안전 절삭
        return self._safe_truncate("\n".join(context))

    def _find_best_match(self, query: str) -> Optional[Dict]:
        """심볼 중복 문제를 해결하기 위한 매칭 로직"""
        # 1. symbol_id 완전 일치 (가장 정확)
        for s in self.symbols_db:
            if s.get('symbol_id') == query: return s
        # 2. name 완전 일치
        for s in self.symbols_db:
            if s.get('name') == query: return s
        # 3. 부분 일치 (Fallback)
        for s in self.symbols_db:
            if query.lower() in s.get('name', '').lower(): return s
        return None

    def _safe_truncate(self, text: str) -> str:
        """문자열 단위가 아닌 라인 단위로 끊어서 코드 파손 방지"""
        lines = text.splitlines()
        if len(lines) <= self.max_context_lines:
            return text
        
        truncated = lines[:self.max_context_lines]
        truncated.append("\n... [⚠️ WARNING: Context truncated by line limit to protect token budget] ...")
        return "\n".join(truncated)

def main():
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query:
        print("💡 Usage: python cline_tools/jjap_retriever.py <symbol_id_or_name>")
        return
    
    retriever = JjapRetriever(Path.cwd())
    print(retriever.retrieve_symbol(query))

if __name__ == "__main__":
    main()