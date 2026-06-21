#!/usr/bin/env python3
"""Generate BV12 smoke bridge audit markdown from artifacts/bv12_smoke_bridge_analysis.json."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv12_smoke_bridge_analysis.json"
AUDITS = ROOT / "docs" / "audits"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def load() -> dict[str, Any]:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def normalize_symbol(sym: str) -> str:
    base = sym.split(" as ")[0].split(" (")[0].strip()
    alias_map = {"read_final_emission_meta_dict": "final_emission_meta_from_output", "_gm_response": "gm_response_stub"}
    return alias_map.get(base, base)


def effective_symbol_fi(data: dict[str, Any]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for mod, pairs in data["symbol_fi_counts"].items():
        counts: Counter[str] = Counter()
        for sym, count in pairs:
            counts[normalize_symbol(sym)] += count
        out[mod] = dict(counts.most_common())
    return out


def subsystem_summary(importers: list[dict[str, Any]]) -> list[list[Any]]:
    by_sub: dict[str, set[str]] = defaultdict(set)
    sym_count: Counter[str] = Counter()
    for imp in importers:
        by_sub[imp["subsystem"]].add(imp["file"])
        for sym in imp["symbols"]:
            sym_count[normalize_symbol(sym)] += 1
    rows = []
    for sub, files in sorted(by_sub.items(), key=lambda x: -len(x[1])):
        top_sym = sym_count.most_common(1)[0][0] if sym_count else "—"
        rows.append([sub, len(files), top_sym])
    return rows


def write_dependency_inventory(data: dict[str, Any]) -> None:
    lines = [
        "# BV12 — Smoke Bridge Dependency Inventory",
        "",
        "**Date:** 2026-06-21  ",
        "**Scope:** Analysis only — every direct importer of `replay_smoke_assertions` and `gate_integration_smoke`  ",
        "**Method:** `python tools/bv12_smoke_bridge_discovery.py` + BU CSV reconciliation  ",
        "",
        "---",
        "",
        "## Hub baseline (current)",
        "",
        md_table(
            ["Module", "BU fan-in", "AST direct importers", "Public exports", "LOC"],
            [
                [
                    "`tests.helpers.replay_smoke_assertions`",
                    data["bu_fan_in"]["tests.helpers.replay_smoke_assertions"],
                    len(data["direct_importers"]["tests.helpers.replay_smoke_assertions"]),
                    len(data["exports_by_module"]["tests.helpers.replay_smoke_assertions"]),
                    data["loc_by_module"]["tests.helpers.replay_smoke_assertions"],
                ],
                [
                    "`tests.helpers.gate_integration_smoke`",
                    data["bu_fan_in"]["tests.helpers.gate_integration_smoke"],
                    len(data["direct_importers"]["tests.helpers.gate_integration_smoke"]),
                    len(data["exports_by_module"]["tests.helpers.gate_integration_smoke"]),
                    data["loc_by_module"]["tests.helpers.gate_integration_smoke"],
                ],
                ["**Combined**", data["combined_fan_in"], "—", "4", "84"],
            ],
        ),
        "",
        "**BV11 context:** Combined FI **95** — largest addressable maintenance cluster post-BV10. "
        "`emission_smoke_assertions` barrel FI **15** (phrase/route smoke only; bridge symbols migrated direct in BV7A).",
        "",
        "## Importer overlap",
        "",
    ]
    replay_files = {i["file"] for i in data["direct_importers"]["tests.helpers.replay_smoke_assertions"]}
    gate_files = {i["file"] for i in data["direct_importers"]["tests.helpers.gate_integration_smoke"]}
    both = sorted(replay_files & gate_files)
    lines.extend(
        [
            md_table(
                ["Pattern", "Count"],
                [
                    ["Replay-only importers", len(replay_files - gate_files)],
                    ["Gate-only importers", len(gate_files - replay_files)],
                    ["Dual-bridge importers (both modules)", len(both)],
                ],
            ),
            "",
            "Dual-bridge coupling is **consumer-side** (25 suites run gate orchestration and FEM reads in the same file), "
            "plus **module-side** (`gate_integration_smoke` imports `final_emission_meta_from_output` from replay bridge).",
            "",
        ]
    )

    for mod, label in (
        ("tests.helpers.replay_smoke_assertions", "replay_smoke_assertions"),
        ("tests.helpers.gate_integration_smoke", "gate_integration_smoke"),
    ):
        importers = data["direct_importers"][mod]
        lines.extend(
            [
                f"## `{label}` — summary by subsystem",
                "",
                md_table(
                    ["Subsystem", "Importers", "Primary symbol"],
                    subsystem_summary(importers),
                ),
                "",
                f"## `{label}` — full importer table",
                "",
                md_table(
                    ["File", "Subsystem", "Symbols imported", "Ownership bucket"],
                    [
                        [i["file"], i["subsystem"], ", ".join(f"`{s}`" for s in i["symbols"]), i["ownership_bucket"]]
                        for i in sorted(importers, key=lambda x: x["file"])
                    ],
                ),
                "",
            ]
        )

    (AUDITS / "BV12_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_symbol_concentration(data: dict[str, Any]) -> None:
    eff = effective_symbol_fi(data)
    lines = [
        "# BV12 — Symbol Concentration Analysis",
        "",
        "**Date:** 2026-06-21  ",
        "**Method:** Per-symbol importer scan (aliases normalized to source export)  ",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "Both bridge modules are **already minimal** (2 exports each, <60 LOC). "
        "High module FI is **symbol concentration**, not helper sprawl: "
        "`final_emission_meta_from_output` (~55 effective FI) and "
        "`apply_final_emission_gate_consumer` (39 FI) dominate.",
        "",
        "## Symbol fan-in (effective, alias-normalized)",
        "",
        md_table(
            ["Module", "Symbol", "Effective FI", "Role"],
            [
                [
                    "replay_smoke_assertions",
                    "`final_emission_meta_from_output`",
                    eff["tests.helpers.replay_smoke_assertions"].get("final_emission_meta_from_output", 0),
                    "FEM read bridge (BV7A/BV10C)",
                ],
                [
                    "replay_smoke_assertions",
                    "`read_turn_debug_notes`",
                    eff["tests.helpers.replay_smoke_assertions"].get("read_turn_debug_notes", 0),
                    "Turn-packet debug notes (pipeline/HTTP)",
                ],
                [
                    "gate_integration_smoke",
                    "`apply_final_emission_gate_consumer`",
                    eff["tests.helpers.gate_integration_smoke"].get("apply_final_emission_gate_consumer", 0),
                    "Full gate orchestration via runtime",
                ],
                [
                    "gate_integration_smoke",
                    "`gm_response_stub`",
                    eff["tests.helpers.gate_integration_smoke"].get("gm_response_stub", 0),
                    "Fake GM HTTP fixture stub",
                ],
            ],
        ),
        "",
        "## Classification",
        "",
        md_table(
            ["Category", "Symbols", "Combined effective FI"],
            [
                ["Bridge symbols (cross-domain)", "final_emission_meta_from_output, apply_final_emission_gate_consumer", "~94"],
                ["Replay-only symbols", "read_turn_debug_notes", "3"],
                ["Gate-only symbols", "gm_response_stub", "2"],
                ["Internal coupling", "gate → replay (final_emission_meta_from_output)", "1 module edge"],
            ],
        ),
        "",
        "## Highest fan-in helpers (ranked)",
        "",
        md_table(
            ["Rank", "Symbol", "FI", "Risk"],
            [
                ["1", "final_emission_meta_from_output", eff["tests.helpers.replay_smoke_assertions"].get("final_emission_meta_from_output", 0), "high — post-BV10C routing hub"],
                ["2", "apply_final_emission_gate_consumer", eff["tests.helpers.gate_integration_smoke"].get("apply_final_emission_gate_consumer", 0), "high — gate orchestration choke point"],
                ["3", "read_turn_debug_notes", eff["tests.helpers.replay_smoke_assertions"].get("read_turn_debug_notes", 0), "low — narrow pipeline surface"],
                ["4", "gm_response_stub", eff["tests.helpers.gate_integration_smoke"].get("gm_response_stub", 0), "low — fixture-only"],
            ],
        ),
        "",
    ]
    (AUDITS / "BV12_symbol_concentration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_usage_classification(data: dict[str, Any]) -> None:
    domain_files: dict[str, set[str]] = defaultdict(set)
    for mod in data["targets"]:
        for imp in data["direct_importers"][mod] + data["barrel_importers"][mod]:
            for domain in imp["usage_domains"]:
                domain_files[domain].add(imp["file"])

    lines = [
        "# BV12 — Usage Classification",
        "",
        "**Date:** 2026-06-21  ",
        "**Method:** Heuristic domain tagging from file path + imported symbols  ",
        "",
        "---",
        "",
        "## Domain totals",
        "",
        md_table(
            ["Domain", "Consumer files (deduped)", "Primary symbols"],
            [
                ["replay acceptance", len(domain_files.get("replay acceptance", set())), "final_emission_meta_from_output"],
                ["gate orchestration", len(domain_files.get("gate orchestration", set())), "apply_final_emission_gate_consumer"],
                ["fallback testing", len(domain_files.get("fallback testing", set())), "both bridge symbols"],
                ["gate validation", len(domain_files.get("gate validation", set())), "apply_final_emission_gate_consumer"],
                ["observability testing", len(domain_files.get("observability testing", set())), "final_emission_meta_from_output"],
                ["replay projection", len(domain_files.get("replay projection", set())), "final_emission_meta_from_output"],
            ],
        ),
        "",
        "## Classification notes",
        "",
        "- **replay acceptance** — integration/regression suites asserting FEM wiring after gate output (largest bucket).",
        "- **gate orchestration** — suites that run full `finalize_player_facing_emission` via consumer helper.",
        "- **fallback testing** — opening/diegetic/fallback suites; frequently **dual-bridge** (gate + FEM read).",
        "- **gate validation** — owner-adjacent gate suites (`test_final_emission_gate_*`, boundary convergence).",
        "- **observability testing** — dead-turn / telemetry confidence reads.",
        "- **replay projection** — golden-replay-adjacent seams (small; most projection uses `golden_replay_projection`).",
        "",
        "## Sample consumers by domain",
        "",
    ]
    for domain in sorted(data["usage_domain_totals"], key=data["usage_domain_totals"].get, reverse=True):
        samples = sorted(domain_files.get(domain, set()))[:8]
        lines.append(f"### {domain}")
        lines.append("")
        for sample in samples:
            lines.append(f"- `{sample}`")
        if len(domain_files.get(domain, set())) > 8:
            lines.append(f"- … and {len(domain_files[domain]) - 8} more")
        lines.append("")

    (AUDITS / "BV12_usage_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_extraction_candidates(data: dict[str, Any]) -> None:
    eff = effective_symbol_fi(data)
    fem_fi = eff["tests.helpers.replay_smoke_assertions"].get("final_emission_meta_from_output", 0)
    notes_fi = eff["tests.helpers.replay_smoke_assertions"].get("read_turn_debug_notes", 0)
    gate_fi = eff["tests.helpers.gate_integration_smoke"].get("apply_final_emission_gate_consumer", 0)
    stub_fi = eff["tests.helpers.gate_integration_smoke"].get("gm_response_stub", 0)

    lines = [
        "# BV12 — Domain Extraction Candidates",
        "",
        "**Date:** 2026-06-21  ",
        "**Constraint:** Behavior-preserving; no production changes in discovery phase  ",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "Decomposition is **feasible** via domain-named thin facades (1–2 symbols each) that delegate to existing "
        "implementations. Modules are already minimal; work is **consumer rerouting** and **governance**, not logic extraction.",
        "",
        "## Candidate helper families",
        "",
        md_table(
            ["Candidate module", "Symbols", "Est. consumers", "Projected FI ↓", "Migration count", "Replay risk"],
            [
                [
                    "`replay_fem_read_smoke`",
                    "final_emission_meta_from_output",
                    "~45 (acceptance + observability)",
                    "−45 from replay_smoke",
                    "~45 import edits",
                    "low",
                ],
                [
                    "`replay_projection_smoke`",
                    "final_emission_meta_from_output (alias stable)",
                    "~8 (transcript/golden-adjacent)",
                    "−8 from replay_smoke",
                    "~8",
                    "low-medium",
                ],
                [
                    "`pipeline_debug_notes_smoke`",
                    "read_turn_debug_notes",
                    "3",
                    "−3 from replay_smoke",
                    "3",
                    "low",
                ],
                [
                    "`gate_orchestration_smoke`",
                    "apply_final_emission_gate_consumer",
                    "~30 (orchestration/integration)",
                    "−30 from gate_integration",
                    "~30",
                    "low-medium",
                ],
                [
                    "`gate_validation_smoke`",
                    "apply_final_emission_gate_consumer",
                    "~9 (gate owner suites)",
                    "−9 from gate_integration",
                    "~9",
                    "medium",
                ],
                [
                    "`gate_fixture_smoke`",
                    "gm_response_stub",
                    "2",
                    "−2 from gate_integration",
                    "2",
                    "low",
                ],
                [
                    "`fallback_bridge_smoke`",
                    "gate consumer + FEM read (dual re-export)",
                    "6 fallback dual-bridge suites",
                    "concentrates dual imports",
                    "6",
                    "low-medium",
                ],
            ],
        ),
        "",
        "## Phase-1 low-risk extractions (recommended first)",
        "",
        "1. **`pipeline_debug_notes_smoke`** — 3 consumers, zero gate overlap.",
        "2. **`gate_fixture_smoke`** — 2 consumers (`turn_pipeline_http_fixtures`, barrel re-export path).",
        "",
        "These remove **5 FI** from combined cluster with minimal replay surface.",
        "",
        "## Evidence anchors",
        "",
        md_table(
            ["Metric", "Value"],
            [
                ["final_emission_meta_from_output effective FI", fem_fi],
                ["read_turn_debug_notes FI", notes_fi],
                ["apply_final_emission_gate_consumer FI", gate_fi],
                ["gm_response_stub FI", stub_fi],
                ["Dual-bridge consumer files", "25"],
            ],
        ),
        "",
    ]
    (AUDITS / "BV12_extraction_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hub_analysis(data: dict[str, Any]) -> None:
    lines = [
        "# BV12 — Smoke Bridge Hub Analysis",
        "",
        "**Date:** 2026-06-21  ",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "Concentration is **intentional aggregation** (BV7A/BV7C design) with **secondary accidental coupling** "
        "from BV10C FEM routing and dual-bridge fallback suites. The bridges are not monolith regrowth — they are "
        "**thin, governed choke points** that accumulated consumer migrations.",
        "",
        "## Intentional aggregation (by design)",
        "",
        "| Mechanism | Evidence |",
        "|---|---|",
        "| BV7 retired smoke monolith (FI 73→15) | `test_bv7c_emission_smoke_assertions_concentration_locked` |",
        "| Named bridge facades for FEM read + gate integration | Module docstrings; ownership registry AL4/BV7A |",
        "| Downstream must not import `game.final_emission_gate` directly | AS2 registry routing |",
        "| BV10C FEM reads route through replay bridge | +10 FI on replay_smoke; observability facades for production |",
        "",
        "## Accidental / secondary coupling",
        "",
        "| Pattern | Impact |",
        "|---|---|",
        "| 25 suites import **both** bridges | Cross-domain edit churn when either bridge changes |",
        "| `gate_integration_smoke` → `replay_smoke_assertions` import edge | Gate module FI partially depends on replay module |",
        "| Alias imports (`as read_final_emission_meta_dict`) | Obscures symbol FI in static scans (12 alias sites) |",
        "| Post-BV10 traffic into FEM read bridge | Shifted authority-cluster cost to replay smoke (+10 FI) |",
        "",
        "## Verdict",
        "",
        "| Question | Answer |",
        "|---|---|",
        "| Is this monolith regrowth? | **No** — 4 exports total, 84 LOC combined |",
        "| Is concentration intentional? | **Yes** — BV7/BV10 governance pattern |",
        "| Is further decomposition warranted? | **Yes** — consumer graph is domain-heterogeneous (6 usage classes) |",
        "| Replay risk if decomposed carefully? | **Low-medium** — symbols are pure delegates; no assertion logic in bridges |",
        "",
        "## Fan-out (dependency tail)",
        "",
        md_table(
            ["Module", "Production fan-out"],
            [
                ["replay_smoke_assertions", ", ".join(f"`{m}`" for m in data["fan_out_by_module"]["tests.helpers.replay_smoke_assertions"] if m.startswith("game."))],
                ["gate_integration_smoke", ", ".join(f"`{m}`" for m in data["fan_out_by_module"]["tests.helpers.gate_integration_smoke"] if m.startswith("game."))],
            ],
        ),
        "",
    ]
    (AUDITS / "BV12_hub_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_plan(data: dict[str, Any]) -> None:
    lines = [
        "# BV12 — Smoke Bridge Decomposition Plan",
        "",
        "**Date:** 2026-06-21  ",
        "**Status:** Plan only — **no implementation**  ",
        "**Primary metric:** Combined smoke bridge FI (current **95**)  ",
        "**Constraint:** Behavior-preserving; BV7C monolith cap + BV10 read-cluster guards remain green  ",
        "",
        "---",
        "",
        "## Architecture target",
        "",
        "```mermaid",
        "flowchart TB",
        "  subgraph domain_facades [Domain facades]",
        "    FEM[\"replay_fem_read_smoke\"]",
        "    PROJ[\"replay_projection_smoke\"]",
        "    DEBUG[\"pipeline_debug_notes_smoke\"]",
        "    GORCH[\"gate_orchestration_smoke\"]",
        "    GVAL[\"gate_validation_smoke\"]",
        "    GFIX[\"gate_fixture_smoke\"]",
        "    FB[\"fallback_bridge_smoke\"]",
        "  end",
        "  subgraph legacy [Compatibility bridges]",
        "    REPLAY[\"replay_smoke_assertions\"]",
        "    GATE[\"gate_integration_smoke\"]",
        "  end",
        "  FEM --> META[\"game.final_emission_meta_read\"]",
        "  GORCH --> RUNTIME[\"game.final_emission_runtime\"]",
        "  GORCH --> FEM",
        "  REPLAY --> FEM",
        "  REPLAY --> DEBUG",
        "  GATE --> GORCH",
        "  GATE --> GFIX",
        "  FB --> GORCH",
        "  FB --> FEM",
        "  TESTS[\"~70 consumer suites\"] --> domain_facades",
        "  TESTS -.-> legacy",
        "```",
        "",
        "---",
        "",
        "## Phase 1 — Low-risk extraction (1 cycle)",
        "",
        "**FI target:** 95 → **~90** (relocate 5 low-FI symbols to named modules)",
        "",
        md_table(
            ["Step", "Action", "Verification"],
            [
                ["1.1", "Create `pipeline_debug_notes_smoke.py`; move `read_turn_debug_notes`", "turn_pipeline_shared + scene_transition_authority green"],
                ["1.2", "Create `gate_fixture_smoke.py`; move `gm_response_stub`", "turn_pipeline_http_fixtures green"],
                ["1.3", "Legacy bridges re-export moved symbols", "Zero consumer changes required initially"],
                ["1.4", "Register new modules in ownership registry", "Registry governance tests green"],
            ],
        ),
        "",
        "**Exit criteria:** New modules exist; combined bridge FI unchanged; symbol FI split measurable.",
        "",
        "## Phase 2 — Consumer migration (1–2 cycles)",
        "",
        "**FI target:** 95 → **~35–45** (−50 to −60 on legacy bridges)",
        "",
        md_table(
            ["Wave", "Consumers", "Target facade", "Expected Δ FI"],
            [
                ["2A", "~45 replay acceptance + observability", "replay_fem_read_smoke", "−45 replay"],
                ["2B", "~8 transcript/golden-adjacent", "replay_projection_smoke", "−8 replay"],
                ["2C", "~30 gate orchestration integration", "gate_orchestration_smoke", "−30 gate"],
                ["2D", "~9 gate validation owner suites", "gate_validation_smoke", "−9 gate"],
                ["2E", "6 fallback dual-bridge suites", "fallback_bridge_smoke", "consolidates dual imports"],
            ],
        ),
        "",
        "Migrate dual-bridge fallback suites **last** — they benefit most from `fallback_bridge_smoke` combined surface.",
        "",
        "**Exit criteria:** Legacy bridge FI ≤ **15** each; domain facades hold ≥80% of consumer imports.",
        "",
        "## Phase 3 — Governance lock (1 cycle)",
        "",
        md_table(
            ["Step", "Action"],
            [
                ["3.1", "Add `test_bv12_smoke_bridge_direct_import_guard_*` — new consumers must use domain facades"],
                ["3.2", "Cap legacy bridge FI (replay ≤12, gate ≤10) — delegate-only importers"],
                ["3.3", "Document domain routing in ownership registry quick reference"],
            ],
        ),
        "",
        "**Exit criteria:** CI guard prevents bridge FI regrowth; BV11 combined cluster FI ≤ **40**.",
        "",
    ]
    (AUDITS / "BV12_decomposition_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_projection(data: dict[str, Any]) -> None:
    current = data["combined_fan_in"]
    phase1 = current - 5
    phase2_low = 38
    phase2_high = 48

    lines = [
        "# BV12 — Decomposition Projection",
        "",
        "**Date:** 2026-06-21  ",
        "**Baseline:** BV11 smoke bridge combined FI **95**  ",
        "",
        "---",
        "",
        "## FI projection",
        "",
        md_table(
            ["Stage", "replay_smoke FI", "gate_integration FI", "Combined", "Δ vs current"],
            [
                ["Current (BV11)", "56", "39", "95", "—"],
                ["After Phase 1", "~53", "~37", str(phase1), "−5"],
                ["After Phase 2 (range)", "8–12", "6–10", f"{phase2_low}–{phase2_high}", "−47 to −57"],
                ["After Phase 3 (target)", "≤12", "≤10", "≤22 legacy + domain facades", "−73 net legacy"],
            ],
        ),
        "",
        "## Domain facade FI distribution (Phase 2 steady state, estimate)",
        "",
        md_table(
            ["Facade", "Projected FI", "Notes"],
            [
                ["replay_fem_read_smoke", "40–48", "Largest slice — acceptance + observability"],
                ["gate_orchestration_smoke", "22–28", "Integration gate runs"],
                ["fallback_bridge_smoke", "5–6", "Dual-bridge fallback suites"],
                ["replay_projection_smoke", "6–8", "Transcript/golden-adjacent"],
                ["gate_validation_smoke", "6–9", "Gate owner suites"],
                ["pipeline_debug_notes_smoke", "3", "Isolated in Phase 1"],
                ["gate_fixture_smoke", "2", "Isolated in Phase 1"],
            ],
        ),
        "",
        "## Replay risk assessment",
        "",
        "| Factor | Risk | Mitigation |",
        "|---|---|---|",
        "| Bridge symbols are pure delegates | **Low** | No assertion logic relocation |",
        "| Gate orchestration touches runtime | **Medium** | Migrate orchestration consumers in isolated wave |",
        "| Golden-replay projection boundary | **Low-medium** | Keep `golden_replay_projection` separate; projection facade is FEM-read only |",
        "| Fallback dual-bridge suites | **Medium** | Dedicated `fallback_bridge_smoke`; migrate last |",
        "",
        "## Scorecard impact (projected post-Phase 2)",
        "",
        md_table(
            ["Dimension", "Projected delta"],
            [
                ["Maintenance drag", "+0.5"],
                ["Operational simplicity", "+0.5"],
                ["Maintenance economics", "+0.5"],
                ["Ownership clarity", "+0.25"],
            ],
        ),
        "",
        "## Success criteria",
        "",
        "A **clear decomposition path exists**: Phase 1 is immediately actionable (5 migrations, low replay risk). "
        "Phase 2 reduces legacy bridge combined FI by **~50–60** while preserving BV7/BV10 governance intent.",
        "",
    ]
    (AUDITS / "BV12_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    data = load()
    AUDITS.mkdir(parents=True, exist_ok=True)
    write_dependency_inventory(data)
    write_symbol_concentration(data)
    write_usage_classification(data)
    write_extraction_candidates(data)
    write_hub_analysis(data)
    write_decomposition_plan(data)
    write_projection(data)
    for name in (
        "BV12_dependency_inventory.md",
        "BV12_symbol_concentration.md",
        "BV12_usage_classification.md",
        "BV12_extraction_candidates.md",
        "BV12_hub_analysis.md",
        "BV12_decomposition_plan.md",
        "BV12_projection.md",
    ):
        print(f"Wrote docs/audits/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
