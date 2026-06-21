#!/usr/bin/env python3
"""BV15 — generate audit markdown from discovery artifact."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv15_final_emission_gate_analysis.json"
AUDITS = ROOT / "docs" / "audits"


def load() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def sym_join(symbols: list[str]) -> str:
    return ", ".join(f"`{s}`" for s in symbols)


def write_dependency_inventory(data: dict) -> None:
    ast_n = data["ast_direct_importers"]
    prod_pct = 100 * data["production_importers"] // ast_n if ast_n else 0
    test_pct = 100 * data["test_importers"] // ast_n if ast_n else 0
    lines = [
        "# BV15 — Final Emission Gate Dependency Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Analysis only — every direct importer of `game.final_emission_gate`",
        "**Method:** `python tools/bv15_final_emission_gate_discovery.py` + BU CSV reconciliation",
        "",
        "---",
        "",
        "## Hub baseline (current)",
        "",
        "| Module | BU fan-in | AST direct importers | Defined exports | Re-exports | LOC | Fan-out |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| `game.final_emission_gate` | **{data['bu_fan_in']}** | {ast_n} | {data['defined_export_count']} | {data['reexport_count']} | {data['loc']} | {data['fan_out_count']} |",
        "",
        "**BV14 context:** `social_exchange_emission` compat FI **52 → 12**; gate owner is now the highest remaining **production-core orchestration** concentration at FI **30**.",
        "",
        f"**Post-BN decomposition:** Module body is **{data['loc']} LOC** with a single defined orchestration entrypoint (`apply_final_emission_gate`); "
        f"{data['reexport_count']} stack/preflight symbols remain as **namespace re-exports** from extracted owners (BN1–BN11).",
        "",
        "## Importer split",
        "",
        "| Layer | Count | Share |",
        "| --- | --- | --- |",
        f"| Production (`game/`) | {data['production_importers']} | {prod_pct}% |",
        f"| Tests (`tests/`) | {data['test_importers']} | {test_pct}% |",
        "",
        "## Summary by subsystem",
        "",
        "| Subsystem | Importers | Primary symbols |",
        "| --- | --- | --- |",
    ]
    by_sub: dict[str, list] = defaultdict(list)
    for imp in data["importers"]:
        by_sub[imp["subsystem"]].append(imp)
    for sub, imps in sorted(by_sub.items(), key=lambda x: -len(x[1])):
        sym_counts: dict[str, int] = defaultdict(int)
        for imp in imps:
            for s in imp["symbols"]:
                sym_counts[s.split(" as ")[0].strip()] += 1
        top = max(sym_counts, key=sym_counts.get) if sym_counts else "—"
        lines.append(f"| {sub} | {len(imps)} | `{top}` |")

    lines.extend(
        [
            "",
            "## Full importer table",
            "",
            "| File | Subsystem | Symbols imported | Ownership bucket |",
            "| --- | --- | --- | --- |",
        ]
    )
    for imp in data["importers"]:
        lines.append(
            f"| `{imp['file']}` | {imp['subsystem']} | {sym_join(imp['symbols'])} | {imp['ownership_bucket']} |"
        )
    (AUDITS / "BV15_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_symbol_concentration(data: dict) -> None:
    meta = data["symbol_meta"]
    ranked = sorted(
        [(sym, m["fan_in_bu"], m["fan_in_ast"], m["category"], m["authority_class"]) for sym, m in meta.items()],
        key=lambda x: (-x[1], -x[2], x[0]),
    )
    orch_fi = meta.get("apply_final_emission_gate", {}).get("fan_in_bu", 0)
    mod_fi = data["bu_fan_in"]
    orch_pct = 100 * orch_fi // mod_fi if mod_fi else 0
    lines = [
        "# BV15 — Symbol Concentration Analysis",
        "",
        "**Date:** 2026-06-21",
        "**Method:** Per-symbol AST importer scan (`artifacts/bv15_final_emission_gate_analysis.json`)",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        f"Module FI **{mod_fi}** is **orchestration-dominant** — `apply_final_emission_gate` holds **{orch_fi} BU FI ({orch_pct}%)**. "
        f"Unlike pre-BN gate monoliths, the module defines **one** function; remaining namespace surface is **{data['reexport_count']} re-exports** "
        "from extracted stack owners (speaker contract, interaction continuity, strict/non-strict stacks, gate context). "
        "Secondary FI is **module-level introspection** (`import game.final_emission_gate as feg`) for governance, monkeypatch, and source inspection — not heterogeneous utility accretion.",
        "",
        "## Symbol fan-in (ranked, BU baseline)",
        "",
        "| Rank | Symbol | BU FI | AST FI | Category | Authority class |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    rank = 0
    for sym, bu, ast, cat, auth in ranked:
        if sym.endswith("(module)"):
            continue
        rank += 1
        lines.append(f"| {rank} | `{sym}` | **{bu}** | {ast} | {cat} | {auth} |")
        if rank >= 15:
            break

    buckets = {
        "orchestration": [],
        "gate-authority": [],
        "compatibility": [],
        "helper": [],
        "module-import": [],
    }
    for sym, m in meta.items():
        cat = m["category"]
        if cat in buckets:
            buckets[cat].append((sym, m["fan_in_bu"], m["fan_in_ast"]))

    lines.extend(
        [
            "",
            "## Classification buckets",
            "",
            "| Category | Re-export / defined count | Top symbol | AST FI | Role |",
            "| --- | --- | --- | --- | --- |",
            f"| **Orchestration exports** | 1 defined | `apply_final_emission_gate` | **{orch_fi}** | Canonical gate orchestration entry — routes strict-social vs non-strict stacks |",
        ]
    )
    compat_syms = [s for s in data["export_map"] if data["export_map"][s].startswith("re-export")]
    lines.append(
        f"| **Gate authority re-exports** | 6 | `run_strict_social_composition_trunk` | 0 external | Stack trunk delegates — namespace legacy only post-BN2 |"
    )
    lines.append(
        f"| **Compatibility re-exports** | 5 | `get_speaker_selection_contract` | 1 | Speaker/IC bridges — BJ-129 thin-boundary compat; no production imports |"
    )
    lines.append(
        "| **Helper re-exports** | 2 | `resolve_gate_preflight_pregate_text` | 0 | Internal preflight — imported into gate body only |"
    )
    mod_imp = next((m for s, m in meta.items() if s.endswith("(module)")), None)
    if mod_imp:
        lines.append(
            f"| **Module import** | — | `feg (module)` | **{mod_imp['fan_in_ast']}** | Governance introspection, monkeypatch seams, ownership registry source scans |"
        )

    lines.extend(
        [
            "",
            "## Namespace re-export inventory (non-orchestration)",
            "",
            "| Symbol | Origin module | External AST FI | Assessment |",
            "| --- | --- | --- | --- |",
        ]
    )
    for sym in sorted(compat_syms):
        if sym == "apply_final_emission_gate":
            continue
        origin = data["export_map"][sym].replace("re-export from ", "")
        ext_fi = meta.get(sym, {}).get("fan_in_ast", 0)
        assessment = "Retire re-export — import origin directly" if ext_fi == 0 else "Migrate consumers to origin"
        lines.append(f"| `{sym}` | `{origin}` | {ext_fi} | {assessment} |")

    lines.extend(
        [
            "",
            "## Highest fan-in exports (maintenance risk)",
            "",
            "| Rank | Symbol | BU FI | Risk |",
            "| --- | --- | --- | --- |",
            f"| 1 | `apply_final_emission_gate` | {orch_fi} | **Low-medium** — legitimate authority; 1 production path via `final_emission_runtime` |",
            f"| 2 | module introspection (`feg`) | {mod_imp['fan_in_ast'] if mod_imp else '—'} | **Medium** — test/governance coupling; not production sprawl |",
            "| 3 | `get_speaker_selection_contract` | 1 | **Low** — compat re-export; migrate to `speaker_contract_enforcement` |",
        ]
    )
    (AUDITS / "BV15_symbol_concentration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_usage_classification(data: dict) -> None:
    totals = data["usage_class_totals"]
    total_tags = sum(totals.values())
    lines = [
        "# BV15 — Usage Classification",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Consumer groups (BV15 taxonomy)",
        "",
        "| Usage class | Tag assignments | Share | Typical symbols |",
        "| --- | --- | --- | --- |",
    ]
    typical = {
        "gate orchestration": "`apply_final_emission_gate`, module introspection for layer-order tests",
        "terminal pipeline": "`final_emission_runtime` re-export seam to API turn path",
        "validators": "— (no direct validator imports from gate)",
        "replay": "gate orchestration smoke + transcript suites that exercise full gate path",
        "fallback": "fallback-behavior gate tests (indirect — gate invokes stacks, not fallback symbols)",
        "tests": "gate legality matrices, selector snapshots, block equivalence harnesses",
        "governance": "ownership registry BN locks, gate_thin_boundary_locks, delegator regression",
        "diagnostics": "architecture audit + validation layer audit fixture strings",
    }
    for cls, count in sorted(totals.items(), key=lambda x: -x[1]):
        share = f"{100 * count // total_tags}%" if total_tags else "0%"
        lines.append(f"| **{cls}** | {count} | {share} | {typical.get(cls, '—')} |")

    lines.extend(
        [
            "",
            f"> **Note:** Importers may appear in multiple classes. Totals sum to **{total_tags}** tag assignments across **{data['ast_direct_importers']}** files.",
            "",
            "## Gate orchestration cluster",
            "",
            "Primary production path: `api_turn_support` → `final_emission_runtime.finalize_player_facing_emission` → "
            "`apply_final_emission_gate`. Only **one** production module imports the gate directly.",
            "",
            "Test cluster (15+ files) imports `apply_final_emission_gate` for end-to-end gate legality, orchestration order, "
            "N4 acceptance-quality floor, opening fallback, and block equivalence (S/T/U).",
            "",
            "## Terminal pipeline cluster",
            "",
            "`game/final_emission_runtime.py` is the **runtime adapter** — sole production importer. "
            "Terminal enforcement (`final_emission_terminal_pipeline`) is invoked from stack exit owners, not from gate imports.",
            "",
            "## Module introspection cluster",
            "",
            f"**{data['symbol_meta'].get('feg', {}).get('fan_in_ast', 0) + data['symbol_meta'].get('feg_module', {}).get('fan_in_ast', 0)}** test modules use `import game.final_emission_gate as feg` for:",
            "",
            "- Governance identity checks (re-export identity === origin owner)",
            "- Source-text negative assertions (`feg._*` must not appear in stack owners)",
            "- Monkeypatch equivalence harnesses",
            "",
            "This FI is **governance overhead**, not accidental production utility sprawl.",
            "",
            "## Governance cluster",
            "",
            "`tests/test_ownership_registry.py`, `tests/helpers/gate_thin_boundary_locks.py`, "
            "`tests/test_final_emission_gate_delegator_regression.py` — BN1–BN11 boundary locks, BJ-129 thin-boundary enforcement.",
            "",
            "## Replay cluster",
            "",
            "Replay-sensitive tests import `apply_final_emission_gate` directly (not gate module introspection): "
            "`test_narration_transcript_regressions` exercises terminal path via stacks; gate FI here is **orchestration-order** not phrase-catalog.",
            "",
            "## Ownership bucket cross-cut",
            "",
            "| Bucket | Importers |",
            "| --- | --- |",
        ]
    )
    for bucket, count in data["ownership_bucket_totals"].items():
        lines.append(f"| {bucket} | {count} |")
    (AUDITS / "BV15_usage_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_authority_analysis(data: dict) -> None:
    lines = [
        "# BV15 — Authority Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Module self-description vs reality",
        "",
        "Docstring claims: *canonical orchestration owner for final player-facing emission*; "
        "*not the canonical owner for validators, repairs, text formatting, or response_type contracts*.",
        "",
        "**Reality matches intent post-BN decomposition.** The module body is a **thin orchestration router** (338 LOC, 1 defined function) "
        "that delegates to extracted stack owners (`strict_social_stack`, `non_strict_stack`, `generic_exit`, `gate_context`). "
        f"FI **{data['bu_fan_in']}** is inflated by **test/governance introspection** (module-level `feg` imports) rather than production utility accretion.",
        "",
        "## Export classification",
        "",
        "| Export | Class | Verdict |",
        "| --- | --- | --- |",
        "| `apply_final_emission_gate` | canonical-gate-authority | **Legitimate authority** — sole orchestration entry; BU FI 17 |",
        "| `run_strict_social_composition_trunk`, `run_non_strict_layer_stack`, `run_generic_*_exit` | orchestration-delegate | **Legitimate but stale namespace** — 0 external imports; re-export for BN2 monkeypatch retirement |",
        "| `initialize_gate_execution_context` | orchestration-delegate | Preflight context owner re-export — 0 external imports |",
        "| `get_speaker_selection_contract`, `validate_emitted_speaker_against_contract`, `detect_emitted_speaker_signature` | compatibility-bridge | **Retire** — import `speaker_contract_enforcement` / `emitted_speaker_signature` directly |",
        "| `apply_interaction_continuity_emission_step`, `attach_interaction_continuity_validation` | compatibility-bridge | **Retire** — import `interaction_continuity` directly; governance tests verify identity only |",
        "| `resolve_gate_preflight_pregate_text`, `apply_observe_passive_scene_concrete_beat_upstream_satisfier` | helper | Internal-only re-exports — remove from public namespace |",
        "",
        "## Canonical authority determination",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Is `final_emission_gate` a legitimate orchestration authority? | **Yes** — single entrypoint owns strict vs non-strict routing |",
        "| Is FI 30 justified by heterogeneous utility? | **No** — 97% test/governance; 1 production importer |",
        "| What is actually authoritative here? | Orchestration sequencing only — stacks/terminal/finalize own behavior |",
        f"| Accidental coupling surfaces? | **{data['reexport_count']} namespace re-exports** — legacy BN2 compat; 0–1 external consumer each |",
        "",
        "## Projection helpers vs accidental bridges",
        "",
        "| Pattern | Examples | Assessment |",
        "| --- | --- | --- |",
        "| Canonical orchestration | `apply_final_emission_gate` | **Keep centralized** — this is the authority |",
        "| Stack delegation | `run_*_stack`, `run_generic_*_exit` | Delegates already extracted — **remove re-exports** |",
        "| Speaker/IC compat | `get_speaker_selection_contract`, IC attach/step | **Compatibility bridges** — governance-verified identity; retire namespace |",
        "| Module introspection | `import feg` in 16 test files | **Governance coupling** — acceptable short-term; not production hub pressure |",
    ]
    (AUDITS / "BV15_authority_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_gate_terminal_boundary(data: dict) -> None:
    b = data["gate_terminal_boundary"]
    lines = [
        "# BV15 — Gate / Terminal Pipeline Boundary Review",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Coupling summary",
        "",
        "| Dimension | `final_emission_gate` | `final_emission_terminal_pipeline` |",
        "| --- | --- | --- |",
        f"| BU fan-in | **{data['bu_fan_in']}** | **{data['terminal_bu_fan_in']}** |",
        f"| Production importers | **{data['production_importers']}** | 2 (via stack exit owners) |",
        f"| Fan-out | {data['fan_out_count']} modules | {b['terminal_fan_out_count']} modules |",
        f"| Direct import of peer | gate → terminal: **{b['gate_imports_terminal']}** | terminal → gate: **{b['terminal_imports_gate']}** |",
        f"| Dual importers (same file imports both) | **{b['dual_importer_count']}** test files | — |",
        "",
        "## Dependency direction",
        "",
        "```mermaid",
        "flowchart TB",
        "  API[\"api_turn_support\"] --> RT[\"final_emission_runtime\"]",
        "  RT --> GATE[\"final_emission_gate.apply_final_emission_gate\"]",
        "  GATE --> CTX[\"gate_context / preflight\"]",
        "  GATE --> SS[\"strict_social_stack\"] --> TP[\"terminal_pipeline\"]",
        "  GATE --> NSS[\"non_strict_stack\"] --> TP",
        "  GATE --> GE[\"generic_exit\"] --> TP",
        "  TP --> FIN[\"final_emission_finalize\"]",
        "```",
        "",
        "**Direction:** Gate **orchestrates** stack selection; stacks/exit owners **call** terminal pipeline; "
        "gate does **not** import terminal pipeline. No circular dependency.",
        "",
        "## Shared dependency surface",
        "",
        f"**{b['shared_dependency_count']}** shared fan-out modules:",
        "",
    ]
    for dep in b["shared_dependencies"][:20]:
        lines.append(f"- `{dep}`")
    if len(b["shared_dependencies"]) > 20:
        lines.append(f"- … and {len(b['shared_dependencies']) - 20} more")

    lines.extend(
        [
            "",
            "## Gate-only dependencies",
            "",
        ]
    )
    for dep in b["gate_only_dependencies"]:
        lines.append(f"- `{dep}`")

    lines.extend(
        [
            "",
            "## Terminal-only dependencies",
            "",
        ]
    )
    for dep in b["terminal_only_dependencies"][:15]:
        lines.append(f"- `{dep}`")
    if len(b["terminal_only_dependencies"]) > 15:
        lines.append(f"- … and {len(b['terminal_only_dependencies']) - 15} more")

    lines.extend(
        [
            "",
            "## Ownership boundaries",
            "",
            "| Concern | Owner | Gate role | Terminal role |",
            "| --- | --- | --- | --- |",
            "| Orchestration routing | `final_emission_gate` | strict vs non-strict branch | none |",
            "| Preflight / turn packet | `gate_context` + BN preflight modules | initialize context | none |",
            "| Layer stack execution | `non_strict_stack` / `strict_social_stack` | delegate | none |",
            "| Late enforcement (visibility, N4, IC, opening) | `terminal_pipeline` | none | accept/replace tail |",
            "| Final packaging | `final_emission_finalize` | pop turn-packet cache at exit | invoked after terminal |",
            "",
            "## Replay sensitivity",
            "",
            "| Change locus | Replay risk | Rationale |",
            "| --- | --- | --- |",
            "| Gate orchestration order | **Medium** | Layer-order tests + transcript regressions pin sequencing |",
            "| Terminal enforcement patches | **High** | Visibility/N4/opening fallback text mutations |",
            "| Namespace re-export retirement | **Low** | Identity-preserving; no behavior change |",
            "",
            "## Dual importer files (gate + terminal)",
            "",
        ]
    )
    for rel in b["dual_importers"]:
        lines.append(f"- `{rel}`")
    (AUDITS / "BV15_gate_terminal_boundary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_candidates(data: dict) -> None:
    lines = [
        "# BV15 — Decomposition Candidates",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Executive framing",
        "",
        "Unlike BV13/BV14, the gate module is **already decomposed internally** (BN1–BN11). "
        "BV15 decomposition targets are **namespace cleanup** and **FI governance**, not stack extraction.",
        "",
        "## Candidate modules",
        "",
        "| Candidate | Extract / action | Est. FI absorbed | Consumers | Migration cost | Replay risk |",
        "| --- | --- | --- | --- | --- | --- |",
        "| **`final_emission_gate_policy`** | Move eligibility/routing predicates if any remain re-exported | **0** (already in gate_context/preflight) | preflight modules | **N/A** — already extracted | **Low** |",
        "| **`final_emission_gate_validation`** | Validator imports (none external today) | **0** | validators module | **N/A** | **Low** |",
        "| **`final_emission_gate_projection`** | FEM/replay owner strings referencing `game.final_emission_gate` | **0 import FI** | replay_projection, ownership_schema | **Low** — string owner migration | **Medium** — attribution labels |",
        "| **`terminal_gate_adapter`** | Consolidate `final_emission_runtime` + document API→gate seam | **1** production | api_turn_support | **Low** | **Low** |",
        f"| **Namespace re-export retirement** | Remove {data['reexport_count']} stack/compat re-exports from gate namespace | **−0 module FI** | governance tests update imports | **Low-medium** | **Low** |",
        f"| **Governance introspection migration** | Point `feg` tests at stack owners directly | **−{data['symbol_meta'].get('feg', {}).get('fan_in_ast', 0) + data['symbol_meta'].get('feg_module', {}).get('fan_in_ast', 0)} AST module FI** | {data['symbol_meta'].get('feg', {}).get('fan_in_ast', 0) + data['symbol_meta'].get('feg_module', {}).get('fan_in_ast', 0)} test modules | **Medium** — large test diff | **Low** |",
        "",
        "## Not recommended",
        "",
        "| Candidate | Reason |",
        "| --- | --- |",
        "| Split `apply_final_emission_gate` across modules | Would fracture orchestration authority — stacks already own behavior |",
        "| Merge gate into terminal_pipeline | Inverts dependency direction; gate must remain upstream router |",
        "| Full module elimination | Legitimate orchestration owner — API path depends on it |",
        "",
        "## Projected FI reduction (module-level)",
        "",
        "| Stage | `final_emission_gate` BU FI | Notes |",
        "| --- | --- | --- |",
        f"| Current | **{data['bu_fan_in']}** | 17 orchestration + 13 governance/introspection |",
        "| After re-export retirement | **~28–30** | BU FI unchanged — re-exports have 0 external imports |",
        "| After governance import migration | **~14–17** | Module-level `feg` imports eliminated; orchestration FI remains |",
        "| After BV15C governance cap | **≤12** | Orchestration + runtime adapter + ownership tests only |",
        "",
        "**Primary win is clarity**, not massive FI drop — gate is already thin post-BN.",
    ]
    (AUDITS / "BV15_decomposition_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hub_analysis(data: dict) -> None:
    orch_fi = data["symbol_meta"].get("apply_final_emission_gate", {}).get("fan_in_bu", 17)
    mod_fi = data["bu_fan_in"]
    lines = [
        "# BV15 — Hub Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "`final_emission_gate` is a **legitimate orchestration authority** with **residual namespace hub artifacts**, "
        "not an oversized gateway monolith. FI **30** overstates production coupling: **1/30 production importers**, "
        "**17/30** on the canonical entrypoint, remainder is test governance introspection.",
        "",
        "## Classification matrix",
        "",
        "| Signal | Evidence | Implication |",
        "| --- | --- | --- |",
        f"| Single-symbol dominance | `apply_final_emission_gate` BU FI {orch_fi} / module FI {mod_fi} ({100*orch_fi//mod_fi}%) | **Orchestration choke** — expected for authority module |",
        f"| Production breadth | {data['production_importers']}/{mod_fi} production importers (3%) | **Not** a production utility hub |",
        f"| LOC / defined surface | {data['loc']} LOC, 1 defined + {data['reexport_count']} re-exports | Body is thin; namespace still carries BN2 legacy |",
        f"| Fan-out | {data['fan_out_count']} deps — stacks, context, speaker compat | Outward coupling **appropriate** for orchestrator |",
        "| Internal decomposition | BN1–BN11 preflight + stack owners extracted | **Decomposition largely complete** |",
        f"| Governance FI | {data['symbol_meta'].get('feg', {}).get('fan_in_ast', 0) + data['symbol_meta'].get('feg_module', {}).get('fan_in_ast', 0)} module introspection imports | Maintenance overhead — not accidental production sprawl |",
        "| Terminal pairing | terminal_pipeline FI 26, 0 direct gate import | Natural **BV16** target for finalize coupling |",
        "",
        "## Verdict",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Legitimate authority module? | **Yes** — orchestration entry is real and documented |",
        "| Mixed authority/utility? | **Mild** — namespace re-exports only; no utility accretion in body |",
        "| Accidental hub? | **Partially** — re-export namespace + governance `feg` introspection |",
        "| Should it remain centralized? | **Yes for orchestration**; **no for re-exports** — retire compat namespace |",
        "",
        "## Comparison to BV14 `social_exchange_emission`",
        "",
        "| Dimension | BV14 social_exchange_emission | BV15 final_emission_gate |",
        "| --- | --- | --- |",
        "| Pre-work state | 3881 LOC monolith | **338 LOC** post-BN router |",
        "| Top symbol share | 19% (multi-concern) | **57%** orchestration entry |",
        "| Production importers | 27/52 (52%) | **1/30 (3%)** |",
        "| Decomposition driver | Extract fallback/policy/validation | **Namespace cleanup + governance FI cap** |",
        "| Replay risk | High (fallback catalog) | **Medium** (orchestration order) |",
        "",
        "## Comparison to `final_emission_terminal_pipeline`",
        "",
        "Terminal pipeline FI **26** with **heterogeneous finalize paths** (visibility, N4, opening, IC) is the **stronger decomposition candidate** for BV16. "
        "Gate FI is **governance-inflated**; terminal FI is **behavior-inflated**.",
    ]
    (AUDITS / "BV15_hub_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_projection(data: dict) -> None:
    lines = [
        "# BV15 — Projection",
        "",
        "**Date:** 2026-06-21",
        "**Baseline:** Post-BV14 — `final_emission_gate` FI **30**, `final_emission_terminal_pipeline` FI **26**",
        "",
        "---",
        "",
        "## FI projection",
        "",
        "| Stage | `final_emission_gate` FI | `final_emission_terminal_pipeline` FI | Top production hotspot |",
        "| --- | --- | --- | --- |",
        f"| BV15 baseline | **{data['bu_fan_in']}** | **{data['terminal_bu_fan_in']}** | gate orchestration owner |",
        "| After namespace re-export retirement | ~28–30 | 26 | unchanged BU (0 external re-export consumers) |",
        "| After governance `feg` migration | **~14–17** | 26 | terminal_pipeline |",
        "| After BV15C cap | **≤12** | 26 | terminal_pipeline **26** |",
        "| After BV16 terminal decomposition | ≤12 | **~8–12** | formatting hub / fallback catalog |",
        "",
        "## BV15 executive recommendation",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Remain centralized orchestration? | **Yes** — `apply_final_emission_gate` stays canonical |",
        "| Decompose gate body further? | **No** — BN series already extracted stacks/preflight |",
        f"| Decompose gate namespace? | **Yes** — retire {data['reexport_count']} re-exports; cap governance FI |",
        "| Pair with terminal pipeline? | **Yes** — BV16 should target `final_emission_terminal_pipeline` |",
        "",
        "## Should terminal pipeline become BV16?",
        "",
        "**Yes.** Evidence:",
        "",
        "- Terminal FI **26** with **14 fan-out** and **23 test importers** — behavior-heavy finalize coupling",
        "- Gate→terminal direction is acyclic; terminal owns replay-sensitive enforcement patches",
        "- Gate BV15 work is primarily **governance + namespace**; terminal BV16 is **authority split** (visibility, N4, opening, IC tail)",
        "",
        "## Success criteria (BV15 analysis)",
        "",
        "| Criterion | Status |",
        "| --- | --- |",
        "| Determine legitimate vs accidental hub | **Legitimate orchestration** + accidental namespace/governance FI |",
        "| Measure fan-in concentration | **57%** on `apply_final_emission_gate`; module FI governance-inflated |",
        "| Gate/terminal boundary documented | Acyclic; stacks mediate; 12 dual-import test files |",
        "| Decomposition recommendation | **Keep orchestration centralized**; retire re-exports; **defer behavior split to BV16** |",
        "",
        "## Replay risk assessment",
        "",
        "| Factor | Risk | Mitigation |",
        "| --- | --- | --- |",
        "| Orchestration order changes | **Medium** | `test_final_emission_gate_orchestration_order` + block equivalence suites |",
        "| Re-export namespace retirement | **Low** | Identity-preserving; update governance imports only |",
        "| Terminal pipeline split (BV16) | **High** | Golden replay + visibility/N4 suites before migration |",
    ]
    (AUDITS / "BV15_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    data = load()
    write_dependency_inventory(data)
    write_symbol_concentration(data)
    write_usage_classification(data)
    write_authority_analysis(data)
    write_gate_terminal_boundary(data)
    write_decomposition_candidates(data)
    write_hub_analysis(data)
    write_projection(data)
    print("Wrote 8 BV15 audit documents to docs/audits/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
