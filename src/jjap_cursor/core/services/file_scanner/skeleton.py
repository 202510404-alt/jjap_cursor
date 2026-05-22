"""AST skeleton extraction and rendering."""

from __future__ import annotations

import ast


def extract_skeleton(module: ast.Module) -> str:
    """Create a minimal AST skeleton with signatures and docstrings."""
    lines: list[str] = []
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines.extend(render_function_skeleton(node, indent=0))
        elif isinstance(node, ast.ClassDef):
            lines.extend(render_class_skeleton(node))
    return "\n".join(lines).strip()


def render_class_skeleton(node: ast.ClassDef) -> list[str]:
    """Render class skeleton with method signatures and class docstring."""
    out = [f"class {node.name}:"]
    class_doc = ast.get_docstring(node)
    if class_doc:
        out.append(f'    """{class_doc}"""')
    method_count = 0
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.extend(render_function_skeleton(child, indent=1))
            method_count += 1
    if method_count == 0 and not class_doc:
        out.append("    ...")
    return out


def render_function_skeleton(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    indent: int,
) -> list[str]:
    """Render one function skeleton preserving signature and docstring."""
    pad = "    " * indent
    async_kw = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    signature = build_signature(node)
    out = [f"{pad}{async_kw}def {node.name}{signature}:"]

    doc = ast.get_docstring(node)
    if doc:
        out.append(f'{pad}    """{doc}"""')
    out.append(f"{pad}    ...")
    return out


def build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Build human-readable function signature from AST arguments."""
    args = node.args
    parts: list[str] = []

    posonly = list(args.posonlyargs)
    normal = list(args.args)
    defaults = list(args.defaults)
    default_offset = len(posonly) + len(normal) - len(defaults)

    all_pos = posonly + normal
    for idx, arg in enumerate(all_pos):
        text = render_arg(arg)
        default_idx = idx - default_offset
        if default_idx >= 0:
            text += f" = {ast.unparse(defaults[default_idx])}"
        parts.append(text)

    if posonly:
        parts.insert(len(posonly), "/")

    if args.vararg:
        parts.append(f"*{render_arg(args.vararg)}")
    elif args.kwonlyargs:
        parts.append("*")

    for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
        text = render_arg(kwarg)
        if default is not None:
            text += f" = {ast.unparse(default)}"
        parts.append(text)

    if args.kwarg:
        parts.append(f"**{render_arg(args.kwarg)}")

    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"({', '.join(parts)}){returns}"


def render_arg(arg: ast.arg) -> str:
    """Render argument with annotation when it exists."""
    if arg.annotation is None:
        return arg.arg
    return f"{arg.arg}: {ast.unparse(arg.annotation)}"
