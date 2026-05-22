"""Symbol table extraction and call-graph metadata."""

from __future__ import annotations

import ast
from typing import Any

from .skeleton import build_signature


def extract_symbols(module: ast.Module, rel_path: str) -> list[dict[str, Any]]:
    """Extract symbol metadata including decorators, range, and call edges."""
    symbols: list[dict[str, Any]] = []

    for node in module.body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(symbol_entry(child, rel_path, parent=node.name, symbol_type="method"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(symbol_entry(node, rel_path, parent=None, symbol_type="function"))

    return symbols


def symbol_entry(
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
        "signature": build_signature(node),
        "calls": sorted(extract_calls(node)),
        "used_by": [],
    }


def extract_calls(node: ast.AST) -> set[str]:
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


def populate_used_by(symbols: list[dict[str, Any]]) -> None:
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
