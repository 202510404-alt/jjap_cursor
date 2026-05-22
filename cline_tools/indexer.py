import ast
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List

class AdvancedIndexerV2:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.symbols: List[Dict[str, Any]] = []
        self.files_context: Dict[str, Any] = {}
        self.definition_map: Dict[str, str] = {}

    def _get_sha256(self, content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _extract_skeleton(self, content: str) -> str:
        """파이썬 소스코드에서 실제 구현부는 숨기고 클래스/함수 선언부 뼈대만 추출"""
        try:
            tree = ast.parse(content)
            skeleton_lines = []
            
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    skeleton_lines.append(f"class {node.name}:")
                    for sub_node in node.body:
                        if isinstance(sub_node, ast.FunctionDef):
                            # 아규먼트 구조 파싱 생략 후 심플 시그니처 렌더링
                            skeleton_lines.append(f"    def {sub_node.name}(...):")
                            skeleton_lines.append(f"        ...")
                elif isinstance(node, ast.FunctionDef):
                    skeleton_lines.append(f"def {node.name}(...):")
                    skeleton_lines.append(f"    ...")
            return "\n".join(skeleton_lines)
        except:
            return "..."

    def index_file(self, file_path: Path):
        """단일 파이썬 파일의 심볼, 스켈레톤, 해시, 호출 관계 정밀 분석"""
        try:
            content = file_path.read_text(encoding="utf-8")
            rel_path = file_path.relative_to(self.project_root).as_posix()
            
            tree = ast.parse(content)
            file_lines = content.splitlines()
            mtime = int(file_path.stat().st_mtime)
            
            current_class = None
            
            # 1. 파일별 스켈레톤 및 해시 생성 (.jjap_context.json용)
            self.files_context[rel_path] = {
                "hash": self._get_sha256(content),
                "mtime": mtime,
                "skeleton": self._extract_skeleton(content)
            }

            # 2. AST 노드 순회하며 심볼 정밀 추출 (.jjap_symbols.json용)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    current_class = node.name
                    symbol_id = f"{rel_path}::{node.name}"
                    
                    self.definition_map[node.name] = f"{rel_path}:{node.lineno}"
                    
                    self.symbols.append({
                        "symbol_id": symbol_id,
                        "full_name": node.name,
                        "name": node.name,
                        "type": "class",
                        "parent": None,
                        "file": rel_path,
                        "start_line": node.lineno,
                        "end_line": getattr(node, "end_lineno", node.lineno),
                        "range": [node.lineno, getattr(node, "end_lineno", node.lineno)],
                        "decorators": [ast.dump(d) for d in node.decorator_list],
                        "signature": f"class {node.name}",
                        "calls": [],
                        "used_by": []
                    })
                    
                elif isinstance(node, ast.FunctionDef):
                    parent_name = None
                    # 간단한 부모 클래스 추정 기법 (완벽 정적분석 한계 보완용)
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef) and node in parent.body:
                            parent_name = parent.name
                            break
                            
                    full_name = f"{parent_name}.{node.name}" if parent_name else node.name
                    symbol_id = f"{rel_path}::{full_name}"
                    
                    # definition_map 등록
                    self.definition_map[full_name] = f"{rel_path}:{node.lineno}"
                    if not parent_name:
                        self.definition_map[node.name] = f"{rel_path}:{node.lineno}"

                    # 내부 호출(calls) 추적
                    calls = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                calls.append(child.func.id)
                            elif isinstance(child.func, ast.Attribute):
                                calls.append(child.func.attr)
                    calls = sorted(list(set(calls)))

                    start = node.lineno
                    end = getattr(node, "end_lineno", node.lineno)

                    self.symbols.append({
                        "symbol_id": symbol_id,
                        "full_name": full_name,
                        "name": node.name,
                        "type": "method" if parent_name else "function",
                        "parent": parent_name,
                        "file": rel_path,
                        "start_line": start,
                        "end_line": end,
                        "range": [start, end],
                        "decorators": [],
                        "signature": f"def {node.name}(...)",
                        "calls": calls,
                        "used_by": []
                    })
        except Exception as e:
            print(f"⚠️ [INDEX ERROR] {file_path.name} 스캔 실패: {e}")

    def scan_project(self):
        """전체 프로젝트 폴더를 순회하며 파이썬 파일 인덱싱 (start.py 검열 완료)"""
        for root, dirs, files in os.walk(self.project_root):
            # 1. 특정 제외 폴더가 경로에 포함되어 있으면 통째로 무시
            if any(p in root for p in [".venv", ".git", "__pycache__", "cline_tools"]):
                continue
                
            for file in files:
                # 🚨 형님의 특명: 단순 실행용 스위치인 start.py는 인덱싱 장부에서 철저히 제외!
                if file == "start.py":
                    continue
                    
                if file.endswith(".py"):
                    self.index_file(Path(root) / file)
        # 의존성 관계 역추적 (used_by 채우기 무의식적 기법)
        for s in self.symbols:
            name_to_check = s["name"]
            for target in self.symbols:
                if name_to_check in target["calls"] and s["symbol_id"] != target["symbol_id"]:
                    s["used_by"].append(target["symbol_id"])
            s["used_by"] = sorted(list(set(s["used_by"])))

        # 3대 신형 데이터 파일로 동시 디스크 쓰기(Write)
        with open(".jjap_context.json", "w", encoding="utf-8") as f:
            json.dump({"files": self.files_context}, f, indent=2, ensure_ascii=False)
            
        with open(".jjap_symbols.json", "w", encoding="utf-8") as f:
            json.dump({"symbols": self.symbols}, f, indent=2, ensure_ascii=False)
            
        with open("definition_map.json", "w", encoding="utf-8") as f:
            json.dump(self.definition_map, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    indexer = AdvancedIndexerV2(Path(".").resolve())
    indexer.scan_project()
    print("🚀 [SUCCESS] 신형 인덱서 V2가 .jjap_context / .jjap_symbols / definition_map을 무결하게 새로 구워냈습니다!")