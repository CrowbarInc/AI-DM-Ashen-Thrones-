"""Generate BV7 audit markdown from artifacts/bv7_smoke_analysis.json."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/bv7_smoke_analysis.json"
AUDITS = ROOT / "docs/audits"


def subsystem(file: str) -> str:
    if file.startswith("tools/"):
        return "tools/analysis"
    if file.startswith("tests/helpers/"):
        name = file.rsplit("/", 1)[-1]
        if "transcript" in name or "golden" in name:
            return "replay helpers"
        if "fallback" in name or "opening" in name:
            return "fallback helpers"
        if "strict_social" in name or "speaker" in name:
            return "speaker helpers"
        return "test helpers"
    if file.startswith("tests/"):
        name = file.rsplit("/", 1)[-1]
        if "fallback" in name or "opening" in name or "diegetic" in name:
            return "fallback"
        if "replay" in name or "golden" in name:
            return "replay"
        if "speaker" in name:
            return "speaker/social"
        if "ownership" in name:
            return "ownership governance"
        if "observational" in name or "telemetry" in name or "dead_turn" in name:
            return "observability/diagnostics"
        if "boundary" in name or "gate" in name or "final_emission" in name:
            return "final emission gate"
        if "pipeline" in name or "turn_packet" in name or "api_" in name:
            return "HTTP/pipeline integration"
        if name.startswith("bv"):
            return "BV audit suites"
        return "integration/regression"
    if file.startswith("game/"):
        return "production runtime"
    return "other"


def load_bu_fi() -> dict[str, int]:
    rows: dict[str, int] = {}
    path = AUDITS / "BU_import_fan_in_fan_out.csv"
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows[row["module"]] = int(row["fan_in_total"])
    return rows


def main() -> None:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    bu_fi = load_bu_fi()
    importers = data["importers"]
    for imp in importers:
        imp["subsystem"] = subsystem(imp["file"])

    bu_module_fi = bu_fi.get("tests.helpers.emission_smoke_assertions", data["module_fi"])

    # --- 1. Dependency inventory ---
    lines = [
        "# BV7 — `emission_smoke_assertions` Dependency Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Analysis only. Maps every direct importer of `tests.helpers.emission_smoke_assertions`.",
        "**Method:** AST + import-regex scan (`scripts/bv7_smoke_facade_discovery.py`); fan-in reconciled with `scripts/bu_final_emission_coupling_discovery.py`.",
        "",
        "## Hub baseline (current)",
        "",
        "| Metric | Value | Source |",
        "|---|---:|---|",
        f"| Fan-in (module, BU scan) | **{bu_module_fi}** | `docs/audits/BU_import_fan_in_fan_out.csv` |",
        f"| Fan-in (AST scan, incl. tools/lazy) | **{data['module_fi']}** | `artifacts/bv7_smoke_analysis.json` |",
        f"| Fan-in (tests) | **69** | BU scan breakdown |",
        f"| Fan-in (helpers) | **4** | BU scan breakdown |",
        f"| Fan-out (production modules) | **{data['module_fo']}** | facade lazy imports |",
        f"| Public exports | **{data['public_export_count']}** | `tests/helpers/emission_smoke_assertions.py` |",
        f"| Module LOC | **{data['loc']}** | same |",
        "",
        "**BV5 rank:** #1 ecosystem fan-in hub (73 FI); ~2.6× `final_emission_meta_read` (28 FI).",
        "",
        "## Importer summary by subsystem",
        "",
        "| Subsystem | Importers | Primary symbols |",
        "|---|---:|---|",
    ]
    sub_groups: dict[str, list] = defaultdict(list)
    for imp in importers:
        sub_groups[imp["subsystem"]].append(imp)
    sym_counter: Counter[str] = Counter()
    for imp in importers:
        for s in imp["symbols"]:
            sym_counter[s.split(" as ")[0].split(" (")[0]] += 1
    for sub, group in sorted(sub_groups.items(), key=lambda x: -len(x[1])):
        top = Counter()
        for g in group:
            for s in g["symbols"]:
                top[s.split(" as ")[0].split(" (")[0]] += 1
        primary = ", ".join(f"`{n}` ({c})" for n, c in top.most_common(3))
        lines.append(f"| {sub} | {len(group)} | {primary} |")

    lines += ["", "## Full importer table", "", "| File | Subsystem | Symbols imported | Ownership bucket |", "|---|---|---|---|"]
    for imp in sorted(importers, key=lambda x: x["file"]):
        syms = ", ".join(f"`{s}`" for s in imp["symbols"])
        lines.append(f"| `{imp['file']}` | {imp['subsystem']} | {syms} | {imp['ownership_bucket']} |")

    lines += [
        "",
        "## Top imported symbols (caller fan-in)",
        "",
        "| Symbol | Consumer files |",
        "|---|---:|",
    ]
    for sym, count in data["top_symbols"][:15]:
        lines.append(f"| `{sym}` | {count} |")

    lines += [
        "",
        "## Evidence",
        "",
        "| Source | Role |",
        "|---|---|",
        "| `artifacts/bv7_smoke_analysis.json` | Per-importer symbol extraction |",
        "| `docs/audits/BU_import_fan_in_fan_out.csv` | Official module fan-in |",
        "| `docs/audits/BU_caller_fan_in.csv` | Per-symbol caller fan-in |",
        "| `tests/helpers/emission_smoke_assertions.py` | Facade module doc + exports |",
    ]
    (AUDITS / "BV7_smoke_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- 2. Usage classification ---
    class_importers: dict[str, list[str]] = defaultdict(list)
    for imp in importers:
        for c in imp["usage_classes"]:
            class_importers[c].append(imp["file"])

    lines = [
        "# BV7 — Smoke Facade Usage Classification",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Group `emission_smoke_assertions` imports by assertion purpose.",
        "",
        "## Classification totals",
        "",
        "| Purpose | Importer count | Share of 73 | Dominant symbols |",
        "|---|---:|---:|---|",
    ]
    purpose_symbols = {
        "replay assertions": ["final_emission_meta_from_output", "read_turn_debug_notes", "assert_final_route_*"],
        "test helpers": ["apply_final_emission_gate_consumer", "response_type_contract", "gm_response_stub", "validate_*", "apply_*_layer"],
        "observability assertions": ["assert_response_type_*", "assert_no_boundary_*", "assert_continuity_*"],
        "fallback assertions": ["assert_*_smoke (phrase/hygiene)", "has_non_accept_final_route_smoke"],
        "attribution assertions": ["assert_open_social_solicitation_route", "assert_broadcast_open_call_*", "assert_open_call_*"],
        "ownership assertions": ["assert_emission_repair_evidence"],
        "speaker assertions": ["assert_social_grounding_smoke", "assert_dialogue_lock_*"],
    }
    for purpose, count in sorted(data["usage_class_totals"].items(), key=lambda x: -x[1]):
        share = round(100 * count / bu_module_fi, 1)
        dom = purpose_symbols.get(purpose, ["—"])[0]
        lines.append(f"| {purpose} | {count} | {share}% | {dom} |")

    lines += [
        "",
        "> Note: Importers may appear in multiple purpose buckets when they import symbols from more than one family.",
        "",
        "## By purpose",
        "",
    ]
    for purpose in sorted(class_importers.keys()):
        files = sorted(set(class_importers[purpose]))
        lines.append(f"### {purpose} ({len(files)} files)")
        lines.append("")
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")

    (AUDITS / "BV7_smoke_usage_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- 3. Assertion family map ---
    lines = [
        "# BV7 — Smoke Assertion Family Map",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Major assertion families exported by `emission_smoke_assertions`.",
        "",
        "| Family | Assertion count | Consumer count | Primary subsystem | Concentration |",
        "|---|---:|---:|---|---|",
    ]
    family_subsystem = {
        "FEM/read bridge": "replay / FEM projection",
        "Gate integration bridge": "integration / gate orchestration",
        "Consumer layer bridge (AC/RD/RT)": "final emission gate / boundary",
        "Route wiring smoke": "route / HTTP pipeline",
        "Phrase/hygiene smoke": "HTTP/pipeline integration",
        "Repair evidence smoke": "ownership / repair wiring",
        "Social/open-call smoke": "speaker / social routing",
        "Smoke phrase constants": "synthetic smoke / AC boundary",
    }
    for fam, stats in data["family_stats"].items():
        conc = "HIGH" if stats["consumer_count"] >= 15 else "MEDIUM" if stats["consumer_count"] >= 5 else "LOW"
        lines.append(
            f"| {fam} | {stats['assertion_count']} | {stats['consumer_count']} | "
            f"{family_subsystem.get(fam, 'mixed')} | {conc} |"
        )

    lines += ["", "## Family detail", ""]
    for fam, stats in data["family_stats"].items():
        lines.append(f"### {fam}")
        lines.append("")
        lines.append(f"- **Assertions ({stats['assertion_count']}):** " + ", ".join(f"`{m}`" for m in stats["members"]))
        lines.append(f"- **Consumers ({stats['consumer_count']}):**")
        for c in stats["consumers"]:
            lines.append(f"  - `{c}`")
        lines.append("")

    (AUDITS / "BV7_assertion_family_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- 4. Concentration report ---
    top_hubs = sorted(bu_fi.items(), key=lambda x: -x[1])[:8]
    lines = [
        "# BV7 — Smoke Facade Concentration Report",
        "",
        "**Date:** 2026-06-21",
        "**Primary metric:** Fan-in concentration",
        "",
        "## Executive answer",
        "",
        f"`tests.helpers.emission_smoke_assertions` remains the **largest ecosystem fan-in node** at **{bu_module_fi} FI** — "
        "unchanged through BV2–BV5 despite meta read-side redistribution. The facade is **partially intentional** "
        "(Cycle AL4/AS2 downstream smoke surface) but has **accidentally absorbed** BV2-scale read and gate-integration "
        "bridges, making it a cross-cutting maintenance hub beyond smoke-only scope.",
        "",
        "## Module-level fan-in (top hubs)",
        "",
        "| Rank | Module | FI | vs smoke |",
        "|---:|---|---:|---|",
    ]
    for i, (mod, fi) in enumerate(top_hubs, 1):
        if mod == "tests.helpers.emission_smoke_assertions":
            vs = "baseline"
        else:
            vs = f"{fi - bu_module_fi:+d} vs smoke"
        lines.append(f"| {i} | `{mod}` | **{fi}** | {vs} |")

    lines += [
        "",
        "## Smoke facade fan-out",
        "",
        "| Production dependency | Role |",
        "|---|---|",
        "| `game.final_emission_meta_read` | FEM + debug read delegate (BV2 read facade) |",
        "| `game.final_emission_runtime` | Gate orchestration via `apply_final_emission_gate_consumer` |",
        "| `game.final_emission_validators` | AC/RD validator seams |",
        "| `game.final_emission_repairs` | AC/RD layer seams |",
        "| `game.final_emission_response_type` | Response-type enforcement seam |",
        "",
        "**Fan-out:** 5 production modules (+ typing/stdlib). Narrow FO vs FI — classic **hub-and-spoke test delegate** shape.",
        "",
        "## Symbol-level ownership concentration",
        "",
        "| Symbol | FI | % of module FI | Owner intent |",
        "|---|---:|---:|---|",
        f"| `final_emission_meta_from_output` | 42 | 58% | FEM read bridge (BV2 read-side spillover) |",
        f"| `apply_final_emission_gate_consumer` | 37 | 51% | Gate integration bridge (AS2 consumer seam) |",
        f"| `response_type_contract` | 14 | 19% | Test scaffold helper |",
        "",
        "Top-3 symbols account for **~93 symbol-imports** across **~55 unique files** (heavy overlap: gate + FEM co-import).",
        "",
        "## Legitimate aggregation vs accidental hub",
        "",
        "| Signal | Legitimate facade | Accidental hub |",
        "|---|---|---|",
        "| Documented AS2/AL4 downstream smoke charter | ✓ | |",
        "| BE6 triple-layer phrase split enforced in registry | ✓ | |",
        "| 58% FI on FEM read re-export (duplicates `final_emission_meta_read` test path) | | ✓ |",
        "| 51% FI on full gate orchestration wrapper | | ✓ (belongs beside `strict_social_harness`) |",
        "| AC/RD/RT layer bridges (18 consumers) parallel `repairs_consumer_facade` | | ✓ |",
        "| BV2–BV5 added +3 net importers while meta FI fell −64% | | ✓ (concentration persisted) |",
        "",
        "**Verdict:** **Hybrid** — smoke phrase/route families are legitimate; **read + gate + consumer bridges** create accidental maintenance drag.",
        "",
        "## Evidence",
        "",
        "| Source | Role |",
        "|---|---|",
        "| [BV5_hub_comparison.md](BV5_hub_comparison.md) | Pre-BV7 hub baseline |",
        "| [BV2C_fan_in_closeout.md](BV2C_fan_in_closeout.md) | Meta FI reduction contrast |",
        "| `tests/test_ownership_registry.py` | BE6 / BJ-4 facade governance locks |",
    ]
    (AUDITS / "BV7_concentration_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- 5. Decomposition candidates ---
    candidates = [
        ("replay_smoke_assertions", "FEM/read bridge", ["final_emission_meta_from_output", "read_turn_debug_notes"], 42, 2, "Low", "Extract to `tests/helpers/replay_smoke_assertions.py`; re-export from thin facade during migration."),
        ("gate_integration_smoke", "Gate integration bridge", ["apply_final_emission_gate_consumer", "gm_response_stub"], 37, 3, "Medium", "Co-locate with `strict_social_harness` / runtime seam docs; shrink gate-consumer FI on monolith."),
        ("consumer_layer_smoke", "Consumer layer bridge (AC/RD/RT)", ["response_type_contract", "validate_answer_completeness", "apply_*_layer", "enforce_response_type_contract_layer", "assert_response_delta_*"], 18, 4, "Medium", "Merge with or alias `repairs_consumer_facade`; registry already splits AC/RD owners."),
        ("route_smoke_assertions", "Route wiring smoke", ["assert_final_route_*", "has_non_accept_final_route_smoke", "assert_dialogue_lock_*"], 8, 2, "Low", "Pure smoke; aligns with AL3 route wiring charter."),
        ("fallback_smoke_assertions", "Phrase/hygiene smoke", ["assert_*_smoke phrase helpers", "SMOKE_*_PHRASES"], 4, 2, "Low", "Preserve BE6 layer-2 separation from sanitizer owner."),
        ("speaker_smoke_assertions", "Social/open-call smoke", ["assert_social_grounding_smoke", "assert_open_*", "assert_broadcast_*"], 4, 2, "Low", "Isolate social routing smoke from FEM/gate bridges."),
        ("attribution_smoke_assertions", "Open-call / broadcast routing", ["assert_open_social_solicitation_route", "assert_broadcast_open_call_*"], 2, 1, "Low", "Optional merge with speaker_smoke_assertions."),
    ]
    lines = [
        "# BV7 — Smoke Facade Decomposition Candidates",
        "",
        "**Date:** 2026-06-21",
        "**Goal:** Reduce module FI while preserving BE6 triple-layer smoke boundaries.",
        "",
        "## Candidate ranking (by projected FI relief)",
        "",
        "| Rank | Module candidate | Source family | Current consumer FI | Migration cost | Risk | Projected module FI after split |",
        "|---:|---|---|---:|---|---|---:|",
    ]
    for i, (name, fam, members, fi, cost, risk, note) in enumerate(candidates, 1):
        after = max(bu_module_fi - fi, 12)
        lines.append(f"| {i} | `{name}.py` | {fam} | **~{fi}** | {cost}/5 | {risk} | **~{after}** (thin re-export) → **~12–18** (post-migration) |")

    lines += ["", "## Candidate detail", ""]
    for name, fam, members, fi, cost, risk, note in candidates:
        lines += [
            f"### `{name}.py`",
            "",
            f"- **Source family:** {fam}",
            f"- **Symbols:** {', '.join(f'`{m}`' for m in members)}",
            f"- **Projected FI reduction:** −{fi} on extracted surface (overlap-adjusted module FI drop **~{min(fi, bu_module_fi - 15)}**)",
            f"- **Migration cost:** {cost}/5",
            f"- **Risk:** {risk}",
            f"- **Notes:** {note}",
            "",
        ]

    lines += [
        "## Overlap adjustment",
        "",
        "Many files import **both** `final_emission_meta_from_output` and `apply_final_emission_gate_consumer`. "
        "Extracting both bridges yields **~45–52** unique consumer migrations, not 79 additive.",
        "",
        "**Highest-ROI pair:** `replay_smoke_assertions` + `gate_integration_smoke` (−~55 unique files, module FI → **~15–20** with re-exports).",
    ]
    (AUDITS / "BV7_decomposition_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- 6. Migration plan ---
    lines = [
        "# BV7 — Smoke Facade Decomposition Plan",
        "",
        "**Date:** 2026-06-21",
        "**Status:** Plan only — **no implementation**",
        "**Constraint:** Behavior-preserving; registry locks (BE6, BJ-4, AL4) must remain green",
        "**Primary metric:** Module fan-in on `emission_smoke_assertions`",
        "",
        "## Objectives",
        "",
        f"1. Reduce monolith FI from **{bu_module_fi}** to **≤20** (post-migration target)",
        "2. Preserve intentional downstream smoke phrase/route ownership",
        "3. Relocate read and gate-integration bridges to named modules (mirror BV2 meta read split)",
        "4. Keep thin compatibility facade until consumer migration completes",
        "",
        "## Architecture target",
        "",
        "```mermaid",
        "flowchart TB",
        "  subgraph bridges [\"Extracted bridges\"]",
        "    REPLAY[\"replay_smoke_assertions\"]",
        "    GATE[\"gate_integration_smoke\"]",
        "    CONSUMER[\"consumer_layer_smoke\"]",
        "  end",
        "  subgraph smoke_core [\"Smoke core (remaining)\"]",
        "    ROUTE[\"route_smoke_assertions\"]",
        "    PHRASE[\"fallback_smoke_assertions\"]",
        "    SPEAKER[\"speaker_smoke_assertions\"]",
        "  end",
        "  FACADE[\"emission_smoke_assertions (thin re-export)\"]",
        "  REPLAY --> META_READ[\"final_emission_meta_read\"]",
        "  GATE --> RUNTIME[\"final_emission_runtime\"]",
        "  CONSUMER --> REPAIRS[\"validators / repairs / response_type\"]",
        "  FACADE --> REPLAY",
        "  FACADE --> GATE",
        "  FACADE --> CONSUMER",
        "  FACADE --> ROUTE",
        "  FACADE --> PHRASE",
        "  FACADE --> SPEAKER",
        "  TESTS[\"69 test importers\"] --> FACADE",
        "  TESTS -.-> REPLAY",
        "  TESTS -.-> GATE",
        "```",
        "",
        "---",
        "",
        "## Phase 1 — Low-risk extraction (1 cycle)",
        "",
        "**FI target:** 73 → **~73** (re-exports only); establishes module boundaries",
        "",
        "| Step | Action | Verification |",
        "|---|---|---|",
        "| 1.1 | Create `tests/helpers/replay_smoke_assertions.py`; move `final_emission_meta_from_output`, `read_turn_debug_notes` | `test_emission_smoke_assertions_contract.py` + transcript suites green |",
        "| 1.2 | Create `tests/helpers/gate_integration_smoke.py`; move `apply_final_emission_gate_consumer`, `gm_response_stub` | Gate orchestration order + strict_social_harness green |",
        "| 1.3 | Create `tests/helpers/route_smoke_assertions.py`, `fallback_smoke_assertions.py`, `speaker_smoke_assertions.py` for pure smoke helpers | BE6 registry lock + turn_pipeline_shared green |",
        "| 1.4 | Monolith re-exports all symbols (no consumer changes) | BU scan: FI unchanged; FO +3 helper modules |",
        "| 1.5 | Update `test_ownership_registry.py` AL4 quick reference paths | Registry governance tests green |",
        "",
        "**Exit criteria:** Zero test behavior change; new modules appear in ownership registry.",
        "",
        "---",
        "",
        "## Phase 2 — Consumer migration (1–2 cycles)",
        "",
        "**FI target:** 73 → **~18–22** (−51 to −55)",
        "",
        "| Wave | Consumers | Target import | Expected Δ FI |",
        "|---|---:|---|---:|",
        "| 2A | 42 FEM-read-only + transcript helpers | `replay_smoke_assertions` | −42 |",
        "| 2B | 37 gate-consumer suites + strict_social_harness | `gate_integration_smoke` | −37 |",
        "| 2C | 18 AC/RD/RT boundary suites | `consumer_layer_smoke` or `repairs_consumer_facade` | −18 |",
        "| 2D | 8 route + 4 phrase + 4 social smoke consumers | dedicated smoke modules | −12 |",
        "",
        "Migrate highest-overlap files first (`test_turn_pipeline_shared.py`, `test_anti_railroading.py`, boundary convergence suite).",
        "",
        "**Exit criteria:** ≤5 importers remain on monolith re-export; BU scan module FI ≤ **22**.",
        "",
        "---",
        "",
        "## Phase 3 — Facade governance (1 cycle)",
        "",
        "| Step | Action |",
        "|---|---|",
        "| 3.1 | Deprecation docstring on monolith re-exports; direct new imports required for new tests |",
        "| 3.2 | Registry lock: monolith must not grow public exports (existing BJ-4 test) |",
        "| 3.3 | Optional: collapse monolith to `__init__`-style re-export barrel or remove after FI ≤5 |",
        "| 3.4 | BU scan + BV scorecard refresh |",
        "",
        "**Exit criteria:** New tests cannot add monolith FI; smoke phrase edits touch ≤2 modules.",
        "",
        "## Verification gates",
        "",
        "```text",
        "python scripts/bu_final_emission_coupling_discovery.py",
        "pytest tests/test_emission_smoke_assertions_contract.py",
        "pytest tests/test_ownership_registry.py -k smoke",
        "pytest tests/test_turn_pipeline_shared.py",
        "pytest tests/test_final_emission_boundary_convergence.py",
        "```",
    ]
    plan_content = "\n".join(lines) + "\n"
    (AUDITS / "BV7_decomposition_plan.md").write_text(plan_content, encoding="utf-8")

    # --- 7. Verification projection ---
    lines = [
        "# BV7 — Smoke Facade Verification Projection",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Project fan-in and maintenance impact if BV7 decomposition executes.",
        "",
        "## Fan-in projection",
        "",
        "| Stage | `emission_smoke_assertions` FI | Ecosystem #1 hub | Notes |",
        "|---|---:|---|---|",
        f"| **Current (BV7 baseline)** | **{bu_module_fi}** | Yes (#1) | Unchanged since BV1C; +3 vs BV4 plan deferral |",
        "| Phase 1 (re-export split) | **73** | Yes | Boundary-only; FI unchanged expected |",
        "| Phase 2A (FEM read migration) | **~31** | Yes | −42 read-bridge consumers |",
        "| Phase 2A+2B (+ gate migration) | **~15–20** | Maybe | Overlap-adjusted; may fall to #2–#3 |",
        "| Phase 2 complete | **~12–18** | No | `final_emission_meta_read` (28) or `terminal_pipeline` (26) becomes #1 |",
        "| Phase 3 (governance) | **≤5** | No | Barrel or retired monolith |",
        "",
        "## Maintenance impact projection",
        "",
        "| Work type | Current blast radius | Post Phase 2 | Post Phase 3 |",
        "|---|---|---|---|",
        "| FEM read path change | 42 test files via smoke facade | 42 via `replay_smoke_assertions` only | Same, but decoupled from phrase smoke |",
        "| Gate orchestration seam change | 37 test files | 37 via `gate_integration_smoke` | Isolated from route/phrase edits |",
        "| Smoke phrase tuple edit | 4 files + monolith | 2 files (`fallback_smoke_assertions`) | Minimal |",
        "| Route smoke assertion edit | 8 files + monolith | 2 files (`route_smoke_assertions`) | Minimal |",
        "| New integration test default import | Adds to #1 hub (73 FI) | Targets specific bridge module | Governed |",
        "",
        "## Success criteria",
        "",
        "| Criterion | Current | Target | Met after |",
        "|---|---|---|---|",
        "| Module FI rank | #1 (73) | ≤#3 and ≤22 FI | Phase 2 |",
        "| Top symbol FI concentration | 58% on one symbol | ≤35% on any symbol | Phase 2A |",
        "| Smoke-only edit locality | Monolith + registry | ≤2 helper modules | Phase 3 |",
        "| BV scorecard hub warning | Active | Cleared | Phase 2 complete |",
        "",
        "## Recommendation",
        "",
        "**Pursue decomposition — high ROI.** BV2 proved read-side extraction reduces production blast radius; BV7 applies the same pattern to the **test-side mirror**. ",
        "",
        "**Highest-ROI strategy:** Phase 1+2A+2B first (`replay_smoke_assertions` + `gate_integration_smoke`) before pure smoke family splits. ",
        "Defer attribution-only split unless speaker/open-call suites grow.",
        "",
        "**Not worth deferring:** Continuing to add integration tests through the monolith (+3 FI since BV4) increases accidental-hub risk without production benefit.",
        "",
        "## Evidence",
        "",
        "| Source | Role |",
        "|---|---|",
        "| [BV7_concentration_report.md](BV7_concentration_report.md) | Hub vs legitimate facade verdict |",
        "| [BV7_decomposition_candidates.md](BV7_decomposition_candidates.md) | Extraction ROI ranking |",
        "| [BV5_follow_on_candidates.md](BV5_follow_on_candidates.md) | Prior deferral note (BV4 facade cycle) |",
        "| [BV2_meta_consolidation_plan.md](BV2_meta_consolidation_plan.md) | Successful read-facade precedent |",
    ]
    (AUDITS / "BV7_verification_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Generated BV7 audit docs in docs/audits/")

if __name__ == "__main__":
    main()
