"""BV7B: migrate consumer-layer symbol imports off emission_smoke_assertions monolith."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONOLITH = "tests.helpers.emission_smoke_assertions"
RT_MOD = "tests.helpers.response_type_smoke"
AC_MOD = "tests.helpers.actor_consistency_smoke"
RD_MOD = "tests.helpers.route_determinism_smoke"

RT_SYMBOLS = frozenset(
    {
        "response_type_contract",
        "assert_response_type_meta",
        "assert_response_type_contract_surfaces",
        "enforce_response_type_contract_layer",
    }
)
AC_SYMBOLS = frozenset(
    {
        "validate_answer_completeness",
        "apply_answer_completeness_layer",
        "skip_answer_completeness_layer",
    }
)
RD_SYMBOLS = frozenset(
    {
        "validate_response_delta",
        "apply_response_delta_layer",
        "skip_response_delta_layer",
        "strict_social_answer_pressure_rd_contract_active",
        "inspect_response_delta_failure",
        "assert_response_delta_boundary_validate_only",
        "assert_no_boundary_reorder_repair",
    }
)


def parse_import_blocks(src: str) -> list[tuple[int, int, str, list[str]]]:
    blocks: list[tuple[int, int, str, list[str]]] = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return blocks
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


def classify_symbol(sym: str) -> str:
    base = sym.split(" as ")[0].strip()
    if base in RT_SYMBOLS:
        return "rt"
    if base in AC_SYMBOLS:
        return "ac"
    if base in RD_SYMBOLS:
        return "rd"
    return "mono"


def migrate_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    blocks = parse_import_blocks(src)
    lines = src.splitlines(keepends=True)

    all_rt: list[str] = []
    all_ac: list[str] = []
    all_rd: list[str] = []
    all_mono: list[str] = []
    remove_ranges: list[tuple[int, int]] = []

    for start, end, _mod, syms in blocks:
        remove_ranges.append((start, end))
        for s in syms:
            bucket = classify_symbol(s)
            if bucket == "rt":
                all_rt.append(s)
            elif bucket == "ac":
                all_ac.append(s)
            elif bucket == "rd":
                all_rd.append(s)
            else:
                all_mono.append(s)

    if not remove_ranges:
        return False

    new_imports: list[str] = []
    if all_rt:
        new_imports.append(format_import(RT_MOD, sorted(set(all_rt), key=str.lower)))
    if all_ac:
        new_imports.append(format_import(AC_MOD, sorted(set(all_ac), key=str.lower)))
    if all_rd:
        new_imports.append(format_import(RD_MOD, sorted(set(all_rd), key=str.lower)))
    if all_mono:
        new_imports.append(format_import(MONOLITH, sorted(set(all_mono), key=str.lower)))

    if not new_imports:
        return False

    new_lines = list(lines)
    for start, end in sorted(remove_ranges, reverse=True):
        del new_lines[start:end]

    insert_at = remove_ranges[0][0] if remove_ranges else 0
    import_block = "\n".join(new_imports) + "\n"
    new_lines.insert(insert_at, import_block)

    path.write_text("".join(new_lines), encoding="utf-8")
    return True


def main() -> None:
    migrated = 0
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("tests/helpers/emission_smoke_assertions"):
            continue
        if rel.startswith("scripts/bv7b_"):
            continue
        src = path.read_text(encoding="utf-8")
        if MONOLITH not in src:
            continue
        if migrate_file(path):
            print(f"migrated: {rel}")
            migrated += 1
    print(f"total migrated: {migrated}")


if __name__ == "__main__":
    main()
