"""Project scanner service for skeleton and symbol table generation."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from ..utils.io_utils import atomic_write_text


@dataclass(slots=True)
class ScanArtifacts:
    """Container for scan outputs produced from Python source files."""

    skeletons: dict[str, str]
    symbol_table: dict[str, list[dict[str, Any]]]


class FileScanner:
    """Scans project files and builds AST-based skeleton and symbol metadata."""

    def __init__(self, project_root: Path) -> None:
        """Initialize scanner with project root and ignore patterns."""
        self.project_root = project_root
        self._ignore_patterns = self._load_gitignore_patterns()

    def scan_project(self) -> ScanArtifacts:
        """Scan all eligible Python files and return generated artifacts."""
        skeletons: dict[str, str] = {}
        symbols: list[dict[str, Any]] = []

        for file_path in self._iter_python_files():
            source = file_path.read_text(encoding="utf-8")
            module = ast.parse(source)
            rel_path = file_path.relative_to(self.project_root).as_posix()

            skeletons[rel_path] = self._extract_skeleton(module)
            symbols.extend(self._extract_symbols(module, rel_path))

        self._populate_used_by(symbols)
        return ScanArtifacts(skeletons=skeletons, symbol_table={"symbols": symbols})

    def write_outputs(self, artifacts: ScanArtifacts) -> None:
        """Write scanner outputs to v8.0 context files in project root."""
        symbols_path = self.project_root / ".jjap_symbols.json"
        context_path = self.project_root / ".jjap_context.json"

        symbol_payload = json.dumps(artifacts.symbol_table, ensure_ascii=False, indent=2)
        atomic_write_text(symbols_path, symbol_payload)

        file_metadata: dict[str, dict[str, Any]] = {}
        for rel_path, skeleton in artifacts.skeletons.items():
            abs_path = self.project_root / rel_path
            file_metadata[rel_path] = {
                "hash": self._sha256_of_file(abs_path),
                "mtime": int(abs_path.stat().st_mtime),
                "skeleton": skeleton,
            }

        context_payload = {
            "files": file_metadata,
            "global_symbols": [s["symbol_id"] for s in artifacts.symbol_table["symbols"]],
        }
        context_json = json.dumps(context_payload, ensure_ascii=False, indent=2)
        atomic_write_text(context_path, context_json)

    def _iter_python_files(self) -> list[Path]:
        """Return Python files excluded by .gitignore-aware filtering."""
        files: list[Path] = []
        for root, dirs, filenames in os.walk(self.project_root):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.project_root).as_posix() if root_path != self.project_root else ""

            # Hard-stop directories that must always be ignored.
            dirs[:] = [d for d in dirs if d not in {".git", "venv", "__pycache__"}]
            dirs[:] = [d for d in dirs if not self._matches_directory_ignore(rel_root, d)]

            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                file_path = root_path / filename
                if not self._is_ignored(file_path):
                    files.append(file_path)
        return sorted(files)

    def _is_ignored(self, path: Path) -> bool:
        """Check if a path is ignored by baseline or .gitignore patterns."""
        rel = path.relative_to(self.project_root).as_posix()
        parts = set(path.parts)

        if ".git" in parts or "__pycache__" in parts:
            return True
        if rel.startswith("venv/") or rel.startswith(".venv/") or rel.startswith("node_modules/"):
            return True

        for pattern in self._ignore_patterns:
            if pattern.endswith("/"):
                dir_pattern = pattern.rstrip("/")
                if rel.startswith(f"{dir_pattern}/"):
                    return True
            elif "/" in pattern and fnmatch(rel, pattern):
                return True
            elif fnmatch(path.name, pattern):
                return True
        return False

    def _load_gitignore_patterns(self) -> list[str]:
        """Parse basic .gitignore rules from project root."""
        gitignore_path = self.project_root / ".gitignore"
        if not gitignore_path.exists():
            return []

        patterns: list[str] = []
        for raw in gitignore_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            normalized = line.lstrip("/")
            if normalized:
                patterns.append(normalized)
        return patterns

    def _matches_directory_ignore(self, rel_root: str, dirname: str) -> bool:
        """Check if a child directory matches configured ignore patterns."""
        if not self._ignore_patterns:
            return False
        rel_dir = f"{rel_root}/{dirname}" if rel_root else dirname
        for pattern in self._ignore_patterns:
            candidate = pattern.rstrip("/")
            if fnmatch(rel_dir, candidate) or fnmatch(dirname, candidate):
                return True
        return False

    def _extract_skeleton(self, module: ast.Module) -> str:
        """Create a minimal AST skeleton with signatures and docstrings."""
        lines: list[str] = []
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines.extend(self._render_function_skeleton(node, indent=0))
            elif isinstance(node, ast.ClassDef):
                lines.extend(self._render_class_skeleton(node))
        return "\n".join(lines).strip()

    def _render_class_skeleton(self, node: ast.ClassDef) -> list[str]:
        """Render class skeleton with method signatures and class docstring."""
        out = [f"class {node.name}:"]
        class_doc = ast.get_docstring(node)
        if class_doc:
            out.append(f'    """{class_doc}"""')
        method_count = 0
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.extend(self._render_function_skeleton(child, indent=1))
                method_count += 1
        if method_count == 0 and not class_doc:
            out.append("    ...")
        return out

    def _render_function_skeleton(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        indent: int,
    ) -> list[str]:
        """Render one function skeleton preserving signature and docstring."""
        pad = "    " * indent
        async_kw = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        signature = self._build_signature(node)
        out = [f"{pad}{async_kw}def {node.name}{signature}:"]

        doc = ast.get_docstring(node)
        if doc:
            out.append(f'{pad}    """{doc}"""')
        out.append(f"{pad}    ...")
        return out

    def _build_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Build human-readable function signature from AST arguments."""
        args = node.args
        parts: list[str] = []

        posonly = list(args.posonlyargs)
        normal = list(args.args)
        defaults = list(args.defaults)
        default_offset = len(posonly) + len(normal) - len(defaults)

        all_pos = posonly + normal
        for idx, arg in enumerate(all_pos):
            text = self._render_arg(arg)
            default_idx = idx - default_offset
            if default_idx >= 0:
                text += f" = {ast.unparse(defaults[default_idx])}"
            parts.append(text)

        if posonly:
            parts.insert(len(posonly), "/")

        if args.vararg:
            parts.append(f"*{self._render_arg(args.vararg)}")
        elif args.kwonlyargs:
            parts.append("*")

        for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
            text = self._render_arg(kwarg)
            if default is not None:
                text += f" = {ast.unparse(default)}"
            parts.append(text)

        if args.kwarg:
            parts.append(f"**{self._render_arg(args.kwarg)}")

        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        return f"({', '.join(parts)}){returns}"

    def _render_arg(self, arg: ast.arg) -> str:
        """Render argument with annotation when it exists."""
        if arg.annotation is None:
            return arg.arg
        return f"{arg.arg}: {ast.unparse(arg.annotation)}"

    def _extract_symbols(self, module: ast.Module, rel_path: str) -> list[dict[str, Any]]:
        """Extract symbol metadata including decorators, range, and call edges."""
        symbols: list[dict[str, Any]] = []

        for node in module.body:
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(self._symbol_entry(child, rel_path, parent=node.name, symbol_type="method"))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(self._symbol_entry(node, rel_path, parent=None, symbol_type="function"))

        return symbols

    def _symbol_entry(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        rel_path: str,
        parent: str | None,
        symbol_type: str,
    ) -> dict[str, Any]:
        """Build one symbol table entry compatible with v8.0 blueprint shape."""
        full_name = f"{parent}.{node.name}" if parent else node.name
        symbol_id = f"{rel_path}::{full_name}"
        return {
            "symbol_id": symbol_id,
            "full_name": full_name,
            "name": node.name,
            "type": symbol_type,
            "parent": parent,
            "file": rel_path,
            "start_line": getattr(node, "lineno", 0),
            "end_line": getattr(node, "end_lineno", getattr(node, "lineno", 0)),
            "range": [getattr(node, "lineno", 0), getattr(node, "end_lineno", getattr(node, "lineno", 0))],
            "decorators": [f"@{ast.unparse(dec)}" for dec in node.decorator_list],
            "signature": self._build_signature(node),
            "calls": sorted(self._extract_calls(node)),
            "used_by": [],
        }

    def _extract_calls(self, node: ast.AST) -> set[str]:
        """Extract simple function call targets from a node subtree."""
        calls: set[str] = set()
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if isinstance(child.func, ast.Name):
                calls.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                root = ast.unparse(child.func.value)
                calls.add(f"{root}.{child.func.attr}")
        return calls

    def _populate_used_by(self, symbols: list[dict[str, Any]]) -> None:
        """Populate reverse call references with namespace-safe heuristic matching."""
        by_short_name: dict[str, list[dict[str, Any]]] = {}
        by_full_name: dict[str, dict[str, Any]] = {}
        by_symbol_id: dict[str, dict[str, Any]] = {}

        for entry in symbols:
            by_short_name.setdefault(entry["name"], []).append(entry)
            by_full_name[entry["full_name"]] = entry
            by_symbol_id[entry["symbol_id"]] = entry

        for entry in symbols:
            caller = entry["symbol_id"]
            caller_parent = entry.get("parent")
            for call in entry["calls"]:
                call_tail = call.split(".")[-1]

                # 1) Match by full_name tail (e.g., AuthService.login or module.AuthService.login).
                target = next(
                    (
                        value
                        for full_name, value in by_full_name.items()
                        if full_name == call or full_name.endswith(f".{call}")
                    ),
                    None,
                )

                # 2) If caller is method, prefer sibling methods in the same class namespace.
                if target is None and caller_parent:
                    sibling_full_name = f"{caller_parent}.{call_tail}"
                    target = by_full_name.get(sibling_full_name)

                # 3) Fallback: short-name match only when unambiguous.
                if target is None:
                    matches = by_short_name.get(call_tail, [])
                    if len(matches) == 1:
                        target = matches[0]

                # 4) Namespace-safe final guard by concrete symbol_id map.
                if target is not None:
                    resolved = by_symbol_id.get(target["symbol_id"])
                    if resolved is not None and caller not in resolved["used_by"]:
                        resolved["used_by"].append(caller)

    def _sha256_of_file(self, path: Path) -> str:
        """Return SHA256 hex digest for a file."""
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
