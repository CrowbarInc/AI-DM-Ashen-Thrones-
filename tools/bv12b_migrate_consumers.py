#!/usr/bin/env python3
"""BV12B — migrate smoke bridge consumers onto domain facades (import paths only)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("tests", "tools", "scripts")

FALLBACK_DUAL = frozenset(
    {
        "tests/test_fallback_overwrite_containment.py",
        "tests/test_fallback_shipped_contract_propagation.py",
        "tests/test_strict_social_emergency_fallback_dialogue.py",
    }
)

SKIP = frozenset(
    {
        "tests/test_bv12a_smoke_bridge_facade_delegates.py",
        "tests/helpers/replay_smoke_assertions.py",
        "tests/helpers/gate_integration_smoke.py",
        "tests/helpers/fallback_bridge_smoke.py",
        "tests/helpers/replay_fem_read_smoke.py",
        "tests/helpers/gate_orchestration_smoke.py",
    }
)

REPLAY_OLD = "tests.helpers.replay_smoke_assertions"
REPLAY_NEW = "tests.helpers.replay_fem_read_smoke"
GATE_OLD = "tests.helpers.gate_integration_smoke"
GATE_NEW = "tests.helpers.gate_orchestration_smoke"
FALLBACK_NEW = "tests.helpers.fallback_bridge_smoke"

IMPORT_LINE = re.compile(
    r"^(\s*)from\s+(tests\.helpers\.(?:replay_smoke_assertions|gate_integration_smoke|fallback_bridge_smoke))\s+import\s+(.+)$"
)


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _migrate_fallback_dual(text: str, rel: str) -> tuple[str, list[dict[str, str]]] | None:
    """Collapse replay+gate compat imports into one fallback_bridge_smoke import."""
    lines = text.splitlines(keepends=True)
    bridge_lines: list[tuple[int, str, str, str]] = []
    for idx, line in enumerate(lines):
        m = IMPORT_LINE.match(line.rstrip("\n"))
        if not m or m.group(2) not in (REPLAY_OLD, GATE_OLD):
            continue
        bridge_lines.append((idx, m.group(1), m.group(2), m.group(3).strip()))

    if not bridge_lines:
        return None

    indent = bridge_lines[0][1]
    merged_symbols = ", ".join(entry[3] for entry in bridge_lines)
    merged_line = f"{indent}from {FALLBACK_NEW} import {merged_symbols}\n"
    changes = [
        {
            "file": rel,
            "old_import": f"from {module} import {symbols}",
            "new_import": merged_line.strip(),
            "domain": "fallback-dual-bridge",
        }
        for _, _, module, symbols in bridge_lines
    ]

    out: list[str] = []
    inserted = False
    for idx, line in enumerate(lines):
        if any(idx == entry[0] for entry in bridge_lines):
            if not inserted:
                out.append(merged_line)
                inserted = True
            continue
        out.append(line)
    return "".join(out), changes


def migrate_file(path: Path) -> list[dict[str, str]] | None:
    rel = _rel(path)
    if rel in SKIP:
        return None

    text = path.read_text(encoding="utf-8")
    if REPLAY_OLD not in text and GATE_OLD not in text:
        return None

    had_replay = REPLAY_OLD in text
    had_gate = GATE_OLD in text
    use_fallback = rel in FALLBACK_DUAL and had_replay and had_gate

    if use_fallback:
        result = _migrate_fallback_dual(text, rel)
        if result is None:
            return None
        new_text, changes = result
        if new_text == text:
            return None
        path.write_text(new_text, encoding="utf-8")
        return changes

    changes: list[dict[str, str]] = []
    new_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        m = IMPORT_LINE.match(line.rstrip("\n"))
        if not m:
            new_lines.append(line)
            continue

        module, symbols = m.group(2), m.group(3).strip()
        if module not in (REPLAY_OLD, GATE_OLD):
            new_lines.append(line)
            continue

        indent = m.group(1)
        new_module = REPLAY_NEW if module == REPLAY_OLD else GATE_NEW
        new_line = f"{indent}from {new_module} import {symbols}\n"
        new_lines.append(new_line)
        domain = "replay-fem-read" if module == REPLAY_OLD else "gate-orchestration"
        if had_replay and had_gate:
            domain = "dual-bridge-split"
        changes.append(
            {
                "file": rel,
                "old_import": f"from {module} import {symbols}",
                "new_import": f"from {new_module} import {symbols}",
                "domain": domain,
            }
        )

    new_text = "".join(new_lines)
    if new_text == text:
        return None

    path.write_text(new_text, encoding="utf-8")
    return changes


def main() -> int:
    all_changes: list[dict[str, str]] = []
    for root_name in SCAN_ROOTS:
        for path in sorted((ROOT / root_name).rglob("*.py")):
            result = migrate_file(path)
            if result:
                all_changes.extend(result)

    out = ROOT / "artifacts" / "bv12b_consumer_migration.json"
    import json

    out.write_text(json.dumps(all_changes, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated {len({c['file'] for c in all_changes})} files, {len(all_changes)} import lines")
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
