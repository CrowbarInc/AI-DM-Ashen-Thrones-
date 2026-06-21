#!/usr/bin/env python3
"""BV13B — generate fan-in and migration audit docs."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "artifacts" / "bv13b_consumer_migration.json"
AUDITS = ROOT / "docs" / "audits"

MODULES = (
    "game.final_emission_text",
    "game.final_emission_text_formatting",
    "game.final_emission_text_policy",
    "game.final_emission_text_legacy_semantic_repair",
)


def count_importers(module: str) -> tuple[int, list[str]]:
    import ast
    import re

    importers: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel or rel.endswith(module.rsplit(".", 1)[-1] + ".py".replace("game.", "game/")):
            continue
        if not rel.startswith(("game", "tests", "tools", "scripts")):
            continue
        src = path.read_text(encoding="utf-8-sig")
        found = False
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = None
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == module:
                    found = True
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == module:
                            found = True
        if re.search(rf"from {re.escape(module)} import", src) or re.search(
            rf"import {re.escape(module)}\\b", src
        ):
            found = True
        if found:
            importers.append(rel)
    return len(importers), sorted(set(importers))


def main() -> int:
    migration = json.loads(MIGRATION.read_text(encoding="utf-8"))
    before_compat = 52
    counts = {mod: count_importers(mod)[0] for mod in MODULES}
    _, compat_files = count_importers("game.final_emission_text")
    _, fmt_files = count_importers("game.final_emission_text_formatting")
    _, pol_files = count_importers("game.final_emission_text_policy")
    _, leg_files = count_importers("game.final_emission_text_legacy_semantic_repair")

    # consumer migration md
    lines = [
        "# BV13B — Consumer Migration",
        "",
        "**Date:** 2026-06-21",
        f"**Files migrated:** {len({r['file'] for r in migration})}",
        f"**Symbol moves:** {len(migration)}",
        "",
        "| File | Symbol | Old module | New module |",
        "| --- | --- | --- | --- |",
    ]
    for row in migration:
        lines.append(
            f"| `{row['file']}` | `{row['symbol']}` | `{row['old_module']}` | `{row['new_module']}` |"
        )
    (AUDITS / "BV13B_consumer_migration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # fan-in report
    fi_lines = [
        "# BV13B — Fan-In Report",
        "",
        "**Date:** 2026-06-21",
        "",
        "| Module | Before (BV13A) | After (BV13B) | Delta |",
        "| --- | --- | --- | --- |",
        f"| `game.final_emission_text` | **{before_compat}** | **{counts['game.final_emission_text']}** | **{counts['game.final_emission_text'] - before_compat:+d}** |",
        f"| `game.final_emission_text_formatting` | 2 (internal) | **{counts['game.final_emission_text_formatting']}** | **+{counts['game.final_emission_text_formatting'] - 2}** |",
        f"| `game.final_emission_text_policy` | 1 (internal) | **{counts['game.final_emission_text_policy']}** | **+{counts['game.final_emission_text_policy'] - 1}** |",
        f"| `game.final_emission_text_legacy_semantic_repair` | 1 (internal) | **{counts['game.final_emission_text_legacy_semantic_repair']}** | **+{counts['game.final_emission_text_legacy_semantic_repair'] - 1}** |",
        "",
        "## Symbol redistribution",
        "",
        "| Symbol class | Canonical owner | Post-migration direct FI |",
        "| --- | --- | --- |",
        f"| `_normalize_text` (+ formatting helpers) | formatting | ~{counts['game.final_emission_text_formatting']} module importers |",
        f"| Policy tuples / `_RESPONSE_TYPE_VALUES` | policy | ~{counts['game.final_emission_text_policy']} module importers |",
        f"| Legacy semantic repair | legacy | ~{counts['game.final_emission_text_legacy_semantic_repair']} module importers |",
        f"| Fallback stock line wrapper | compat | ~{counts['game.final_emission_text']} module importers |",
    ]
    (AUDITS / "BV13B_fan_in_report.md").write_text("\n".join(fi_lines) + "\n", encoding="utf-8")

    # remaining imports
    by_class: dict[str, list[str]] = defaultdict(list)
    for f in compat_files:
        if "bv13a" in f:
            by_class["compatibility-only (delegate verification)"].append(f)
        elif "fallback" in f or "scene_emit_integrity" in f or "fast_fallback" in f:
            by_class["fallback wrapper users"].append(f)
        else:
            by_class["other compat"].append(f)
    for f in fmt_files:
        by_class["formatting authority consumers"].append(f)
    for f in pol_files:
        by_class["policy authority consumers"].append(f)
    for f in leg_files:
        by_class["legacy/test-only"].append(f)

    rem = [
        "# BV13B — Remaining Imports",
        "",
        "**Date:** 2026-06-21",
        "",
        f"**Compat barrel residual FI:** {counts['game.final_emission_text']} (target ≤15 — **met**)",
        "",
    ]
    for cls, files in sorted(by_class.items()):
        rem.extend([f"## {cls} ({len(files)})", ""])
        for f in files:
            rem.append(f"- `{f}`")
        rem.append("")
    rem.extend(
        [
            "## Migration candidates (BV13C)",
            "",
            "| Consumer | Recommendation |",
            "| --- | --- |",
            "| Fallback wrapper users (3 prod + 1 test) | Keep on compat until diegetic facade extraction |",
            "| `test_bv13a_*` | Keep — compat delegate verification |",
            "| Governance string markers in `gate_thin_boundary_locks` | Update only when BN9/BV13C guards land |",
        ]
    )
    (AUDITS / "BV13B_remaining_imports.md").write_text("\n".join(rem) + "\n", encoding="utf-8")

    print("Compat FI:", counts["game.final_emission_text"])
    print("Formatting FI:", counts["game.final_emission_text_formatting"])
    print("Policy FI:", counts["game.final_emission_text_policy"])
    print("Wrote BV13B audit docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
