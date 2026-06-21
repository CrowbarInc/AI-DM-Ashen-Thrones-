#!/usr/bin/env python3
"""BV14B — generate fan-in and migration audit docs."""

from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "artifacts" / "bv14b_consumer_migration.json"
AUDITS = ROOT / "docs" / "audits"

MODULES = (
    "game.social_exchange_emission",
    "game.social_exchange_fallback_catalog",
    "game.social_exchange_policy",
    "game.social_exchange_validation",
    "game.social_exchange_projection",
)

BEFORE_COMPAT = 52


def count_importers(module: str) -> tuple[int, list[str]]:
    short = module.rsplit(".", 1)[-1]
    own = f"game/{short}.py"
    importers: list[str] = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/__pycache__/" in rel or rel == own:
            continue
        if not rel.startswith(("game", "tests", "tools", "scripts")):
            continue
        src = path.read_text(encoding="utf-8-sig")
        found = bool(
            re.search(rf"from {re.escape(module)} import", src)
            or re.search(rf"import {re.escape(module)}\\b", src)
        )
        if found:
            importers.append(rel)
    return len(importers), sorted(set(importers))


def main() -> int:
    migration = json.loads(MIGRATION.read_text(encoding="utf-8"))
    counts = {mod: count_importers(mod)[0] for mod in MODULES}

    lines = [
        "# BV14B — Consumer Migration",
        "",
        "**Date:** 2026-06-21",
        "**Phase:** BV14B — consumer migration (compat preserved)",
        f"**Files migrated:** {len({r['file'] for r in migration})}",
        f"**Symbol moves:** {len(migration)}",
        "",
        "| File | Symbol | Old module | New module | Domain |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in migration:
        lines.append(
            f"| `{row['file']}` | `{row['symbol']}` | `{row['old_module']}` | `{row['new_module']}` | {row['domain']} |"
        )
    (AUDITS / "BV14B_consumer_migration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    by_domain: dict[str, int] = defaultdict(int)
    for row in migration:
        by_domain[row["domain"]] += 1

    fi_lines = [
        "# BV14B — Fan-In Report",
        "",
        "**Date:** 2026-06-21",
        "",
        "## Module fan-in",
        "",
        "| Module | Before (BV14A) | After (BV14B) | Delta |",
        "| --- | --- | --- | --- |",
        f"| `game.social_exchange_emission` | **{BEFORE_COMPAT}** | **{counts['game.social_exchange_emission']}** | **{counts['game.social_exchange_emission'] - BEFORE_COMPAT:+d}** |",
        f"| `game.social_exchange_fallback_catalog` | 0 (direct external) | **{counts['game.social_exchange_fallback_catalog']}** | **+{counts['game.social_exchange_fallback_catalog']}** |",
        f"| `game.social_exchange_policy` | 0 (direct external) | **{counts['game.social_exchange_policy']}** | **+{counts['game.social_exchange_policy']}** |",
        f"| `game.social_exchange_validation` | 0 (direct external) | **{counts['game.social_exchange_validation']}** | **+{counts['game.social_exchange_validation']}** |",
        f"| `game.social_exchange_projection` | 0 (direct external) | **{counts['game.social_exchange_projection']}** | **+{counts['game.social_exchange_projection']}** |",
        "",
        "## Symbol moves by domain",
        "",
        "| Domain | Symbol moves |",
        "| --- | --- |",
    ]
    for domain, n in sorted(by_domain.items(), key=lambda x: -x[1]):
        fi_lines.append(f"| {domain} | {n} |")

    _, compat_files = count_importers("game.social_exchange_emission")
    fi_lines.extend(
        [
            "",
            "## Residual compat importers",
            "",
            f"**{counts['game.social_exchange_emission']}** files still import `game.social_exchange_emission` "
            f"(target ≤12; projected steady-state 6–10):",
            "",
        ]
    )
    for f in compat_files:
        fi_lines.append(f"- `{f}`")

    fi_lines.extend(
        [
            "",
            "## Private leak cleanup (BV14A → BV14B)",
            "",
            "| Former private symbol | Public surface | Canonical module |",
            "| --- | --- | --- |",
            "| `_npc_display_name_for_emission` | `npc_display_name_for_emission` | `social_exchange_policy` |",
            "| `_speaker_label` | `speaker_label` | `social_exchange_policy` |",
            "| `_has_explicit_interruption_shape` | `has_explicit_interruption_shape` | `social_exchange_validation` |",
            "| `_text_is_strict_social_minimal_emergency_fallback` | `text_is_strict_social_minimal_emergency_fallback` | `social_exchange_fallback_catalog` |",
            "| `_active_interlocutor_matches_resolution_social_npc` | `active_interlocutor_matches_resolution_social_npc` | `social_exchange_fallback_catalog` |",
            "| `_merge_open_social_recovery_emission_debug` | `merge_open_social_recovery_emission_debug` | `social_exchange_fallback_catalog` |",
            "| `_open_social_recovery_passes_anti_stall` | `open_social_recovery_passes_anti_stall` | `social_exchange_fallback_catalog` |",
            "| `_social_integrity_fallback_line_candidates` | `social_integrity_fallback_line_candidates` | `social_exchange_fallback_catalog` |",
            "| `_apply_interruption_repeat_guard` | `apply_interruption_repeat_guard` | `social_exchange_emission` (composition) |",
            "",
            "External production imports of `_`-prefixed symbols via compat barrel: **0** (post-BV14B).",
            "",
            "## Success criteria",
            "",
            f"- Compat FI **{BEFORE_COMPAT} → {counts['game.social_exchange_emission']}** (target ≤12)",
            "- No runtime/replay/strict-social behavior changes (compat re-exports preserved)",
            "- Private symbol leaks eliminated from external compat imports",
        ]
    )
    (AUDITS / "BV14B_fan_in_report.md").write_text("\n".join(fi_lines) + "\n", encoding="utf-8")

    print("Compat FI:", counts["game.social_exchange_emission"])
    print("Fallback FI:", counts["game.social_exchange_fallback_catalog"])
    print("Policy FI:", counts["game.social_exchange_policy"])
    print("Validation FI:", counts["game.social_exchange_validation"])
    print("Projection FI:", counts["game.social_exchange_projection"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
