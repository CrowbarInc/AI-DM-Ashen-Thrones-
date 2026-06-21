#!/usr/bin/env python3
"""BV16 — generate audit markdown from terminal pipeline discovery artifact."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv16_final_emission_terminal_pipeline_analysis.json"
AUDITS = ROOT / "docs" / "audits"


def load() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def sym_join(symbols: list[str]) -> str:
    return ", ".join(f"`{s}`" for s in symbols) if symbols else "—"


def attr_join(attrs: list[str]) -> str:
    return ", ".join(f"`{a}`" for a in attrs) if attrs else "—"


def write_dependency_inventory(data: dict) -> None:
    ast_n = data["ast_direct_importers"]
    prod_pct = 100 * data["production_importers"] // ast_n if ast_n else 0
    test_pct = 100 * data["test_importers"] // ast_n if ast_n else 0
    lines = [
        "# BV16 — Final Emission Terminal Pipeline Dependency Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Analysis only — every direct importer of `game.final_emission_terminal_pipeline`",
        "**Method:** `python tools/bv16_final_emission_terminal_pipeline_discovery.py` + BU CSV reconciliation",
        "",
        "---",
        "",
        "## Hub baseline (current)",
        "",
        "| Module | BU fan-in | AST direct importers | Defined exports | Namespace imports | LOC | Fan-out |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        f"| `game.final_emission_terminal_pipeline` | **{data['bu_fan_in']}** | {ast_n} | {data['defined_export_count']} | {data['reexport_count']} | {data['loc']} | {data['fan_out_count']} |",
        "",
        "**BV15 context:** `final_emission_gate` classified as **legitimate orchestration authority** (FI **30**, governance-inflated). "
        "Terminal pipeline is the paired **finalize-tail** target at FI **26**.",
        "",
        f"**Module shape:** **{data['loc']} LOC** with **{data['defined_export_count']} defined symbols** "
        f"(`run_gate_terminal_enforcement_pipeline`, `apply_strict_social_emergency_fallback_patch`, profile type, 2 private helpers) "
        f"and **{data['reexport_count']} imported symbols** bound at module scope (visibility, N4, IC, opening, repairs, meta).",
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
        "| Subsystem | Importers | Primary symbols / attrs |",
        "| --- | --- | --- |",
    ]
    by_sub: dict[str, list] = defaultdict(list)
    for imp in data["importers"]:
        by_sub[imp["subsystem"]].append(imp)
    for sub, imps in sorted(by_sub.items(), key=lambda x: -len(x[1])):
        sym_counts: dict[str, int] = defaultdict(int)
        for imp in imps:
            for s in imp["symbols"]:
                sym_counts[s] += 1
            for a in imp["attribute_uses"]:
                sym_counts[a] += 1
        top = max(sym_counts, key=sym_counts.get) if sym_counts else "—"
        lines.append(f"| {sub} | {len(imps)} | `{top}` |")

    lines.extend(
        [
            "",
            "## Full importer table",
            "",
            "| File | Subsystem | Imported symbols | Attribute uses | Ownership bucket |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for imp in data["importers"]:
        lines.append(
            f"| `{imp['file']}` | {imp['subsystem']} | {sym_join(imp['symbols'])} | {attr_join(imp['attribute_uses'])} | {imp['ownership_bucket']} |"
        )
    (AUDITS / "BV16_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_symbol_concentration(data: dict) -> None:
    meta = data["symbol_meta"]
    ranked = sorted(
        [
            (sym, m["fan_in_ast"], m["fan_in_bu"], m["category"], m["authority_class"])
            for sym, m in meta.items()
            if m["fan_in_ast"] > 0
        ],
        key=lambda x: (-x[1], -x[2], x[0]),
    )
    pipe_fi = meta.get("run_gate_terminal_enforcement_pipeline", {}).get("fan_in_bu", 0)
    pipe_ast = meta.get("run_gate_terminal_enforcement_pipeline", {}).get("fan_in_ast", 0)
    vis_ast = meta.get("apply_visibility_enforcement", {}).get("fan_in_ast", 0)
    mod_fi = data["bu_fan_in"]
    pipe_pct = 100 * pipe_fi // mod_fi if mod_fi else 0

    lines = [
        "# BV16 — Symbol Concentration Analysis",
        "",
        "**Date:** 2026-06-21",
        "**Method:** Per-symbol AST importer + attribute-use scan (`artifacts/bv16_final_emission_terminal_pipeline_analysis.json`)",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        f"Module BU FI **{mod_fi}** is **test-monkeypatch inflated** — canonical `run_gate_terminal_enforcement_pipeline` has BU FI **{pipe_fi} ({pipe_pct}%)** "
        f"with AST FI **{pipe_ast}** (2 production exit owners + governance source scans). "
        f"**Highest AST concentration** is `apply_visibility_enforcement` namespace binding at **{vis_ast} files** — tests patch visibility via terminal namespace, not owner module. "
        "The module is a **sequencer** that delegates behavior to extracted owners; FI reflects **monkeypatch seam concentration**, not heterogeneous utility accretion in production.",
        "",
        "## Symbol fan-in (ranked, AST + BU)",
        "",
        "| Rank | Symbol | AST FI | BU FI | Category | Authority class |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for rank, (sym, ast_fi, bu_fi, cat, auth) in enumerate(ranked[:20], 1):
        lines.append(f"| {rank} | `{sym}` | **{ast_fi}** | {bu_fi} | {cat} | {auth} |")

    buckets = {
        "finalize": [],
        "visibility": [],
        "N4": [],
        "opening": [],
        "IC": [],
        "realization": [],
        "compatibility": [],
        "module-import": [],
    }
    for sym, m in meta.items():
        cat = m["category"]
        if m["fan_in_ast"] > 0 and cat in buckets:
            buckets[cat].append((sym, m["fan_in_ast"], m["fan_in_bu"]))

    lines.extend(
        [
            "",
            "## Classification buckets",
            "",
            "| Category | Symbols with external use | Top symbol | AST FI | Role |",
            "| --- | --- | --- | --- | --- |",
            f"| **Finalize exports** | {len(buckets['finalize'])} | `run_gate_terminal_enforcement_pipeline` | **{pipe_ast}** | Canonical late-gate enforcement sequencer — accept/replace tail |",
            f"| **Visibility exports** | {len(buckets['visibility'])} | `apply_visibility_enforcement` | **{vis_ast}** | Owner delegate — monkeypatched via terminal namespace in tests |",
            f"| **N4 exports** | {len(buckets['N4'])} | `apply_acceptance_quality_n4_floor_seam` | {buckets['N4'][0][1] if buckets['N4'] else 0} | Acceptance-quality floor seam delegate |",
            f"| **IC exports** | {len(buckets['IC'])} | `attach_interaction_continuity_validation` | {max((x[1] for x in buckets['IC']), default=0)} | Interaction continuity attach/step delegates |",
            f"| **Opening exports** | {len(buckets['opening'])} | `reassert_scene_opening_accepted_candidate` | {max((x[1] for x in buckets['opening']), default=0)} | Opening accept reassert (via `opening_fallback` alias) — source inspection only |",
            f"| **Realization exports** | {len(buckets['realization'])} | `apply_strict_social_emergency_fallback_patch` | {buckets['realization'][0][1] if buckets['realization'] else 0} | Strict-social emergency fallback patch helper |",
            f"| **Compatibility exports** | {len(buckets['compatibility'])} | `_apply_fallback_behavior_layer` | {max((x[1] for x in buckets['compatibility']), default=0)} | Repairs/meta/text imports — internal + monkeypatch only |",
        ]
    )

    mod_entries_ast = meta.get("terminal_pipeline", {}).get("fan_in_ast", 0)
    if mod_entries_ast:
        lines.append(
            f"| **Module import** | — | `terminal_pipeline (module)` | **{mod_entries_ast}** | Governance introspection, visibility noop hooks, orchestration-order tests |"
        )

    lines.extend(
        [
            "",
            "## Defined vs imported namespace surface",
            "",
            "| Kind | Count | Examples | External AST FI |",
            "| --- | --- | --- | --- |",
            f"| Defined | {data['defined_export_count']} | `run_gate_terminal_enforcement_pipeline`, `apply_strict_social_emergency_fallback_patch` | {pipe_ast + meta.get('apply_strict_social_emergency_fallback_patch', {}).get('fan_in_ast', 0) + meta.get('_apply_referent_clarity_pre_finalize', {}).get('fan_in_ast', 0)} |",
            f"| Imported (namespace-bound) | {data['reexport_count']} | `apply_visibility_enforcement`, `apply_acceptance_quality_n4_floor_seam`, IC attach/step | {vis_ast + max((m['fan_in_ast'] for s, m in meta.items() if m['category'] in ('N4', 'IC', 'compatibility')), default=0)} |",
            "",
            "## Highest fan-in exports (maintenance risk)",
            "",
            "| Rank | Symbol | AST FI | BU FI | Risk |",
            "| --- | --- | --- | --- | --- |",
            f"| 1 | `apply_visibility_enforcement` (namespace) | {vis_ast} | 0 | **Medium** — test monkeypatch seam; owner is `final_emission_visibility_fallback` |",
            f"| 2 | `run_gate_terminal_enforcement_pipeline` | {pipe_ast} | {pipe_fi} | **Low-medium** — legitimate authority; 2 production paths |",
            f"| 3 | module introspection | {mod_entries_ast} | — | **Medium** — governance + replay noop hooks |",
            f"| 4 | `_apply_referent_clarity_pre_finalize` | {meta.get('_apply_referent_clarity_pre_finalize', {}).get('fan_in_ast', 0)} | 0 | **Low** — defined helper; direct unit tests + probe harness |",
        ]
    )
    (AUDITS / "BV16_symbol_concentration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_usage_classification(data: dict) -> None:
    totals = data["usage_class_totals"]
    total_tags = sum(totals.values())
    lines = [
        "# BV16 — Usage Classification",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Consumer groups (BV16 taxonomy)",
        "",
        "| Usage class | Tag assignments | Share | Typical symbols / attrs |",
        "| --- | --- | --- | --- |",
    ]
    typical = {
        "finalize path": "`run_gate_terminal_enforcement_pipeline` via `strict_social_stack` / `generic_exit`",
        "visibility": "`terminal_pipeline.apply_visibility_enforcement` monkeypatch noop in layer tests",
        "N4": "`apply_acceptance_quality_n4_floor_seam` hook in selector snapshots + gate N4 tests",
        "IC": "`attach_interaction_continuity_validation`, `apply_interaction_continuity_emission_step` hooks",
        "opening": "source inspection of `opening_fallback.reassert_*` inside pipeline body",
        "realization": "`apply_strict_social_emergency_fallback_patch` direct import in sealed fallback tests",
        "replay": "transcript regressions with visibility noop + full gate path",
        "validators": "— (no direct validator imports from terminal pipeline)",
        "tests": "gate legality, boundary convergence, player-facing purity suites",
        "governance": "ownership registry BJ-73/74/75/76 direct-call assertions, gate_thin_boundary_locks",
    }
    for cls, count in sorted(totals.items(), key=lambda x: -x[1]):
        share = f"{100 * count // total_tags}%" if total_tags else "0%"
        lines.append(f"| **{cls}** | {count} | {share} | {typical.get(cls, '—')} |")

    lines.extend(
        [
            "",
            f"> **Note:** Importers may appear in multiple classes. Totals sum to **{total_tags}** tag assignments across **{data['ast_direct_importers']}** files.",
            "",
            "## Finalize path cluster",
            "",
            "**2 production modules** call `run_gate_terminal_enforcement_pipeline` directly:",
            "",
            "- `game/final_emission_strict_social_stack.py` — strict accept/replace exit (2 call sites)",
            "- `game/final_emission_generic_exit.py` — generic accept/replace exit (2 call sites)",
            "",
            "Gate does **not** import terminal pipeline; stacks mediate. This is the **canonical production finalize tail**.",
            "",
            "## Visibility cluster",
            "",
            f"**{totals.get('visibility', 0)}** files monkeypatch `terminal_pipeline.apply_visibility_enforcement` to noop or trace — "
            "layer-isolation pattern for anti-railroading, context separation, player-facing purity, prompt context, tone escalation, "
            "speaker contract, social exchange emission, narration transcript regressions, gate orchestration order, boundary convergence.",
            "",
            "Ownership tests (BJ-73) already assert terminal pipeline **calls visibility owner directly** in source — monkeypatch target is legacy convenience.",
            "",
            "## N4 cluster",
            "",
            "`test_final_emission_gate_selector_snapshots` and `test_final_emission_gate_n4` hook N4/IC via terminal namespace. "
            "BJ-74 ownership registry verifies direct call to `final_emission_acceptance_quality` owner.",
            "",
            "## IC cluster",
            "",
            "Fallback behavior gate tests hook IC emission step + fallback behavior layer via terminal namespace. "
            "`post_speaker_finalize_probe` wraps terminal-bound IC/visibility/N4 symbols for finalize stack divergence characterization.",
            "",
            "## Replay cluster",
            "",
            "Transcript regressions import terminal module for visibility noop only — replay sensitivity is **enforcement order + text mutations**, "
            "not terminal module identity.",
            "",
            "## Governance cluster",
            "",
            "`tests/test_ownership_registry.py`, `tests/helpers/gate_thin_boundary_locks.py`, "
            "`tests/test_final_emission_gate_delegator_regression.py` — BJ-42/69/73/74/75/76 boundary locks; "
            "verify terminal pipeline does not lazy-import gate namespace and calls extracted owners directly.",
            "",
            "## Ownership bucket cross-cut",
            "",
            "| Bucket | Importers |",
            "| --- | --- |",
        ]
    )
    for bucket, count in data["ownership_bucket_totals"].items():
        lines.append(f"| {bucket} | {count} |")
    (AUDITS / "BV16_usage_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_authority_analysis(data: dict) -> None:
    meta = data["symbol_meta"]
    vis_ast = meta.get("apply_visibility_enforcement", {}).get("fan_in_ast", 0)
    lines = [
        "# BV16 — Authority Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Module self-description vs reality",
        "",
        "Docstring claims: *late gate terminal enforcement pipeline (visibility through IC attach)*; "
        "*shared accept/replace exit tail*; visibility/N4 owned by extracted modules and **called directly here**.",
        "",
        f"**Reality matches intent.** The module is a **finalize sequencer** ({data['loc']} LOC, {data['defined_export_count']} defined functions) "
        f"that orders calls to **already-extracted owners** (visibility, N4, opening, IC, repairs, narrative-mode output). "
        f"BU FI **{data['bu_fan_in']}** is inflated by **{vis_ast} test files** patching imported symbols via terminal namespace — "
        "not by production utility sprawl (only **2** production importers).",
        "",
        "## Export classification",
        "",
        "| Export | Class | Verdict |",
        "| --- | --- | --- |",
        "| `run_gate_terminal_enforcement_pipeline` | canonical-finalize-authority | **Legitimate authority** — ordered late enforcement tail; BU FI 2 |",
        "| `apply_strict_social_emergency_fallback_patch` | realization-helper | **Legitimate helper** — strict-social emergency path; 1 test direct import |",
        "| `GateTerminalEnforcementProfile` | finalize | **Legitimate type** — profile routing for accept/replace paths |",
        "| `_apply_referent_clarity_pre_finalize` | internal-helper | **Legitimate internal** — pre-finalize referent clarity pass; 3 direct uses |",
        "| `apply_visibility_enforcement` | visibility-policy-delegate | **Delegate — accidental test bridge** — owner is `final_emission_visibility_fallback` |",
        "| `apply_acceptance_quality_n4_floor_seam` | N4-policy-delegate | **Delegate — accidental test bridge** — owner is `final_emission_acceptance_quality` |",
        "| `apply_interaction_continuity_emission_step`, `attach_interaction_continuity_validation` | IC-projection-delegate | **Delegate — accidental test bridge** — owner is `interaction_continuity` |",
        "| `opening_fallback` / `reassert_scene_opening_accepted_candidate` | opening-projection-delegate | **Delegate** — owner is `final_emission_opening_fallback`; generic_accept only |",
        "| Repairs/meta/text imports | accidental-bridge | **Internal composition** — should not be monkeypatch targets |",
        "",
        "## Canonical authority determination",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Is terminal pipeline a legitimate finalize authority? | **Yes** — single sequencer owns accept/replace enforcement order |",
        "| Is FI 26 justified by heterogeneous production utility? | **No** — 92% test; 2 production importers on canonical entry |",
        "| What is actually authoritative here? | **Enforcement sequencing** — visibility/N4/IC/opening/realization owned elsewhere |",
        f"| Accidental coupling surfaces? | **{data['reexport_count']} namespace-bound imports** — test monkeypatch seams, not production API |",
        "",
        "## Projection helpers vs accidental bridges",
        "",
        "| Pattern | Examples | Assessment |",
        "| --- | --- | --- |",
        "| Canonical finalize sequencer | `run_gate_terminal_enforcement_pipeline` | **Keep centralized** — this is the authority |",
        "| Owner delegation (in-body) | `apply_visibility_enforcement`, N4 floor seam, IC attach | **Correct** — direct calls to owners inside sequencer |",
        "| Namespace-bound imports | Same symbols exposed on module object | **Accidental bridges** — enable test monkeypatch via terminal namespace |",
        "| Emergency fallback patch | `apply_strict_social_emergency_fallback_patch` | **Realization helper** — could move to sealed_fallback owner; low FI |",
        "| Module introspection | `import terminal_pipeline as tp` in 20+ tests | **Governance + replay noop overhead** |",
    ]
    (AUDITS / "BV16_authority_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_finalize_boundary(data: dict) -> None:
    b = data["finalize_boundary"]
    lines = [
        "# BV16 — Finalize Boundary Review",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Coupling summary",
        "",
        "| Dimension | `final_emission_gate` | `final_emission_terminal_pipeline` | `final_emission_visibility_fallback` | `final_emission_opening_fallback` | `interaction_continuity` |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| BU fan-in | **{data['gate_bu_fan_in']}** | **{data['bu_fan_in']}** | (owner) | (owner) | (owner) |",
        f"| Production importers | 1 | **2** | direct from terminal | via terminal alias | direct from terminal |",
        f"| Fan-out | {b['gate_fan_out_count']} | **{b['terminal_fan_out_count']}** | {b['visibility_fan_out_count']} | {b['opening_fan_out_count']} | {b['ic_fan_out_count']} |",
        f"| Imports peer gate | gate → terminal: **{b['gate_imports_terminal']}** | terminal → gate: **{b['terminal_imports_gate']}** | — | — | — |",
        f"| Dual importers (gate + terminal) | **{b['dual_importer_count']}** test files | — | — | — | — |",
        "",
        "## Dependency direction",
        "",
        "```mermaid",
        "flowchart TB",
        "  GATE[\"final_emission_gate\"] --> SS[\"strict_social_stack\"]",
        "  GATE --> GE[\"generic_exit\"]",
        "  SS --> TP[\"terminal_pipeline.run_gate_terminal_enforcement_pipeline\"]",
        "  GE --> TP",
        "  TP --> VIS[\"visibility_fallback.apply_visibility_enforcement\"]",
        "  TP --> N4[\"acceptance_quality N4 floor seam\"]",
        "  TP --> OPEN[\"opening_fallback.reassert_scene_opening\"]",
        "  TP --> IC[\"interaction_continuity attach/step\"]",
        "  TP --> REP[\"repairs / narrative_mode_output / sealed_fallback\"]",
        "  SS --> FIN[\"final_emission_finalize\"]",
        "  GE --> FIN",
        "```",
        "",
        "**Direction:** Acyclic. Gate routes to stacks; stacks call terminal sequencer; terminal calls policy owners. "
        "No gate↔terminal import cycle. Opening/visibility/IC modules do **not** import terminal pipeline.",
        "",
        "## Terminal direct owner calls",
        "",
        "| Concern | Canonical owner | Terminal call site |",
        "| --- | --- | --- |",
        f"| Visibility enforcement | `{b['terminal_direct_calls']['visibility']}` | mid-pipeline, after referential clarity + passive scene |",
        f"| N4 floor seam | `{b['terminal_direct_calls']['n4']}` | post-NMO assessment, pre-IC attach |",
        f"| Opening accept reassert | `{b['terminal_direct_calls']['opening']}` | `generic_accept` profile only |",
        f"| IC validation step | `{b['terminal_direct_calls']['ic_step']}` | `strict_accept` validate-only path |",
        f"| IC attach | `{b['terminal_direct_calls']['ic_attach']}` | all profiles; preserve flag on strict_accept |",
        "",
        "## Shared gate / terminal dependency surface",
        "",
        f"**{b['shared_gate_terminal_count']}** shared fan-out modules:",
        "",
    ]
    for dep in b["shared_gate_terminal"]:
        lines.append(f"- `{dep}`")

    lines.extend(
        [
            "",
            "## Terminal-only dependencies (gate does not share)",
            "",
        ]
    )
    for dep in b["terminal_only_dependencies"][:18]:
        lines.append(f"- `{dep}`")
    if len(b["terminal_only_dependencies"]) > 18:
        lines.append(f"- … and {len(b['terminal_only_dependencies']) - 18} more")

    lines.extend(
        [
            "",
            "## Ownership boundaries",
            "",
            "| Concern | Owner | Terminal role | Peer role |",
            "| --- | --- | --- | --- |",
            "| Orchestration routing | `final_emission_gate` | none | selects stack path |",
            "| Layer stack execution | `strict_social_stack` / `generic_exit` | invoked by exit owners | calls terminal once per exit |",
            "| Visibility policy | `final_emission_visibility_fallback` | delegate call + ordered slot | standalone enforcement API |",
            "| N4 acceptance floor | `final_emission_acceptance_quality` | delegate call | also invoked from gate tests directly |",
            "| Opening accept persistence | `final_emission_opening_fallback` | delegate via module alias | also used from finalize/non_strict_stack |",
            "| IC contracts | `interaction_continuity` | step + attach in strict/generic paths | gate re-exports IC for compat (BV15 retire target) |",
            "| Final packaging | `final_emission_finalize` | none (downstream of terminal) | pop turn-packet after terminal returns |",
            "",
            "## Replay sensitivity",
            "",
            "| Change locus | Replay risk | Rationale |",
            "| --- | --- | --- |",
            "| Terminal enforcement **order** | **High** | Orchestration-order + selector snapshot tests pin step sequence |",
            "| Visibility/N4/opening **policy** changes | **High** | Text mutations + fallback selection — owner modules, not terminal splits |",
            "| Monkeypatch target migration (terminal → owner) | **Low** | Identity-preserving if hook points unchanged |",
            "| Extract terminal sub-sequencers | **High** | Would fragment single ordered tail; transcript regressions |",
            "",
            "## Dual importer files (gate + terminal)",
            "",
        ]
    )
    for rel in b["dual_importers"]:
        lines.append(f"- `{rel}`")
    (AUDITS / "BV16_finalize_boundary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_candidates(data: dict) -> None:
    meta = data["symbol_meta"]
    vis_ast = meta.get("apply_visibility_enforcement", {}).get("fan_in_ast", 0)
    lines = [
        "# BV16 — Decomposition Candidates",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Executive framing",
        "",
        "Unlike pre-BN gate monoliths, terminal pipeline is **already a thin sequencer** over extracted owners. "
        "BV16 decomposition targets are **monkeypatch seam retirement** and optional **helper relocation**, not tail extraction.",
        "",
        "## Candidate modules",
        "",
        "| Candidate | Extract / action | Est. FI absorbed | Consumers | Migration cost | Replay risk |",
        "| --- | --- | --- | --- | --- | --- |",
        "| **`terminal_visibility_policy`** | Extract visibility ordering wrapper | **0 BU** — owner exists | 0 production | **High** — splits sequencer | **High** |",
        "| **`terminal_opening_projection`** | Extract generic_accept opening reassert slice | **0 BU** | 0 production | **Medium** | **Medium** — opening accept debug |",
        "| **`terminal_ic_projection`** | Extract IC step/attach ordering | **0 BU** | 0 production | **High** | **High** — strict_accept IC path |",
        "| **`finalize_realization_adapter`** | Move `apply_strict_social_emergency_fallback_patch` to `sealed_fallback` | **−1 AST** | 1 test | **Low** | **Low-medium** — fallback stamping |",
        "| **Monkeypatch migration to owners** | Point tests at `visibility_fallback`, `acceptance_quality`, `interaction_continuity` | **−~20 AST module FI** | 20+ test files | **Medium** — wide test diff | **Low** — noop hooks preserved |",
        "| **Keep centralized sequencer** | No body split; document canonical entry only | **0** | 2 production | **None** | **None** |",
        "",
        "## Not recommended",
        "",
        "| Candidate | Reason |",
        "| --- | --- |",
        "| Split `run_gate_terminal_enforcement_pipeline` into profile-specific modules | Fragments **single enforcement order** — high replay risk |",
        "| Merge terminal into gate | Inverts BV15 boundary — gate must not own finalize tail |",
        "| Merge terminal into visibility/opening/IC owners | Each owner would need cross-concern ordering knowledge |",
        "| Full module elimination | Legitimate finalize sequencer — 2 production exit paths depend on it |",
        "",
        "## Projected FI reduction (module-level)",
        "",
        "| Stage | `final_emission_terminal_pipeline` BU FI | Notes |",
        "| --- | --- | --- |",
        f"| Current | **{data['bu_fan_in']}** | 2 production + 23 test + 1 helper |",
        "| After monkeypatch target migration | **~4–6** | BU may remain 26 until CSV refresh; AST drops sharply |",
        "| After emergency patch relocation | **~4–6** | −1 direct symbol import |",
        "| After BV16C governance cap | **≤6** | Production + ownership tests only |",
        "| After full tail extraction | **~2** | **Not recommended** — sequencer authority lost |",
        "",
        f"**Primary win is governance clarity**, not massive BU FI drop — **{vis_ast}** visibility monkeypatches dominate AST FI but not BU caller CSV.",
    ]
    (AUDITS / "BV16_decomposition_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hub_analysis(data: dict) -> None:
    meta = data["symbol_meta"]
    pipe_ast = meta.get("run_gate_terminal_enforcement_pipeline", {}).get("fan_in_ast", 0)
    vis_ast = meta.get("apply_visibility_enforcement", {}).get("fan_in_ast", 0)
    vis_share = 100 * vis_ast // (vis_ast + pipe_ast) if (vis_ast + pipe_ast) else 0
    mod_ast = meta.get("terminal_pipeline", {}).get("fan_in_ast", 0) + meta.get("tp", {}).get("fan_in_ast", 0)
    lines = [
        "# BV16 — Hub Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        f"`final_emission_terminal_pipeline` is a **legitimate finalize authority** with **residual test monkeypatch hub artifacts**, "
        f"not the next production-core maintenance monolith. FI **{data['bu_fan_in']}** overstates production coupling: "
        f"**{data['production_importers']}/{data['ast_direct_importers']} production importers**, "
        f"**{pipe_ast} AST** on canonical entry vs **{vis_ast} AST** on visibility namespace monkeypatch seam.",
        "",
        "## Classification matrix",
        "",
        "| Signal | Evidence | Implication |",
        "| --- | --- | --- |",
        f"| Single-symbol production dominance | `run_gate_terminal_enforcement_pipeline` BU FI 2 / module FI {data['bu_fan_in']} | **Finalize choke** — expected for tail sequencer |",
        f"| Production breadth | {data['production_importers']}/{data['ast_direct_importers']} production importers ({100 * data['production_importers'] // data['ast_direct_importers'] if data['ast_direct_importers'] else 0}%) | **Not** a production utility hub |",
        f"| LOC / defined surface | {data['loc']} LOC, {data['defined_export_count']} defined + {data['reexport_count']} namespace imports | Body is sequencer; imports bind test monkeypatch surface |",
        f"| Fan-out | {data['fan_out_count']} deps — visibility, N4, IC, opening, repairs | Outward coupling **appropriate** for ordered tail |",
        f"| Internal decomposition | Owners already extracted (BJ-73/74/75) | **Behavior split largely complete** — terminal owns order only |",
        f"| Test monkeypatch FI | visibility namespace AST {vis_ast}; module introspection AST {mod_ast} | Maintenance overhead — accidental bridge, not authority sprawl |",
        f"| Gate pairing | gate FI {data['gate_bu_fan_in']}, 0 direct gate→terminal import | Acyclic finalize boundary preserved post-BV15 |",
        "",
        "## Verdict",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Legitimate finalize authority? | **Yes** — `run_gate_terminal_enforcement_pipeline` is real, documented, production-used |",
        "| Mixed authority/utility? | **Mild** — namespace-bound owner imports for test hooks only |",
        "| Accidental hub? | **Partially** — visibility/IC/N4 monkeypatch namespace; not production sprawl |",
        "| Should it remain centralized? | **Yes for sequencing**; **no for monkeypatch namespace** — migrate hooks to owners |",
        "",
        "## Comparison to BV15 `final_emission_gate`",
        "",
        "| Dimension | BV15 final_emission_gate | BV16 terminal_pipeline |",
        "| --- | --- | --- |",
        "| Authority type | Upstream orchestration router | Downstream finalize sequencer |",
        f"| Top symbol share | 57% orchestration entry | **8% BU** on canonical entry; **{vis_share}% AST** on visibility noop |",
        f"| Production importers | 1/{data['gate_bu_fan_in']} FI context | **2/{data['bu_fan_in']}** |",
        "| Decomposition driver | Namespace re-export + governance FI | **Monkeypatch seam retirement** — not tail extraction |",
        "| Replay risk | Medium (order) | **High** (enforcement tail text + order) |",
        "",
        "## Comparison to pre-BV14 hubs",
        "",
        "Terminal pipeline is **not** analogous to pre-BV14 `social_exchange_emission` (3881 LOC monolith). "
        "It is a **351 LOC ordered delegate caller** — closer to post-BN gate than to a decomposition-primary hotspot.",
    ]
    (AUDITS / "BV16_hub_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_projection(data: dict) -> None:
    meta = data["symbol_meta"]
    vis_ast = meta.get("apply_visibility_enforcement", {}).get("fan_in_ast", 0)
    pipe_ast = meta.get("run_gate_terminal_enforcement_pipeline", {}).get("fan_in_ast", 0)
    vis_share = 100 * vis_ast // (vis_ast + pipe_ast) if (vis_ast + pipe_ast) else 0
    lines = [
        "# BV16 — Projection",
        "",
        "**Date:** 2026-06-21",
        f"**Baseline:** Post-BV15 — `final_emission_gate` FI **{data['gate_bu_fan_in']}**, `final_emission_terminal_pipeline` FI **{data['bu_fan_in']}**",
        "",
        "---",
        "",
        "## FI projection",
        "",
        "| Stage | `final_emission_gate` FI | `final_emission_terminal_pipeline` FI | Top production hotspot |",
        "| --- | --- | --- | --- |",
        f"| BV16 baseline | **{data['gate_bu_fan_in']}** | **{data['bu_fan_in']}** | terminal finalize tail |",
        "| After BV15 namespace cleanup (parallel) | ≤12 | 26 | terminal_pipeline |",
        "| After monkeypatch migration to owners | ≤12 | **~6–8** (AST); BU ~26 until remeasure | gate orchestration |",
        "| After emergency patch relocation | ≤12 | **~5–7** | formatting / fallback catalog |",
        "| After BV16C governance cap | ≤12 | **≤6** | next BU-ranked module |",
        "| After full tail extraction (not recommended) | ≤12 | ~2 | — |",
        "",
        "## BV16 executive recommendation",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Remain centralized finalize sequencer? | **Yes** — `run_gate_terminal_enforcement_pipeline` stays canonical |",
        "| Decompose terminal body (visibility/N4/IC/opening splits)? | **No** — owners already extracted; splitting sequencer fragments order |",
        f"| Decompose terminal namespace / monkeypatch surface? | **Yes** — migrate **{vis_ast}** visibility (+ IC/N4) test hooks from terminal namespace to owner modules |",
        "| Proceed to extraction phase (BV16A)? | **No** — governance cleanup only; optional helper relocation |",
        "",
        "## Should BV16 proceed to extraction?",
        "",
        "**No — governance cleanup only.** Evidence:",
        "",
        f"- Terminal is **legitimate finalize authority** — 2 production exit owners, single ordered entrypoint",
        f"- FI **{data['bu_fan_in']}** is **test-monkeypatch inflated** ({vis_ast} files patch `apply_visibility_enforcement` via terminal namespace)",
        "- BV15 gate work established acyclic gate→stack→terminal boundary — tail extraction would **invert** that separation incorrectly",
        "- BJ-73/74/75 ownership tests already verify direct owner calls — remaining work is **consumer migration**, not new modules",
        "",
        "## Success criteria (BV16 analysis)",
        "",
        "| Criterion | Status |",
        "| --- | --- |",
        "| Determine legitimate vs accidental hub | **Legitimate finalize sequencer** + accidental monkeypatch namespace |",
        f"| Measure fan-in concentration | **8% BU** on canonical entry; **{vis_share}% AST** on visibility noop seam |",
        "| Finalize boundary documented | Acyclic; 5 owner modules; 12 dual-import test files |",
        "| Decomposition recommendation | **Keep sequencer centralized**; migrate monkeypatches; **defer tail extraction** |",
        "",
        "## Replay risk assessment",
        "",
        "| Factor | Risk | Mitigation |",
        "| --- | --- | --- |",
        "| Terminal enforcement order changes | **High** | `test_final_emission_gate_orchestration_order`, selector snapshots, block equivalence |",
        "| Owner policy changes (visibility/N4/opening) | **High** | Owner-module test suites; terminal source-order governance tests |",
        "| Monkeypatch target migration | **Low** | Point hooks at same owner callables — identity-preserving |",
        "| Tail module extraction | **High** | **Avoid** — not in BV16 scope |",
    ]
    (AUDITS / "BV16_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    data = load()
    write_dependency_inventory(data)
    write_symbol_concentration(data)
    write_usage_classification(data)
    write_authority_analysis(data)
    write_finalize_boundary(data)
    write_decomposition_candidates(data)
    write_hub_analysis(data)
    write_projection(data)
    print("Wrote BV16 audit docs to docs/audits/BV16_*.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
