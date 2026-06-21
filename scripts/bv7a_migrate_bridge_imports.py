"""BV7A: migrate bridge symbol imports off emission_smoke_assertions monolith."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONOLITH = "tests.helpers.emission_smoke_assertions"
REPLAY_MOD = "tests.helpers.replay_smoke_assertions"
GATE_MOD = "tests.helpers.gate_integration_smoke"

REPLAY_SYMBOLS = frozenset({"final_emission_meta_from_output", "read_turn_debug_notes"})
GATE_SYMBOLS = frozenset({"apply_final_emission_gate_consumer", "gm_response_stub"})


def parse_import_blocks(src: str) -> list[tuple[int, int, str, list[str]]]:
    """Return (start_line, end_line, module, symbols) for ImportFrom blocks."""
    blocks: list[tuple[int, int, str, list[str]]] = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return blocks
    lines = src.splitlines()
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != MONOLITH:
            continue
        syms = [a.asname or a.name for a in node.names if a.name != "*"]
        if not syms:
            continue
        start = node.lineno - 1
        end = node.end_lineno or node.lineno
        blocks.append((start, end, node.module, syms))
    return blocks


def format_import(module: str, symbols: list[str]) -> str:
    if len(symbols) == 1:
        return f"from {module} import {symbols[0]}"
    inner = ",\n    ".join(symbols)
    return f"from {module} import (\n    {inner},\n)"


def migrate_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    blocks = parse_import_blocks(src)
    lines = src.splitlines(keepends=True)

    all_replay: list[str] = []
    all_gate: list[str] = []
    all_mono: list[str] = []
    remove_ranges: list[tuple[int, int]] = []

    for start, end, _mod, syms in blocks:
        remove_ranges.append((start, end))
        for s in syms:
            base = s.split(" as ")[0].strip()
            if base in REPLAY_SYMBOLS:
                all_replay.append(s)
            elif base in GATE_SYMBOLS:
                all_gate.append(s)
            else:
                all_mono.append(s)

    if not remove_ranges:
        new_src = src
        new_src = re.sub(
            rf"from {MONOLITH.replace('.', r'\.')} import apply_final_emission_gate_consumer\b",
            f"from {GATE_MOD} import apply_final_emission_gate_consumer",
            new_src,
        )
        new_src = re.sub(
            rf"from {MONOLITH.replace('.', r'\.')} import final_emission_meta_from_output\b",
            f"from {REPLAY_MOD} import final_emission_meta_from_output",
            new_src,
        )
        if new_src != src:
            path.write_text(new_src, encoding="utf-8")
            return True
        return False

    new_imports: list[str] = []
    if all_replay:
        new_imports.append(format_import(REPLAY_MOD, sorted(set(all_replay), key=str.lower)))
    if all_gate:
        new_imports.append(format_import(GATE_MOD, sorted(set(all_gate), key=str.lower)))
    if all_mono:
        new_imports.append(format_import(MONOLITH, sorted(set(all_mono), key=str.lower)))

    if not new_imports:
        return False

    # Apply removals from bottom to top
    new_lines = list(lines)
    for start, end in sorted(remove_ranges, reverse=True):
        del new_lines[start:end]

    insert_at = remove_ranges[0][0] if remove_ranges else 0
    replacement = "\n".join(new_imports) + "\n"
    if insert_at < len(new_lines) and not new_lines[insert_at - 1].endswith("\n"):
        replacement += "\n"
    new_lines.insert(insert_at, replacement)

    new_src = "".join(new_lines)

    # lazy imports inside functions
    new_src = re.sub(
        rf"from {MONOLITH.replace('.', r'\.')} import apply_final_emission_gate_consumer\b",
        f"from {GATE_MOD} import apply_final_emission_gate_consumer",
        new_src,
    )
    new_src = re.sub(
        rf"from {MONOLITH.replace('.', r'\.')} import final_emission_meta_from_output\b",
        f"from {REPLAY_MOD} import final_emission_meta_from_output",
        new_src,
    )

    if new_src != src:
        path.write_text(new_src, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "tests/helpers/emission_smoke_assertions.py":
            continue
        if rel.startswith(".git/"):
            continue
        if MONOLITH.split(".")[-1] not in path.read_text(encoding="utf-8"):
            continue
        if MONOLITH not in path.read_text(encoding="utf-8"):
            continue
        if migrate_file(path):
            changed.append(rel)
    print(f"Migrated {len(changed)} files:")
    for c in changed:
        print(f"  {c}")


if __name__ == "__main__":
    main()
