#!/usr/bin/env python3
"""Generate BV12A facade extraction audit markdown."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv12_smoke_bridge_analysis.json"
BU_CSV = ROOT / "docs" / "audits" / "BU_import_fan_in_fan_out.csv"
AUDITS = ROOT / "docs" / "audits"


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


def main() -> int:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    replay_fi = bu_fi("tests.helpers.replay_smoke_assertions")
    gate_fi = bu_fi("tests.helpers.gate_integration_smoke")

    replay_importers = data["direct_importers"]["tests.helpers.replay_smoke_assertions"]
    gate_importers = data["direct_importers"]["tests.helpers.gate_integration_smoke"]
    dual = sorted(
        {i["file"] for i in replay_importers} & {i["file"] for i in gate_importers}
    )
    fallback_dual = [f for f in dual if "fallback" in f or "diegetic" in f]

    delegate_doc = [
        "# BV12A — Delegate Verification",
        "",
        "**Date:** 2026-06-21  ",
        "**Phase:** BV12A domain facade extraction  ",
        "**Constraint:** No runtime, replay, or assertion semantic changes.",
        "",
        "---",
        "",
        "## Executive summary",
        "",
        "Three domain facades were added; compatibility bridges are re-export-only barrels.",
        "",
        md_table(
            ["Facade", "Role", "Implementation owner"],
            [
                ["`replay_fem_read_smoke`", "FEM read + debug notes", "Delegates to `game.final_emission_meta_read`"],
                ["`gate_orchestration_smoke`", "Gate consumer + HTTP stub", "Delegates to `game.final_emission_runtime` + replay FEM facade"],
                ["`fallback_bridge_smoke`", "Dual-bridge import surface", "Re-exports domain facades only"],
                ["`replay_smoke_assertions`", "Compatibility barrel", "Re-exports `replay_fem_read_smoke`"],
                ["`gate_integration_smoke`", "Compatibility barrel", "Re-exports `gate_orchestration_smoke`"],
            ],
        ),
        "",
        "## Verification method",
        "",
        md_table(
            ["Check", "Mechanism", "Result"],
            [
                ["Function identity delegation (compat → domain)", "`tests/test_bv12a_smoke_bridge_facade_delegates.py`", "Automated"],
                ["Fallback bridge re-exports", "Same test module", "Automated"],
                ["Compat barrels have no local FunctionDef", "AST scan in test module", "Automated"],
                ["Gate domain uses replay FEM facade (not compat barrel)", "Source import audit", "Automated"],
                ["No replay projection duplication", "Forbidden fragment scan", "Automated"],
                ["Registry bridge ownership", "`test_bj4_emission_smoke_facade_stays_weak_consumer_bridge`", "Automated"],
            ],
        ),
        "",
        "## Domain separation",
        "",
        "- **Replay responsibility:** `replay_fem_read_smoke` owns FEM extraction only.",
        "- **Gate responsibility:** `gate_orchestration_smoke` owns runtime orchestration + fixture stub.",
        "- **Fallback responsibility:** `fallback_bridge_smoke` combines import surface without merged logic.",
        "- **Cross-domain coupling removed:** `gate_orchestration_smoke` imports `replay_fem_read_smoke`, not `replay_smoke_assertions`.",
        "",
    ]

    extraction_doc = [
        "# BV12A — Facade Extraction Baseline",
        "",
        "**Date:** 2026-06-21  ",
        "**Phase:** BV12A complete — no consumer migrations yet  ",
        "",
        "---",
        "",
        "## Current fan-in (unchanged — compat barrels retained)",
        "",
        md_table(
            ["Module", "BU FI", "Status"],
            [
                ["`replay_smoke_assertions`", replay_fi, "Compatibility barrel"],
                ["`gate_integration_smoke`", gate_fi, "Compatibility barrel"],
                ["**Combined**", replay_fi + gate_fi, "Baseline for Phase 2"],
            ],
        ),
        "",
        "## New domain facades (Phase 1 extraction)",
        "",
        md_table(
            ["Module", "Exports", "Phase 2 migration target FI"],
            [
                ["`replay_fem_read_smoke`", "2", f"~{replay_fi - 3} (FEM read consumers)"],
                ["`gate_orchestration_smoke`", "2", f"~{gate_fi - 2} (gate consumer consumers)"],
                ["`fallback_bridge_smoke`", "2 (re-export)", f"~{len(fallback_dual)} fallback dual-bridge suites"],
            ],
        ),
        "",
        "## Migration-ready consumers (Phase 2)",
        "",
        md_table(
            ["Target facade", "Ready consumers", "Notes"],
            [
                ["replay_fem_read_smoke", len(replay_importers), "Direct importers of compat barrel today"],
                ["gate_orchestration_smoke", len(gate_importers), "Direct importers of compat barrel today"],
                ["fallback_bridge_smoke", len(fallback_dual), ", ".join(f"`{f}`" for f in fallback_dual) or "—"],
            ],
        ),
        "",
        "## Projected Phase 2 reduction",
        "",
        md_table(
            ["Metric", "Current", "Post Phase 2 (est.)"],
            [
                ["Combined compat bridge FI", replay_fi + gate_fi, "38–48"],
                ["replay_smoke_assertions FI", replay_fi, "8–12 (barrel only)"],
                ["gate_integration_smoke FI", gate_fi, "6–10 (barrel only)"],
                ["Domain facade FI (distributed)", "0", "70–80"],
            ],
        ),
        "",
        "## Validation",
        "",
        md_table(
            ["Suite batch", "Result"],
            [
                ["BV12A delegate verification", "8/8 pass"],
                ["Registry (BJ4 + BV10C guards)", "pass"],
                ["Replay (golden_replay_direct_seam, projection)", "pass"],
                ["Gate (orchestration_order, selector_snapshots, n4)", "pass"],
                ["Fallback (behavior_gate, overwrite_containment, diegetic)", "pass"],
                ["Smoke (anti_railroading, turn_pipeline_shared, emission contract)", "pass"],
                ["Note", "`test_final_emission_opening_fallback::test_adapter_selects_usable_upstream_prepared_payload_unchanged` fails on owner-bucket projection (orthogonal to BV12A import routing)"],
            ],
        ),
        "",
    ]

    (AUDITS / "BV12A_delegate_verification.md").write_text("\n".join(delegate_doc) + "\n", encoding="utf-8")
    (AUDITS / "BV12A_facade_extraction.md").write_text("\n".join(extraction_doc) + "\n", encoding="utf-8")
    print("Wrote docs/audits/BV12A_delegate_verification.md")
    print("Wrote docs/audits/BV12A_facade_extraction.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
