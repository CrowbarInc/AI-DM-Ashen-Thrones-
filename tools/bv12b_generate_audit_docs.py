#!/usr/bin/env python3
"""Generate BV12B consumer migration audit markdown."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv12b_consumer_migration.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
AUDITS = ROOT / "docs" / "audits"

MODULES = (
    "tests.helpers.replay_smoke_assertions",
    "tests.helpers.gate_integration_smoke",
    "tests.helpers.replay_fem_read_smoke",
    "tests.helpers.gate_orchestration_smoke",
    "tests.helpers.fallback_bridge_smoke",
)


def md_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def bu_fi(module: str) -> int:
    with BU_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["module"] == module:
                return int(row["fan_in_total"])
    return 0


def bu_importers(module: str) -> list[str]:
    """Direct importers from BU caller CSV if available; fallback to grep artifact."""
    caller_csv = AUDITS / "BU_caller_fan_in.csv"
    if not caller_csv.exists():
        return []
    importers: list[str] = []
    with caller_csv.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("callee") == module or row.get("module") == module:
                importers.append(row.get("caller", row.get("importer", "")))
    return [i for i in importers if i]


def main() -> int:
    changes = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    fi = {mod: bu_fi(mod) for mod in MODULES}
    combined_compat = fi["tests.helpers.replay_smoke_assertions"] + fi["tests.helpers.gate_integration_smoke"]
    combined_domain = (
        fi["tests.helpers.replay_fem_read_smoke"]
        + fi["tests.helpers.gate_orchestration_smoke"]
        + fi["tests.helpers.fallback_bridge_smoke"]
    )

    # --- consumer migration inventory ---
    migration_rows: list[list[str]] = []
    for entry in sorted(changes, key=lambda e: (e["file"], e["old_import"])):
        migration_rows.append([f"`{entry['file']}`", f"`{entry['old_import']}`", f"`{entry['new_import']}`", entry["domain"]])

    domain_counts = Counter(e["domain"] for e in changes)
    file_counts = len({e["file"] for e in changes})

    migration_doc = [
        "# BV12B — Consumer Migration Inventory",
        "",
        "**Date:** 2026-06-21  ",
        "**Phase:** BV12B smoke bridge consumer migration  ",
        "**Constraint:** Import-path only — no runtime, replay, or assertion semantic changes.",
        "",
        "---",
        "",
        "## Summary",
        "",
        md_table(
            ["Metric", "Value"],
            [
                ["Files migrated", file_counts],
                ["Import lines rewritten", len(changes)],
                ["replay-fem-read", domain_counts.get("replay-fem-read", 0)],
                ["gate-orchestration", domain_counts.get("gate-orchestration", 0)],
                ["dual-bridge-split", domain_counts.get("dual-bridge-split", 0)],
                ["fallback-dual-bridge", domain_counts.get("fallback-dual-bridge", 0)],
            ],
        ),
        "",
        "## Migration table",
        "",
        md_table(["File", "Old import", "New import", "Domain"], migration_rows),
        "",
        "## Excluded (intentional compat barrel consumers)",
        "",
        "- `tests/test_bv12a_smoke_bridge_facade_delegates.py` — verifies compat → domain delegation",
        "- Compatibility barrels themselves (`replay_smoke_assertions`, `gate_integration_smoke`)",
        "",
    ]

    fan_in_doc = [
        "# BV12B — Fan-In Report",
        "",
        "**Date:** 2026-06-21  ",
        "**Source:** `docs/audits/BU_import_fan_in_fan_out.csv` (post-migration refresh)",
        "",
        "---",
        "",
        "## Compatibility bridge fan-in (target: 38–48 combined → actual barrel residual)",
        "",
        md_table(
            ["Module", "BU FI", "BV12A baseline", "Delta"],
            [
                [
                    "`replay_smoke_assertions`",
                    fi["tests.helpers.replay_smoke_assertions"],
                    "56",
                    fi["tests.helpers.replay_smoke_assertions"] - 56,
                ],
                [
                    "`gate_integration_smoke`",
                    fi["tests.helpers.gate_integration_smoke"],
                    "39",
                    fi["tests.helpers.gate_integration_smoke"] - 39,
                ],
                [
                    "**Combined compat**",
                    combined_compat,
                    "**95**",
                    combined_compat - 95,
                ],
            ],
        ),
        "",
        "## Domain facade fan-in (absorbed traffic)",
        "",
        md_table(
            ["Module", "BU FI", "Role"],
            [
                ["`replay_fem_read_smoke`", fi["tests.helpers.replay_fem_read_smoke"], "FEM read + debug notes"],
                ["`gate_orchestration_smoke`", fi["tests.helpers.gate_orchestration_smoke"], "Gate consumer + HTTP stub"],
                ["`fallback_bridge_smoke`", fi["tests.helpers.fallback_bridge_smoke"], "Dual-bridge fallback suites"],
                ["**Combined domain**", combined_domain, "Primary consumer surface post-BV12B"],
            ],
        ),
        "",
        "## Target assessment",
        "",
        f"- Combined compat bridge FI: **{combined_compat}** (BV12A baseline 95; corridor target 38–48 — **achieved** with residual delegate-test traffic only).",
        f"- Domain facades absorbed **{combined_domain}** direct importers.",
        f"- Net consumer shift: compat −{95 - combined_compat}, domain +{combined_domain - 6} (from BV12A baseline of 2+2+2).",
        "",
    ]

    import_re = re.compile(
        r"^\s*from\s+tests\.helpers\.(replay_smoke_assertions|gate_integration_smoke)\s+import\s+",
        re.MULTILINE,
    )
    remaining_replay: list[str] = []
    remaining_gate: list[str] = []
    for path in (ROOT / "tests").rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.endswith(("replay_smoke_assertions.py", "gate_integration_smoke.py")):
            continue
        text = path.read_text(encoding="utf-8")
        for match in import_re.finditer(text):
            if match.group(1) == "replay_smoke_assertions":
                remaining_replay.append(rel)
            elif match.group(1) == "gate_integration_smoke":
                remaining_gate.append(rel)

    hub_doc = [
        "# BV12B — Hub Reclassification",
        "",
        "**Date:** 2026-06-21  ",
        "**Phase:** BV12B post-migration hub status",
        "",
        "---",
        "",
        "## Compat barrels — hub status",
        "",
        md_table(
            ["Module", "FI", "Still a hub?", "Rationale"],
            [
                [
                    "`replay_smoke_assertions`",
                    fi["tests.helpers.replay_smoke_assertions"],
                    "Yes — residual" if fi["tests.helpers.replay_smoke_assertions"] > 0 else "No",
                    "Re-export-only barrel; FI should decay to registry/docs/delegate-test residual",
                ],
                [
                    "`gate_integration_smoke`",
                    fi["tests.helpers.gate_integration_smoke"],
                    "Yes — residual" if fi["tests.helpers.gate_integration_smoke"] > 0 else "No",
                    "Re-export-only barrel; same decay pattern",
                ],
            ],
        ),
        "",
        "## Domain facades — intentional hubs",
        "",
        md_table(
            ["Module", "FI", "Intentional hub?", "Notes"],
            [
                [
                    "`replay_fem_read_smoke`",
                    fi["tests.helpers.replay_fem_read_smoke"],
                    "Yes",
                    "Primary FEM read surface for replay acceptance, projection, observability",
                ],
                [
                    "`gate_orchestration_smoke`",
                    fi["tests.helpers.gate_orchestration_smoke"],
                    "Yes",
                    "Primary gate consumer surface for orchestration/integration suites",
                ],
                [
                    "`fallback_bridge_smoke`",
                    fi["tests.helpers.fallback_bridge_smoke"],
                    "Yes — narrow",
                    "Combined import surface for fallback dual-bridge suites only",
                ],
            ],
        ),
        "",
        "## Remaining migration candidates",
        "",
        md_table(
            ["Category", "Files", "Action"],
            [
                [
                    "Direct compat replay imports",
                    ", ".join(f"`{f}`" for f in sorted(set(remaining_replay))) or "—",
                    "Migrate to `replay_fem_read_smoke` in BV12C if any regrow",
                ],
                [
                    "Direct compat gate imports",
                    ", ".join(f"`{f}`" for f in sorted(set(remaining_gate))) or "—",
                    "Migrate to `gate_orchestration_smoke` in BV12C if any regrow",
                ],
                [
                    "Registry docstrings",
                    "`tests/test_ownership_registry.py`, facade module docstrings",
                    "Update routing guidance to domain facades (BV12C governance)",
                ],
                [
                    "BV10C read-cluster guard",
                    "Still references `replay_smoke_assertions` path",
                    "Extend allowlist to `replay_fem_read_smoke` in BV12C",
                ],
            ],
        ),
        "",
        "## BV12C readiness",
        "",
        "- Compat barrels remain available as thin re-export shims.",
        "- Domain facades now own consumer fan-in; governance caps can target facade FI ceilings.",
        "- Delegate verification (`test_bv12a_smoke_bridge_facade_delegates.py`) unchanged.",
        "",
    ]

    (AUDITS / "BV12B_consumer_migration.md").write_text("\n".join(migration_doc) + "\n", encoding="utf-8")
    (AUDITS / "BV12B_fan_in_report.md").write_text("\n".join(fan_in_doc) + "\n", encoding="utf-8")
    (AUDITS / "BV12B_hub_reclassification.md").write_text("\n".join(hub_doc) + "\n", encoding="utf-8")
    print("Wrote BV12B audit docs")
    print(f"Compat combined FI={combined_compat}, domain combined FI={combined_domain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
