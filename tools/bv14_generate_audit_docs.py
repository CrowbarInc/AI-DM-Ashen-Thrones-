#!/usr/bin/env python3
"""BV14 — generate audit markdown from discovery artifact."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv14_social_exchange_emission_analysis.json"
AUDITS = ROOT / "docs" / "audits"


def load() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def sym_join(symbols: list[str]) -> str:
    return ", ".join(f"`{s}`" for s in symbols)


def write_dependency_inventory(data: dict) -> None:
    lines = [
        "# BV14 — Social Exchange Emission Dependency Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Analysis only — every direct importer of `game.social_exchange_emission`",
        "**Method:** `python tools/bv14_social_exchange_emission_discovery.py` + BU CSV reconciliation",
        "",
        "---",
        "",
        "## Hub baseline (current)",
        "",
        "| Module | BU fan-in | AST direct importers | Public exports | LOC | Fan-out |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| `game.social_exchange_emission` | **{data['bu_fan_in']}** | {data['ast_direct_importers']} | {data['public_export_count']} | {data['loc']} | {data['fan_out_count']} |",
        "",
        "**BV13 context:** `final_emission_text` compat FI **52 → 5**; `social_exchange_emission` is now the highest-ranked remaining **production-core** concentration.",
        "",
        "## Importer split",
        "",
        "| Layer | Count | Share |",
        "| --- | --- | --- |",
        f"| Production (`game/`) | {data['production_importers']} | {100 * data['production_importers'] // data['ast_direct_importers']}% |",
        f"| Tests (`tests/`) | {data['test_importers']} | {100 * data['test_importers'] // data['ast_direct_importers']}% |",
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
    (AUDITS / "BV14_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_symbol_concentration(data: dict) -> None:
    meta = data["symbol_meta"]
    ranked = sorted(
        [(sym, m["fan_in_bu"], m["fan_in_ast"], m["category"], m["authority_class"]) for sym, m in meta.items()],
        key=lambda x: (-x[1], -x[2], x[0]),
    )
    lines = [
        "# BV14 — Symbol Concentration Analysis",
        "",
        "**Date:** 2026-06-21",
        "**Method:** Per-symbol AST importer scan (`artifacts/bv14_social_exchange_emission_analysis.json`)",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        f"Module FI **{data['bu_fan_in']}** is **multi-symbol** — unlike BV13's 90% `_normalize_text` choke. "
        "Top three symbols (`minimal_social_emergency_fallback_line`, `strict_social_emission_will_apply`, "
        "`build_final_strict_social_response`) account for **~29 BU FI** combined. "
        "The module bundles **composition**, **fallback**, **eligibility policy**, **telemetry**, and **private-helper leaks**.",
        "",
        "## Symbol fan-in (ranked, BU baseline)",
        "",
        "| Rank | Symbol | BU FI | AST FI | Category | Authority class |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, (sym, bu, ast, cat, auth) in enumerate(ranked[:25], 1):
        if sym.endswith("(module)"):
            continue
        lines.append(f"| {i} | `{sym}` | **{bu}** | {ast} | {cat} | {auth} |")

    buckets = {
        "composition": [],
        "projection": [],
        "validator": [],
        "fallback": [],
        "policy": [],
    }
    for sym, m in meta.items():
        if sym.endswith("(module)"):
            continue
        cat = m["category"]
        if cat in buckets:
            buckets[cat].append((sym, m["fan_in_bu"]))

    lines.extend(
        [
            "",
            "## Classification buckets",
            "",
            "| Category | Symbols (public) | Top symbol FI | Role |",
            "| --- | --- | --- | --- |",
        ]
    )
    role_map = {
        "composition": "Strict-social terminal response assembly + ownership filters",
        "projection": "FEM/realization family stamping + gate prompt merge + telemetry",
        "validator": "Route legality + sanitizer/global fallback rejection",
        "fallback": "Emergency/deterministic social fallback line selection",
        "policy": "Strict-social eligibility / will-apply predicates",
    }
    for cat, role in role_map.items():
        syms = sorted(buckets[cat], key=lambda x: -x[1])
        top_fi = syms[0][1] if syms else 0
        top_sym = syms[0][0] if syms else "—"
        count = len([s for s in data["public_exports"] if meta.get(s, {}).get("category") == cat])
        lines.append(f"| **{cat.title()} exports** | {count} | `{top_sym}` **{top_fi}** | {role} |")

    private_leaks = [sym for sym in meta if sym.startswith("_") and meta[sym]["fan_in_ast"] > 0]
    lines.extend(
        [
            "",
            "## Private symbol leaks (accidental export surface)",
            "",
            f"**{len(private_leaks)}** private helpers imported by external modules — violates encapsulation and inflates perceived hub authority:",
            "",
        ]
    )
    for sym in sorted(private_leaks, key=lambda s: -meta[s]["fan_in_ast"]):
        m = meta[sym]
        lines.append(f"- `{sym}` — AST FI **{m['fan_in_ast']}** ({', '.join(f'`{f}`' for f in m['importers'][:4])}{'…' if len(m['importers']) > 4 else ''})")

    lines.extend(
        [
            "",
            "## Highest fan-in exports (maintenance risk)",
            "",
            "| Rank | Symbol | BU FI | Risk |",
            "| --- | --- | --- | --- |",
            "| 1 | `minimal_social_emergency_fallback_line` | 10 | **High** — cross-cuts terminal pipeline, sanitizer, gm, visibility |",
            "| 2 | `strict_social_emission_will_apply` | 9 | **High** — API entry, preflight, sanitizer, policy enforcement |",
            "| 3 | `build_final_strict_social_response` | 8 | **Medium** — canonical composition; mostly stack + tests |",
            "| 4 | `effective_strict_social_resolution_for_emission` | 7 | **Medium** — resolution projection for gate/sanitizer |",
            "| 5 | `merged_player_prompt_for_gate` | 7 | **Medium** — gate preflight prompt merge (6 production) |",
        ]
    )
    (AUDITS / "BV14_symbol_concentration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_usage_classification(data: dict) -> None:
    totals = data["usage_class_totals"]
    total_tags = sum(totals.values())
    lines = [
        "# BV14 — Usage Classification",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Consumer groups (BV14 taxonomy)",
        "",
        "| Usage class | Tag assignments | Share | Typical symbols |",
        "| --- | --- | --- | --- |",
    ]
    typical = {
        "strict-social pipeline": "`build_final_strict_social_response`, `effective_strict_social_resolution_for_emission`",
        "terminal emission": "`minimal_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback`",
        "gate": "`strict_social_emission_will_apply`, `merged_player_prompt_for_gate`",
        "validators": "`is_route_illegal_global_or_sanitizer_fallback_text`, `replacement_is_route_legal_social`",
        "tests": "module monkeypatch + legality owner suite",
        "replay": "`build_final_strict_social_response` (transcript regressions)",
        "diagnostics": "ownership registry + gate delegator governance strings",
    }
    for cls, count in sorted(totals.items(), key=lambda x: -x[1]):
        share = f"{100 * count // total_tags}%"
        lines.append(f"| **{cls}** | {count} | {share} | {typical.get(cls, '—')} |")

    lines.extend(
        [
            "",
            f"> **Note:** Importers may appear in multiple classes. Totals sum to **{total_tags}** tag assignments across **{data['ast_direct_importers']}** files.",
            "",
            "## Strict-social pipeline cluster (23 tagged)",
            "",
            "Primary composition path: `final_emission_strict_social_stack` → `build_final_strict_social_response`. "
            "Upstream narrative modules consume `merged_player_prompt_for_gate` for gate-aligned player text.",
            "",
            "Representative: `final_emission_strict_social_stack`, `interaction_context`, `final_emission_*` policy modules, `gm_retry`.",
            "",
            "## Gate cluster (6 tagged)",
            "",
            "Preflight strict-social (`final_emission_gate_preflight_strict_social`), API turn routing (`api`, `api_turn_support`), "
            "sanitizer boundary (`output_sanitizer`), anti-reset guard.",
            "",
            "**Dominant imports:** `strict_social_emission_will_apply`, `merged_player_prompt_for_gate`, `effective_strict_social_resolution_for_emission`.",
            "",
            "## Terminal emission cluster (16 tagged)",
            "",
            "Fallback line selection and ownership terminal paths across visibility, sealed fallback, terminal pipeline, "
            "response_type, speaker contract, interaction continuity.",
            "",
            "**Dominant import:** `minimal_social_emergency_fallback_line` (BU FI 10).",
            "",
            "## Validators cluster (7 tagged)",
            "",
            "`final_emission_validators`, `final_emission_referential_clarity`, `gm.py`, contextual repair regressions. "
            "Route-legality predicates for social replacement acceptance.",
            "",
            "## Tests cluster (25 importers)",
            "",
            "`tests/test_social_exchange_emission.py` is the **BD-2 KEEP** legality owner. "
            "Additional social/speaker/transcript suites import composition and fallback symbols directly.",
            "",
            "## Replay cluster (1 tagged)",
            "",
            "`tests/test_narration_transcript_regressions.py` — imports `build_final_strict_social_response` and module-level patches. "
            "Replay risk is **behavioral** (strict-social terminal text), not import-graph direct.",
            "",
            "## Diagnostics cluster (1 tagged)",
            "",
            "`tests/test_ownership_registry.py` — BJ-115/116 delegate verification, BN8 strict-social boundary locks, "
            "gate delegator governance map entry for `game.social_exchange_emission`.",
            "",
            "## Ownership bucket cross-cut",
            "",
            "| Bucket | Importers |",
            "| --- | --- |",
        ]
    )
    for bucket, count in data["ownership_bucket_totals"].items():
        lines.append(f"| {bucket} | {count} |")
    (AUDITS / "BV14_usage_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_authority_analysis(data: dict) -> None:
    meta = data["symbol_meta"]
    lines = [
        "# BV14 — Authority vs Utility Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Module self-description vs reality",
        "",
        "Docstring claims: *downstream emission consumer and application layer for strict-social turns; "
        "not the contract owner, not the repair owner.*",
        "",
        "Actual contents span **canonical strict-social composition** (`build_final_strict_social_response`), "
        "**eligibility policy**, **fallback content authority**, **telemetry logging**, **route-legality validators**, "
        "and **102 private helpers** (many never imported externally). The composition subset matches a legitimate authority; "
        "fallback + policy + telemetry co-location creates BV13-style **mixed hub** pressure at FI 52.",
        "",
        "## Export classification (public surface)",
        "",
        "| Export | Class | Verdict |",
        "| --- | --- | --- |",
        "| `build_final_strict_social_response` | canonical-composition-authority | **Legitimate authority** — terminal strict-social assembly owner |",
        "| `apply_strict_social_*_ownership_*`, `normalize_social_exchange_candidate`, `hard_reject_social_exchange_text` | composition-helper | Composition sub-primitives — belong with composition module |",
        "| `strict_social_emission_will_apply`, `should_apply_strict_social_exchange_emission` | policy-vocabulary | **Policy authority** — eligibility predicates; consumers span API + gate |",
        "| `merged_player_prompt_for_gate` | realization-projection | Gate prompt merge — policy/projection seam |",
        "| `minimal_social_emergency_fallback_line`, `select_strict_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback` | fallback-authority | **Fallback content authority** — high FI sprawl (10+ importers) |",
        "| `is_route_illegal_global_or_sanitizer_fallback_text`, `replacement_is_route_legal_social` | validator-projection | Validator vocabulary — belongs with validation module or `final_emission_validators` facade |",
        "| `log_final_emission_decision`, `log_final_emission_trace` | telemetry-projection | Diagnostics — accidental co-location with composition |",
        "| `project_strict_social_replace_realization_family`, `stamp_strict_social_deterministic_fallback_family` | realization-projection | FEM family projection — thin delegates to `realization_provenance` |",
        "| `_npc_display_name_for_emission`, `_speaker_label`, `_has_explicit_interruption_shape` (private leaks) | accidental-bridge | **Encapsulation violation** — production imports private helpers |",
        "",
        "## Canonical authority determination",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Is `social_exchange_emission` a legitimate authority module? | **Partially** — strict-social **composition + fallback content** are genuine authorities |",
        "| Is FI 52 justified by a single concern? | **No** — top symbol FI 10; five concern categories with overlapping consumers |",
        "| What is actually authoritative here? | Terminal strict-social response assembly; emergency fallback line catalog; eligibility will-apply predicates |",
        "| Closest legitimate owners after split | Composition → `social_exchange_composition`; Fallback → `social_exchange_fallback`; Policy → `social_exchange_policy`; Validators → `social_exchange_validation` |",
        "",
        "## Projection helpers vs accidental bridges",
        "",
        "| Pattern | Examples | Assessment |",
        "| --- | --- | --- |",
        "| Canonical composition | `build_final_strict_social_response` | Legitimate — should remain named authority (possibly renamed module) |",
        "| Policy vocabulary | `strict_social_emission_will_apply` | Legitimate but **misplaced breadth** — API + gate + sanitizer share one predicate |",
        "| Fallback authority | `minimal_social_emergency_fallback_line` | Legitimate content owner — **over-imported** across unrelated fallback layers |",
        "| Telemetry | `log_final_emission_*` | Convenience — BJ-115 moved logging calls to direct import; should live in diagnostics module |",
        "| Private helper leaks | `_npc_display_name_for_emission` (4 AST), `_has_explicit_interruption_shape` (2 AST) | **Accidental bridges** — force hub coupling for display/interruption scans |",
        "",
        "## BU1 / BN8 alignment",
        "",
        "BU ownership map marks module as **strict-social composition** (FI 52, 27 production). "
        "BN8 preflight strict-social boundary already treats this as a **coordination seam** with `final_emission_gate_preflight_strict_social`. "
        "BV14 confirms: keep **composition authority centralized**; decompose **fallback FI sprawl** and **private leaks** first (BV13 parallel).",
    ]
    (AUDITS / "BV14_authority_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_candidates(data: dict) -> None:
    lines = [
        "# BV14 — Decomposition Candidates",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Candidate modules",
        "",
        "| Candidate | Extract | Est. FI | Consumers | Migration cost | Replay risk |",
        "| --- | --- | --- | --- | --- | --- |",
        "| **`social_exchange_composition`** | `build_final_strict_social_response`, ownership filters, resolution coercion/reconcile, `hard_reject_social_exchange_text`, GM retry recovery | **~15–20** | strict_social_stack, gm_retry, test legality owner | **Medium** — stack owner coordination | **Medium** — transcript golden strict-social text |",
        "| **`social_exchange_fallback`** | `minimal_social_emergency_fallback_line`, `select_*`, `strict_social_ownership_terminal_fallback`, deterministic/lawful dialogue fallbacks, sanitizer line | **~18–22** | terminal pipeline, visibility, sealed, response_type, gm, sanitizer, 8+ modules | **Medium-high** — widest production sprawl | **High** — shipped fallback phrase catalog |",
        "| **`social_exchange_policy`** | `strict_social_emission_will_apply`, `should_apply_*`, `merged_player_prompt_for_gate`, player-line triggers, narration-beat suppression | **~12–15** | API, preflight, 6 gate policy modules, interaction_context | **Medium** — API + preflight first | **Low** — predicate-only |",
        "| **`social_exchange_validation`** | `is_route_illegal_*`, `replacement_is_route_legal_social`, malformed echo checks | **~6–8** | validators, referential_clarity, gm, sanitizer tests | **Low-medium** | **Low** |",
        "| **`social_exchange_projection`** | `log_final_emission_*`, FEM family stamp/project helpers | **~5–7** | generic_exit, strict_social_stack, visibility, fem_assembly | **Low** | **Low** — telemetry only |",
        "| **Private helper encapsulation** | `_npc_display_name_for_emission`, `_speaker_label`, `_has_explicit_interruption_shape`, `_text_is_strict_social_minimal_emergency_fallback` | **~8–10** | referential_clarity, speaker_contract, dialogue_social_plan, emitted_speaker_signature | **Low** — promote to public on target module or inline at caller | **Low** |",
        "",
        "## Not recommended",
        "",
        "| Candidate | Reason |",
        "| --- | --- |",
        "| Full module deletion | Composition + fallback are genuine production authorities |",
        "| Split composition per sentence-filter | Over-fragmentation — filters are internal to `build_final_strict_social_response` |",
        "| Move eligibility to `response_policy_contracts` | Contracts are read-only; emission predicates need session/world resolution context |",
        "",
        "## Projected FI reduction (module-level)",
        "",
        "| Stage | `social_exchange_emission` FI | New module FI |",
        "| --- | --- | --- |",
        "| Current | **52** | — |",
        "| After Phase 1 extract + compat re-export | **52** (unchanged short-term) | fallback **~20**, policy **~12**, composition **~15** |",
        "| After Phase 2 consumer migration | **~6–10** | fallback **~20**, policy **~12**, composition **~15**, validation **~6** |",
        "| Steady state (compat retired) | **0–4** | named authorities hold direct FI |",
        "",
        "**Net maintenance win:** FI concentration moves from ambiguous 3881-LOC monolith to **named authorities**; "
        "fallback sprawl (FI ~20) becomes explicit maintenance surface rather than hidden in composition module.",
    ]
    (AUDITS / "BV14_decomposition_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hub_analysis(data: dict) -> None:
    lines = [
        "# BV14 — Hub Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "Concentration is **mixed authority/utility** with a **legitimate composition core** — not a pure accidental hub like BV13 `final_emission_text`, "
        "but **larger than a single authority should be** due to fallback FI sprawl and private-helper leaks.",
        "",
        "## Classification matrix",
        "",
        "| Signal | Evidence | Implication |",
        "| --- | --- | --- |",
        "| Multi-symbol FI | Top symbol FI 10 / module FI 52 (19%) | **Not** a single-symbol choke — heterogeneous concerns |",
        "| Production breadth | 27/52 importers in `game/` (52%) | Production-core maintenance magnet |",
        "| LOC / export surface | 3881 LOC, 47 public + 102 private defs | **Oversized** for stated downstream-consumer role |",
        "| Fan-out | 17 deps including `game.gm` (circular risk) | Outward coupling moderate; **inbound** coupling is the problem |",
        "| Fallback sprawl | `minimal_social_emergency_fallback_line` → 10+ production paths | Accidental **fallback hub** layered on composition authority |",
        "| Private symbol imports | 8+ private helpers imported externally | Encapsulation failure — maintenance drag |",
        "| Governance locks | BJ-115/116, BN8 preflight, gate delegator map | Team treats module as **strict-social authority seam** |",
        "| Test legality owner | `tests/test_social_exchange_emission.py` BD-2 KEEP | Legitimate contract surface — decomposition must preserve |",
        "",
        "## Verdict",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Legitimate authority module? | **Partially** — composition + fallback content are real authorities |",
        "| Mixed authority/utility? | **Yes** — composition + policy + fallback + telemetry + validator vocabulary |",
        "| Accidental hub? | **Partially** — fallback sprawl and private leaks resemble BV13 utility accretion |",
        "| Should it remain centralized? | **Core composition yes; periphery no** — BV13-style split for fallback/policy/validation |",
        "",
        "## Comparison to BV13 `final_emission_text`",
        "",
        "| Dimension | BV13 final_emission_text | BV14 social_exchange_emission |",
        "| --- | --- | --- |",
        "| Intent | Unplanned utility accretion | **Planned** strict-social authority (docstring) |",
        "| Single-symbol dominance | 90% `_normalize_text` | 19% top symbol — **multi-concern** |",
        "| LOC | 465 | **3881** |",
        "| Decomposition driver | Symbol category heterogeneity | **Same** + encapsulation repair |",
        "| Replay risk | Low (formatting) | **Medium-high** (fallback phrase catalog) |",
        "| Legitimate core | Formatting primitive only | **Strict-social composition + fallback content** |",
        "",
        "## Comparison to post-BV13 formatting hub",
        "",
        "`final_emission_text_formatting` FI ~51 is **homogeneous** (one concern). "
        "`social_exchange_emission` FI 52 is **heterogeneous** (five concern categories) — "
        "decomposition ROI is **higher** despite similar FI number.",
    ]
    (AUDITS / "BV14_hub_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_plan(data: dict) -> None:
    lines = [
        "# BV14 — Decomposition Plan",
        "",
        "**Date:** 2026-06-21",
        "**Status:** Plan only — **no implementation**",
        "**Primary metric:** `game.social_exchange_emission` FI (current **52**)",
        "**Constraint:** Behavior-preserving; BD-2 legality owner + BN8 preflight boundary remain green",
        "",
        "---",
        "",
        "## Architecture target",
        "",
        "```mermaid",
        "flowchart TB",
        "  subgraph composition [Composition authority]",
        "    COMP[\"social_exchange_composition\"]",
        "  end",
        "  subgraph fallback [Fallback content authority]",
        "    FB[\"social_exchange_fallback\"]",
        "  end",
        "  subgraph policy [Eligibility policy]",
        "    POL[\"social_exchange_policy\"]",
        "  end",
        "  subgraph validation [Route legality]",
        "    VAL[\"social_exchange_validation\"]",
        "  end",
        "  subgraph compat [Compat barrel - temporary]",
        "    LEG[\"social_exchange_emission\"]",
        "  end",
        "  STACK[\"final_emission_strict_social_stack\"] --> COMP",
        "  STACK --> FB",
        "  PREF[\"gate_preflight_strict_social\"] --> POL",
        "  PREF --> COMP",
        "  SAN[\"output_sanitizer\"] --> FB",
        "  SAN --> POL",
        "  FEV[\"final_emission_validators\"] --> VAL",
        "  LEG -.-> COMP",
        "  LEG -.-> FB",
        "  LEG -.-> POL",
        "  LEG -.-> VAL",
        "```",
        "",
        "## Phase 1 — Low-risk extraction (1 cycle)",
        "",
        "**FI target:** 52 → **52** (compat re-exports; measurable symbol split)",
        "",
        "| Step | Action | Verification |",
        "| --- | --- | --- |",
        "| 1.1 | Create `game/social_exchange_fallback.py`; move emergency/deterministic fallback line family | strict_social_stack + visibility + sanitizer tests green |",
        "| 1.2 | Create `game/social_exchange_policy.py`; move will-apply predicates + `merged_player_prompt_for_gate` | API + preflight + narrative authority tests green |",
        "| 1.3 | Create `game/social_exchange_validation.py`; move route-legality predicates | validators + referential_clarity green |",
        "| 1.4 | Create `game/social_exchange_projection.py`; move telemetry + FEM family stamp/project | BJ-115/116 ownership registry green |",
        "| 1.5 | `social_exchange_emission` re-exports moved symbols (compat barrel); composition core stays | AST FI unchanged; symbol FI split in artifact |",
        "| 1.6 | Promote leaked private helpers to public on correct target module OR inline at caller | referential_clarity + speaker_contract green |",
        "| 1.7 | Register modules in ownership registry + gate delegator governance map | ownership registry tests green |",
        "",
        "**Exit criteria:** New modules exist; combined symbol FI measurable; zero consumer import changes required.",
        "",
        "## Phase 2 — Consumer migration (1–2 cycles)",
        "",
        "**FI target:** 52 → **~6–10** on compat barrel",
        "",
        "| Wave | Consumers | Target import | Expected Δ FI |",
        "| --- | --- | --- | --- |",
        "| 2A | Fallback sprawl (visibility, sealed, terminal, response_type, gm, continuity, repairs) | `social_exchange_fallback` | −18 from compat |",
        "| 2B | API + preflight + 6 gate policy modules + interaction_context | `social_exchange_policy` | −12 from compat |",
        "| 2C | validators, referential_clarity, gm route checks | `social_exchange_validation` | −6 from compat |",
        "| 2D | generic_exit, strict_social_stack, visibility, fem_assembly | `social_exchange_projection` | −5 from compat |",
        "| 2E | strict_social_stack composition path | `social_exchange_composition` (direct) | −3 from compat |",
        "| 2F | 25 test modules | target modules (direct) | −15 from compat |",
        "",
        "Migrate **fallback consumers first** — highest FI symbol (`minimal_social_emergency_fallback_line`) and widest sprawl.",
        "",
        "**Exit criteria:** compat FI ≤ **10**; fallback module holds ≥18 direct importers.",
        "",
        "## Phase 3 — Governance lock (1 cycle)",
        "",
        "| Step | Action |",
        "| --- | --- |",
        "| 3.1 | Add `test_bv14_social_exchange_emission_direct_import_guard_*` — new consumers must import named authorities |",
        "| 3.2 | Cap compat barrel FI ≤ **6** (delegate-only + ownership tests + BD-2 re-exports) |",
        "| 3.3 | Extend BN8 preflight guard: forbid fallback/policy imports via compat in preflight modules |",
        "| 3.4 | Forbid external import of `_`-prefixed symbols from compat barrel (encapsulation lock) |",
        "| 3.5 | Document routing in ownership registry quick reference |",
        "",
        "**Exit criteria:** CI prevents hub FI regrowth; production-core top hotspot drops below **final_emission_gate** FI (~30).",
    ]
    (AUDITS / "BV14_decomposition_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_projection(data: dict) -> None:
    lines = [
        "# BV14 — Decomposition Projection",
        "",
        "**Date:** 2026-06-21",
        "**Baseline:** Post-BV13 — `social_exchange_emission` FI **52** (highest production-core concentration)",
        "",
        "---",
        "",
        "## FI projection",
        "",
        "| Stage | `social_exchange_emission` FI | New module FI | Top production hotspot |",
        "| --- | --- | --- | --- |",
        "| BV14 baseline | **52** | — | `social_exchange_emission` **52** |",
        "| After Phase 1 (extract + re-export) | 52 | fallback ~20, policy ~12, composition ~15, validation ~6 | unchanged (compat) |",
        "| After Phase 2 (migration) | **~6–10** | fallback ~20, policy ~12, composition ~15 | `final_emission_text_formatting` ~51 or `final_emission_gate` ~30 |",
        "| After Phase 3 (governance lock) | **≤6** | named authorities stable | gate owner reassessment |",
        "",
        "**Expected net:** compat FI **52 → ~6** (−46), comparable to BV13B **52 → 5**.",
        "",
        "## Scorecard impact (projected post-Phase 2)",
        "",
        "| Dimension | Projected delta | Rationale |",
        "| --- | --- | --- |",
        "| Maintenance drag | **+0.5** | Fallback sprawl localized; composition edits isolated |",
        "| Operational simplicity | **+0.25** | Clear import routing for gate vs fallback vs composition |",
        "| Maintenance economics | **+0.5** | Largest remaining production FI choke split into named authorities |",
        "| Ownership clarity | **+0.5** | BN8/BJ-115 guards updated; private leak pattern eliminated |",
        "",
        "## Replay risk assessment",
        "",
        "| Factor | Risk | Mitigation |",
        "| --- | --- | --- |",
        "| Fallback phrase catalog relocation | **High** | Phase 1 re-export only; golden transcript suite before any phrase edits |",
        "| `build_final_strict_social_response` move | **Medium** | Same function objects via compat; narration transcript regressions first |",
        "| Policy predicate moves | **Low** | Constants/predicates only; API path selection tests |",
        "| Telemetry projection moves | **None** | Logging side-effect only |",
        "| Private helper promotion | **Low** | Behavior-preserving rename to public on target module |",
        "",
        "## BV14C projection (governance)",
        "",
        "| Item | Target | Notes |",
        "| --- | --- | --- |",
        "| Compat barrel FI cap | **≤6** | BD-2 legality owner + delegate tests |",
        "| Import guard | New `test_bv14c_*` | Forbid fallback/policy via compat for new consumers |",
        "| Encapsulation lock | Private symbol ban | Eliminate `_npc_display_name_for_emission` external imports |",
        "",
        "## Success criteria",
        "",
        "**Target state:** `social_exchange_emission` compat barrel **≤6 FI**; "
        "`social_exchange_composition` holds canonical terminal assembly; "
        "fallback FI (~20) is an **explicit** maintenance surface.",
        "",
        "## BV14 executive recommendation",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Remain centralized? | **No** for full module — **yes** for composition core |",
        "| BV13-style decomposition? | **Yes** — parallel pattern: extract fallback/policy/validation, migrate, govern |",
        "| Primary driver | Fallback FI sprawl (10+) + multi-concern 3881 LOC — not illegitimate composition authority |",
        "",
        "Recommended sequence: **BV14** (this decomposition) → reassess **`final_emission_gate`** FI (~30) → "
        "evaluate **`final_emission_terminal_pipeline`** FI (~26).",
    ]
    (AUDITS / "BV14_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    data = load()
    write_dependency_inventory(data)
    write_symbol_concentration(data)
    write_usage_classification(data)
    write_authority_analysis(data)
    write_decomposition_candidates(data)
    write_hub_analysis(data)
    write_decomposition_plan(data)
    write_projection(data)
    print("Wrote 8 BV14 audit documents to docs/audits/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
