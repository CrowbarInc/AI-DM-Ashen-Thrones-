#!/usr/bin/env python3
"""BV13B — migrate final_emission_text consumers to formatting/policy authorities."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("game", "tests")
OLD = "game.final_emission_text"
FMT = "game.final_emission_text_formatting"
POL = "game.final_emission_text_policy"
LEG = "game.final_emission_text_legacy_semantic_repair"

SKIP = frozenset(
    {
        "game/final_emission_text.py",
        "tests/test_bv13a_final_emission_text_facade_delegates.py",
        "tests/helpers/gate_thin_boundary_locks.py",
        "tools/bv13b_migrate_consumers.py",
    }
)

FORMATTING = frozenset(
    {
        "_normalize_text",
        "_normalize_text_preserve_paragraphs",
        "_sanitize_output_text",
        "_normalize_terminal_punctuation",
        "_capitalize_sentence_fragment",
        "_has_terminal_punctuation",
    }
)
POLICY = frozenset(
    {
        "_RESPONSE_TYPE_VALUES",
        "_ANSWER_DIRECT_PATTERNS",
        "_ANSWER_FILLER_PATTERNS",
        "_ACTION_RESULT_PATTERNS",
        "_AGENCY_SUBSTITUTE_PATTERNS",
        "_ACTION_STOPWORDS",
    }
)
COMPAT = frozenset(
    {
        "_global_narrative_fallback_stock_line",
        "_decompress_overpacked_sentences",
        "_repair_fragmentary_participial_splits",
    }
)


def parse_imports(source: str) -> list[tuple[int, int, str, list[str]]]:
    """Return (start, end, module, symbols) for each ImportFrom from OLD."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    hits: list[tuple[int, int, str, list[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != OLD:
            continue
        syms = [a.name for a in node.names if a.name != "*"]
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        hits.append((start, end, OLD, syms))
    return hits


def render_import(module: str, symbols: list[str]) -> str:
    if len(symbols) == 1:
        return f"from {module} import {symbols[0]}\n"
    inner = ",\n".join(f"    {s}" for s in symbols)
    return f"from {module} import (\n{inner},\n)\n"


def migrate_file(path: Path) -> list[dict]:
    rel = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8-sig")
    hits = parse_imports(source)
    if not hits:
        return []

    records: list[dict] = []
    lines = source.splitlines(keepends=True)

    # Process bottom-up to preserve line indices.
    for start, end, _mod, syms in reversed(hits):
        fmt_syms = sorted(s for s in syms if s in FORMATTING)
        pol_syms = sorted(s for s in syms if s in POLICY)
        compat_syms = sorted(s for s in syms if s in COMPAT)
        unknown = sorted(set(syms) - FORMATTING - POLICY - COMPAT)
        if unknown:
            raise RuntimeError(f"{rel}: unknown symbols {unknown}")

        new_blocks: list[str] = []
        if fmt_syms:
            new_blocks.append(render_import(FMT, fmt_syms))
        if pol_syms:
            new_blocks.append(render_import(POL, pol_syms))
        if compat_syms:
            if any(s in COMPAT - {"_global_narrative_fallback_stock_line"} for s in compat_syms):
                legacy = [s for s in compat_syms if s != "_global_narrative_fallback_stock_line"]
                stock = [s for s in compat_syms if s == "_global_narrative_fallback_stock_line"]
                if legacy:
                    new_blocks.append(render_import(LEG, legacy))
                if stock:
                    new_blocks.append(render_import(OLD, stock))
            else:
                new_blocks.append(render_import(OLD, compat_syms))

        replacement = "".join(new_blocks)
        lines[start:end] = [replacement]

        for sym in fmt_syms:
            records.append(
                {"file": rel, "symbol": sym, "old_module": OLD, "new_module": FMT}
            )
        for sym in pol_syms:
            records.append(
                {"file": rel, "symbol": sym, "old_module": OLD, "new_module": POL}
            )
        for sym in compat_syms:
            if sym in {"_decompress_overpacked_sentences", "_repair_fragmentary_participial_splits"}:
                records.append(
                    {"file": rel, "symbol": sym, "old_module": OLD, "new_module": LEG}
                )
            else:
                records.append(
                    {"file": rel, "symbol": sym, "old_module": OLD, "new_module": OLD}
                )

    path.write_text("".join(lines), encoding="utf-8")
    return records


def main() -> int:
    all_records: list[dict] = []
    for root_name in SCAN_ROOTS:
        for path in sorted((ROOT / root_name).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel in SKIP or "/__pycache__/" in rel:
                continue
            all_records.extend(migrate_file(path))

    artifact = ROOT / "artifacts" / "bv13b_consumer_migration.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(all_records, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated {len({r['file'] for r in all_records})} files, {len(all_records)} symbol moves")
    print(f"Wrote {artifact.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
