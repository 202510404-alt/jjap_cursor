"""Concrete context builder with token estimation and granular eviction."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..interfaces.context_builder import ContextBuilder
from ..types import BudgetPriority, ContextBundle, EditPlan, SymbolSlice


class DefaultContextBuilder(ContextBuilder):
    """Default v8.0 context builder focused on budget-safe symbol packing."""

    def __init__(self, project_root: Path, max_tokens: int = 16000) -> None:
        """Initialize builder with project root and base token budget."""
        self.project_root = project_root
        self.max_tokens = max_tokens

    def set_budget(self, max_tokens: int) -> None:
        """Configure maximum token budget for the next context assembly."""
        self.max_tokens = max_tokens

    def collect_target_context(self, plan: EditPlan, user_query: str) -> list[SymbolSlice]:
        """Collect highest-priority target symbols tied directly to requested edits."""
        symbol_table = self._read_symbol_table()
        target_files = {step.target_file.as_posix() for step in plan.steps}
        targets: list[SymbolSlice] = []

        for entry in symbol_table:
            if entry.get("file") not in target_files:
                continue
            content = f'{entry.get("name")} {entry.get("signature", "")}'
            sid = entry.get("symbol_id") or f'{entry.get("file")}::{entry.get("name")}'
            targets.append(
                SymbolSlice(
                    symbol_id=sid,
                    file_path=self.project_root / entry.get("file", ""),
                    content=content.strip(),
                    token_cost=self.estimate_tokens(content),
                    priority="target",
                    score=1.0,
                )
            )
        return targets

    def collect_related_symbols(self, plan: EditPlan) -> list[SymbolSlice]:
        """Collect relational symbols through import and call-graph dependencies."""
        symbol_table = self._read_symbol_table()
        target_names = {step.target_file.stem for step in plan.steps}
        related: list[SymbolSlice] = []

        for entry in symbol_table:
            calls = entry.get("calls", [])
            used_by = entry.get("used_by", [])
            if not any(name in " ".join(calls + used_by) for name in target_names):
                continue
            content = f'{entry.get("name")} {entry.get("signature", "")}'
            sid = entry.get("symbol_id") or f'{entry.get("file")}::{entry.get("name")}'
            related.append(
                SymbolSlice(
                    symbol_id=sid,
                    file_path=self.project_root / entry.get("file", ""),
                    content=content.strip(),
                    token_cost=self.estimate_tokens(content),
                    priority="related_symbols",
                    score=0.5,
                )
            )
        return related

    def collect_facts(self, project_root: Path) -> list[str]:
        """Load stable facts and approved notes from persistent project memory."""
        briefing = project_root / "ai_briefing.md"
        if not briefing.exists():
            return []
        return [line.strip() for line in briefing.read_text(encoding="utf-8").splitlines() if line.strip()]

    def collect_skeletons(self, plan: EditPlan) -> list[str]:
        """Load AST skeleton snippets for lower-priority structural context."""
        context_path = self.project_root / ".jjap_context.json"
        if not context_path.exists():
            return []

        payload = json.loads(context_path.read_text(encoding="utf-8"))
        files_block = payload.get("files", {})
        target_files = {step.target_file.as_posix() for step in plan.steps}

        if isinstance(files_block, dict) and files_block:
            out: list[str] = []
            for path, meta in files_block.items():
                if path not in target_files:
                    continue
                if isinstance(meta, dict):
                    sk = meta.get("skeleton", "")
                else:
                    sk = str(meta)
                if sk:
                    out.append(sk)
            return out

        skeletons = payload.get("skeletons", {})
        return [text for path, text in skeletons.items() if path in target_files]

    def build_planning_context(self, user_query: str) -> str:
        """Build lightweight text context for AI planning (metadata + scored skeletons)."""
        context_path = self.project_root / ".jjap_context.json"
        if not context_path.exists():
            return "No project index (.jjap_context.json). Run a scan before planning.\n"

        payload = json.loads(context_path.read_text(encoding="utf-8"))
        files_block = payload.get("files", {})
        if not isinstance(files_block, dict) or not files_block:
            legacy = payload.get("skeletons", {})
            files_block = {
                rel: {"hash": "", "mtime": 0, "skeleton": text}
                for rel, text in legacy.items()
            }

        keywords = {w for w in re.findall(r"\w+", user_query.lower()) if len(w) > 1}

        scored: list[tuple[int, str, dict]] = []
        for rel_path, meta in files_block.items():
            if not isinstance(meta, dict):
                continue
            skeleton = meta.get("skeleton", "") or ""
            blob = f"{rel_path} {skeleton}".lower()
            score = sum(1 for k in keywords if k in blob) if keywords else 0
            scored.append((score, rel_path, meta))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

        lines: list[str] = []
        lines.append("## File index (relative path | hash[:16] | mtime)\n")
        manifest_cap = 80
        for idx, rel_path in enumerate(sorted(files_block.keys())):
            if idx >= manifest_cap:
                lines.append(f"... and {len(files_block) - manifest_cap} more files.\n")
                break
            meta = files_block.get(rel_path, {})
            if isinstance(meta, dict):
                h = (meta.get("hash") or "")[:16]
                mt = meta.get("mtime", 0)
            else:
                h, mt = "", 0
            lines.append(f"- {rel_path} | {h} | {mt}")

        symbol_table = self._read_symbol_table()
        symbol_hits: list[str] = []
        for entry in symbol_table:
            blob = f"{entry.get('symbol_id', '')} {entry.get('full_name', '')} {entry.get('file', '')}".lower()
            if keywords and any(k in blob for k in keywords):
                symbol_hits.append(str(entry.get("symbol_id", "")))
        if symbol_hits:
            lines.append("\n## Relevant symbol_ids (keyword heuristic)\n")
            for sid in symbol_hits[:50]:
                lines.append(f"- {sid}")

        lines.append("\n## Skeletons (highest relevance first, token-budgeted)\n")
        budget_tokens = min(self.max_tokens, 6000)
        used = self.estimate_tokens("\n".join(lines))

        for score, rel_path, meta in scored:
            if score < 0:
                continue
            sk = meta.get("skeleton", "") if isinstance(meta, dict) else ""
            if not sk.strip():
                continue
            block = f"### {rel_path}\n```python\n{sk.strip()}\n```\n"
            cost = self.estimate_tokens(block)
            if used + cost > budget_tokens:
                continue
            lines.append(block)
            used += cost

        return "\n".join(lines).strip() + "\n"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token cost for one text fragment or symbol payload."""
        if not text:
            return 0
        lexical_units = len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))
        char_based = max(1, len(text) // 4)
        return max(lexical_units, char_based)

    def evict_until_within_budget(
        self,
        slices: list[SymbolSlice],
        priority_order: list[BudgetPriority],
        max_tokens: int,
    ) -> list[SymbolSlice]:
        """Evict low-priority symbols first until total token cost fits the budget."""
        if max_tokens <= 0 or not slices:
            return []

        rank = {priority: idx for idx, priority in enumerate(priority_order)}
        kept = list(slices)
        total = sum(item.token_cost for item in kept)

        while kept and total > max_tokens:
            kept.sort(
                key=lambda item: (
                    -rank.get(item.priority, len(priority_order)),
                    item.score,
                    -item.token_cost,
                )
            )
            removed = kept.pop(0)
            total -= removed.token_cost

        return kept

    def assemble(self, plan: EditPlan, user_query: str) -> ContextBundle:
        """Build final context bundle ordered by target > related > facts > skeletons."""
        targets = self.collect_target_context(plan, user_query)
        related = self.collect_related_symbols(plan)
        facts = self.collect_facts(self.project_root)
        skeletons = self.collect_skeletons(plan)

        fact_slices = [
            SymbolSlice(
                symbol_id=f"fact::{idx}",
                file_path=self.project_root,
                content=fact,
                token_cost=self.estimate_tokens(fact),
                priority="facts",
                score=0.2,
            )
            for idx, fact in enumerate(facts)
        ]
        skeleton_slices = [
            SymbolSlice(
                symbol_id=f"skeleton::{idx}",
                file_path=self.project_root,
                content=text,
                token_cost=self.estimate_tokens(text),
                priority="skeletons",
                score=0.1,
            )
            for idx, text in enumerate(skeletons)
        ]

        merged = targets + related + fact_slices + skeleton_slices
        kept = self.evict_until_within_budget(
            merged,
            priority_order=["target", "related_symbols", "facts", "skeletons"],
            max_tokens=self.max_tokens,
        )

        target_kept = [s for s in kept if s.priority == "target"]
        related_kept = [s for s in kept if s.priority == "related_symbols"]
        fact_kept = [s.content for s in kept if s.priority == "facts"]
        skeleton_kept = [s.content for s in kept if s.priority == "skeletons"]

        return ContextBundle(
            total_tokens=sum(item.token_cost for item in kept),
            system_prompt="Plan-first. Output JSON only.",
            target_context=target_kept,
            related_symbols=related_kept,
            facts=fact_kept,
            skeletons=skeleton_kept,
        )

    def _read_symbol_table(self) -> list[dict]:
        """Read symbol table file generated by scanner."""
        symbols_path = self.project_root / ".jjap_symbols.json"
        if not symbols_path.exists():
            return []
        payload = json.loads(symbols_path.read_text(encoding="utf-8"))
        return payload.get("symbols", [])
