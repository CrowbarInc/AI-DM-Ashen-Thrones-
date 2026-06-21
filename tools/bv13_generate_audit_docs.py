#!/usr/bin/env python3
"""BV13 — Generate audit markdown from discovery artifact."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "bv13_final_emission_text_analysis.json"
AUDITS = ROOT / "docs" / "audits"


def load() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def sym_list(symbols: list[str]) -> str:
    return ", ".join(f"`{s}`" for s in symbols)


def write_dependency_inventory(data: dict) -> None:
    lines = [
        "# BV13 — Final Emission Text Dependency Inventory",
        "",
        "**Date:** 2026-06-21",
        "**Scope:** Analysis only — every direct importer of `game.final_emission_text`",
        "**Method:** `python tools/bv13_final_emission_text_discovery.py` + BU CSV reconciliation",
        "",
        "---",
        "",
        "## Hub baseline (current)",
        "",
        "| Module | BU fan-in | AST direct importers | Exported symbols | LOC | Fan-out |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| `game.final_emission_text` | **{data['bu_fan_in']}** | {data['ast_direct_importers']} | {data['export_count']} | {data['loc']} | {len(data['fan_out'])} (`diegetic_fallback_narration` only production dep) |",
        "",
        "**BV12 context:** Smoke bridge cluster retired; `final_emission_text` is the largest remaining **production-core** FI node (tied with `social_exchange_emission` at 52).",
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
        "| Subsystem | Importers | Primary symbol |",
        "| --- | --- | --- |",
    ]
    by_sub: dict[str, list] = {}
    for imp in data["importers"]:
        by_sub.setdefault(imp["subsystem"], []).append(imp)
    for sub, items in sorted(by_sub.items(), key=lambda x: -len(x[1])):
        sym_counts: dict[str, int] = {}
        for item in items:
            for s in item["symbols"]:
                clean = s.split(" as ")[0].split(" (")[0].strip()
                if clean and not clean.endswith('\\n"'):
                    sym_counts[clean] = sym_counts.get(clean, 0) + 1
        top = max(sym_counts, key=sym_counts.get) if sym_counts else "—"
        lines.append(f"| {sub} | {len(items)} | `{top}` |")

    lines.extend(["", "## Full importer table", "", "| File | Subsystem | Symbols imported | Ownership bucket |", "| --- | --- | --- | --- |"])
    for imp in sorted(data["importers"], key=lambda x: x["file"]):
        syms = [s for s in imp["symbols"] if not s.endswith('\\n"')]
        if not syms:
            syms = ["(governance string scan only)"]
        lines.append(
            f"| `{imp['file']}` | {imp['subsystem']} | {sym_list(syms)} | {imp['ownership_bucket']} |"
        )
    (AUDITS / "BV13_dependency_inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_symbol_concentration(data: dict) -> None:
    lines = [
        "# BV13 — Symbol Concentration Analysis",
        "",
        "**Date:** 2026-06-21",
        "**Method:** Per-symbol AST importer scan (`artifacts/bv13_final_emission_text_analysis.json`)",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "Module FI **52** is almost entirely **`_normalize_text` concentration (FI 47, 90%)**. The module bundles four unrelated concerns: whitespace normalization, HTML sanitize, validator regex policy, and retired semantic-repair helpers. This is **utility sprawl**, not a single authority surface.",
        "",
        "## Symbol fan-in (ranked)",
        "",
        "| Rank | Symbol | FI | Category | Authority class |",
        "| --- | --- | --- | --- | --- |",
    ]
    for idx, (sym, fi) in enumerate(data["symbol_fi_counts"], 1):
        if sym.endswith('\\n"'):
            continue
        meta = data["symbol_meta"].get(sym, {})
        lines.append(
            f"| {idx} | `{sym}` | **{fi}** | {meta.get('category', 'other')} | {meta.get('authority_class', 'other')} |"
        )

    lines.extend(
        [
            "",
            "## Classification buckets",
            "",
            "| Category | Symbols | Combined FI | Role |",
            "| --- | --- | --- | --- |",
            "| **Formatting** | `_normalize_text`, `_normalize_text_preserve_paragraphs`, `_sanitize_output_text`, `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment` | **56** (module-level; `_normalize_text` shared) | Whitespace/HTML/punctuation primitives |",
            "| **Policy constants** | `_RESPONSE_TYPE_VALUES`, `_ANSWER_*`, `_ACTION_*`, `_AGENCY_*` | **13** (unique importers ~6) | Validator / contract regex vocabulary |",
            "| **Orchestration wrapper** | `_global_narrative_fallback_stock_line` | **3** | Diegetic fallback delegate + stock line |",
            "| **Legacy semantic repair** | `_decompress_overpacked_sentences`, `_repair_fragmentary_participial_splits` (+ 6 internal helpers, **0 production importers**) | **1** (tests only) | Retired C2 boundary repair — docstring says not invoked in production |",
            "",
            "## Read-only vs mutating",
            "",
            "| Export kind | Count | Notes |",
            "| --- | --- | --- |",
            "| Read-only pure functions | 14 | All formatting + legacy repair helpers |",
            "| Read-only constants | 6 | Pattern tuples + `_RESPONSE_TYPE_VALUES` |",
            "| Orchestration (calls diegetic) | 1 | `_global_narrative_fallback_stock_line` |",
            "",
            "## Highest fan-in exports (maintenance risk)",
            "",
            "| Rank | Symbol | FI | Risk |",
            "| --- | --- | --- | --- |",
            "| 1 | `_normalize_text` | 47 | **Critical** — cross-cuts gate, finalize, social, fallback |",
            "| 2 | `_normalize_terminal_punctuation` | 4 | Low — repairs + authenticity only |",
            "| 3 | `_ACTION_RESULT_PATTERNS` / `_ANSWER_DIRECT_PATTERNS` / `_normalize_text_preserve_paragraphs` / `_global_narrative_fallback_stock_line` | 3 each | Medium — policy/fallback coupling |",
            "| 4 | `_sanitize_output_text` / `_ANSWER_FILLER_PATTERNS` / `_RESPONSE_TYPE_VALUES` | 2 each | Low-medium |",
        ]
    )
    (AUDITS / "BV13_symbol_concentration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_usage_classification(data: dict) -> None:
    lines = [
        "# BV13 — Usage Classification",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Consumer groups (BV13 taxonomy)",
        "",
        "| Usage class | Importers | Share | Typical symbols |",
        "| --- | --- | --- | --- |",
    ]
    by_class: dict[str, list] = {}
    for imp in data["importers"]:
        for cls in imp["usage_classes"]:
            by_class.setdefault(cls, []).append(imp["file"])
    totals = data["usage_class_totals"]
    for cls, count in sorted(totals.items(), key=lambda x: -x[1]):
        share = f"{100 * count // sum(totals.values())}%"
        examples = by_class.get(cls, [])[:3]
        sym_hint = "`_normalize_text`" if cls != "ownership" else "governance scans"
        lines.append(f"| **{cls}** | {count} | {share} | {sym_hint} (e.g. `{examples[0]}` …) |" if examples else f"| **{cls}** | {count} | {share} | — |")

    lines.extend(
        [
            "",
            "> **Note:** Importers may appear in multiple classes (e.g. gate test suites = `gate` + `tests`). Totals sum to **58** tag assignments across **52** files.",
            "",
            "## Gate cluster (28 tagged)",
            "",
            "Gate owner, preflight modules (BN9 extractions), pipeline layers, and gate test suites. **Dominant import:** `_normalize_text` only (24/28 gate-tagged files).",
            "",
            "Representative: `final_emission_gate`, `final_emission_gate_preflight_*`, `final_emission_validators`, `final_emission_repairs`, `final_emission_strict_social_stack`.",
            "",
            "## Finalization cluster (10 tagged)",
            "",
            "Upstream narrative/social modules outside the gate trunk: `acceptance_quality`, `dialogue_social_plan`, `speaker_contract_enforcement`, `narrative_mode_contract`, `upstream_response_repairs`.",
            "",
            "## Diagnostics cluster (6 tagged)",
            "",
            "Fallback provenance, visibility/sealed/opening fallback, fast fallback composition. Mix of normalize + sanitize + stock-line wrapper.",
            "",
            "## Tests cluster (13 importers)",
            "",
            "Integration regressions, gate boundary suites, speaker helpers, diegetic fallback block4. One legacy-repair suite (`test_final_emission_visibility`).",
            "",
            "## Ownership cluster (1)",
            "",
            "`tests/test_ownership_registry.py` — BN9 pregate-text import guard + BJ-111/112 delegate verification (module import + synthetic string fixtures).",
            "",
            "## Replay / observability",
            "",
            "**No direct replay importers.** Replay suites consume normalized text **indirectly** via gate orchestration smoke and golden fixtures. Text normalization at replay boundary is embedded in production gate/finalize path — **replay risk is behavioral**, not import-graph.",
            "",
            "## Ownership bucket cross-cut",
            "",
            "| Bucket | Importers |",
            "| --- | --- |",
        ]
    )
    for bucket, count in data["ownership_bucket_totals"].items():
        lines.append(f"| {bucket} | {count} |")
    (AUDITS / "BV13_usage_classification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_authority_analysis(data: dict) -> None:
    lines = [
        "# BV13 — Authority vs Utility Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Module self-description vs reality",
        "",
        "Docstring claims: *\"Shared text utilities … No policy orchestration.\"*",
        "",
        "Actual contents span **formatting**, **validator policy constants**, **fallback content wrapper**, and **legacy semantic repair** (test-only). Only the formatting subset matches the stated role.",
        "",
        "## Export classification",
        "",
        "| Export | Class | Verdict |",
        "| --- | --- | --- |",
        "| `_normalize_text` | formatting-helper | **Canonical primitive** — should live in dedicated formatting module |",
        "| `_normalize_text_preserve_paragraphs` | formatting-helper | Canonical primitive (strict-social / NA paragraph seams) |",
        "| `_sanitize_output_text` | formatting-helper | Canonical primitive (finalize + provenance debug) |",
        "| `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment`, `_has_terminal_punctuation` | formatting-helper | Formatting sub-primitives |",
        "| `_RESPONSE_TYPE_VALUES` | policy-constant | **Misplaced authority** — belongs with `response_policy_contracts` or validator policy module |",
        "| `_ANSWER_*`, `_ACTION_*`, `_AGENCY_*` pattern tuples | policy-constant | **Misplaced authority** — validator vocabulary; currently split across `final_emission_validators` consumers |",
        "| `_global_narrative_fallback_stock_line` | convenience-wrapper | Accidental bridge to `diegetic_fallback_narration` — content authority is diegetic, not text utils |",
        "| `_decompress_overpacked_sentences`, `_repair_fragmentary_participial_splits` (+ helpers) | accidental-bridge | **Retired production path** — C2 packaging-only boundary explicitly excludes these; test-only retention |",
        "",
        "## Canonical authority determination",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Is `final_emission_text` a legitimate authority module? | **No** — it is a **mixed utility hub** with no write ownership or orchestration role |",
        "| What is actually authoritative here? | Nothing. All exports are pure functions/constants consumed by gate, validators, and finalize layers |",
        "| Closest legitimate owners | Formatting → new `final_emission_text_formatting`; policy tuples → `final_emission_validators` or `response_policy_contracts`; stock line → `diegetic_fallback_narration` facade |",
        "",
        "## Projection helpers vs accidental bridges",
        "",
        "| Pattern | Examples | Assessment |",
        "| --- | --- | --- |",
        "| Projection helpers | `_normalize_text` used for comparison/hashing in tests | Legitimate **if** owned by formatting module |",
        "| Convenience wrappers | `_global_narrative_fallback_stock_line` | Thin delegate — creates cross-domain fallback coupling |",
        "| Accidental bridges | Legacy participial repair suite in same module as normalize | Violates C2 boundary; increases perceived hub authority |",
        "",
        "## BU1 alignment",
        "",
        "BU1 stack contract marked `final_emission_text` as **\"Keep (shared primitive)\"** for normalize only. BV13 confirms that verdict for **`_normalize_text`** but rejects keeping policy + legacy repair in the same module.",
    ]
    (AUDITS / "BV13_authority_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_candidates(data: dict) -> None:
    lines = [
        "# BV13 — Decomposition Candidates",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Candidate modules",
        "",
        "| Candidate | Extract | Est. FI | Consumers | Migration cost | Replay risk |",
        "| --- | --- | --- | --- | --- | --- |",
        "| **`final_emission_text_formatting`** | `_normalize_text`, `_normalize_text_preserve_paragraphs`, `_sanitize_output_text`, `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment`, `_has_terminal_punctuation` | **~47–52** | 39 production + 12 test | **Medium** — mechanical import rewrite across gate trunk | **Low** — pure functions; golden hash stable if behavior preserved |",
        "| **`final_emission_text_policy`** | `_RESPONSE_TYPE_VALUES`, `_ANSWER_*`, `_ACTION_*`, `_AGENCY_*` | **~6** | validators, referential_clarity, answer_shape_primacy, narrative_mode_contract, interaction_continuity, response_policy_contracts | **Low-medium** — 6 modules + validator owner coordination | **Low** — constants only |",
        "| **`final_emission_text_projection`** | (optional) re-export barrel for tests comparing normalized text | **~5–8** | test helpers only | **Low** | **Low** |",
        "| **Retire / isolate legacy repair** | `_decompress_*`, `_repair_*`, participial helpers | **1** | `test_final_emission_visibility` only | **Low** — move to test fixture or `legacy_semantic_repair_archive` | **None** — not on production path |",
        "| **Fallback stock line** | `_global_narrative_fallback_stock_line` | **3** | fast_fallback_composition, scene_emit_integrity, diegetic test | **Low** — colocate with `diegetic_fallback_narration` or `final_emission_fast_fallback_composition` | **Medium** — touches shipped fallback text |",
        "",
        "## Not recommended",
        "",
        "| Candidate | Reason |",
        "| --- | --- |",
        "| `final_emission_text_views` | No view/projection exports exist — module is function/constants only |",
        "| Full module deletion | Formatting primitive is genuinely shared; deletion would recreate hub elsewhere |",
        "",
        "## Projected FI reduction (module-level)",
        "",
        "| Stage | `final_emission_text` FI | New module FI |",
        "| --- | --- | --- |",
        "| Current | **52** | — |",
        "| After formatting extract + compat re-export | **52** (unchanged short-term) | formatting **47** |",
        "| After consumer migration (formatting) | **~5–8** | formatting **47** |",
        "| After policy extract | **~2–3** (compat/legacy only) | policy **6**, formatting **47** |",
        "| Steady state (compat retired) | **0–2** | formatting **47**, policy **6** |",
        "",
        "**Net maintenance win:** FI **concentration** moves from ambiguous hub to **named primitive owner** (formatting FI ~47 is *legitimate* — same as stdlib `json` pattern for a true shared utility).",
    ]
    (AUDITS / "BV13_decomposition_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_hub_analysis(data: dict) -> None:
    lines = [
        "# BV13 — Hub Analysis",
        "",
        "**Date:** 2026-06-21",
        "",
        "---",
        "",
        "## Executive answer",
        "",
        "Concentration is **mixed authority/utility** trending toward **accidental hub**. The module is *not* a legitimate authority owner — it accumulated normalize calls (BJ-111/112 gate delegator extractions), validator policy tuples, and retired semantic repair in one file.",
        "",
        "## Classification matrix",
        "",
        "| Signal | Evidence | Implication |",
        "| --- | --- | --- |",
        "| Single-symbol dominance | `_normalize_text` FI 47 / 52 (90%) | Hub is **normalize choke**, not policy orchestration |",
        "| Production breadth | 39/52 importers in `game/` | Production-core maintenance magnet |",
        "| Fan-out tail | 4 deps; only `diegetic_fallback_narration` is domain | Low outward coupling — **inbound** coupling is the problem |",
        "| Policy constants in utility module | 6 pattern tuples + response types | Accidental policy authority |",
        "| Legacy repair co-location | 200+ LOC, 0 production importers | Accidental bridge / dead weight |",
        "| Governance locks | BN9 pregate-text guard forbids gate context → direct import | Team already treats hub as **leaky** |",
        "",
        "## Verdict",
        "",
        "| Question | Answer |",
        "| --- | --- |",
        "| Legitimate authority module? | **No** |",
        "| Mixed authority/utility? | **Yes** — formatting (legitimate) + policy + legacy (illegitimate co-location) |",
        "| Accidental hub? | **Yes** — BJ cycle delegator migrations routed normalize here instead of a named primitive module |",
        "| Should it remain centralized? | **Partial** — keep **one formatting primitive module**; decompose policy and retire legacy |",
        "",
        "## Comparison to BV12 smoke bridges",
        "",
        "| Dimension | BV12 smoke bridges | BV13 final_emission_text |",
        "| --- | --- | --- |",
        "| Intent | Intentional test facades (BV7 design) | Unplanned production utility accretion |",
        "| Export count | 4 total | 20 symbols, 6 categories |",
        "| LOC | 84 combined | 465 |",
        "| Decomposition driver | Consumer heterogeneity | **Symbol category heterogeneity** |",
        "| Replay risk | Low (delegates) | Low formatting / medium fallback stock line |",
    ]
    (AUDITS / "BV13_hub_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decomposition_plan(data: dict) -> None:
    lines = [
        "# BV13 — Decomposition Plan",
        "",
        "**Date:** 2026-06-21",
        "**Status:** Plan only — **no implementation**",
        "**Primary metric:** `game.final_emission_text` FI (current **52**)",
        "**Constraint:** Behavior-preserving; BN9 pregate-text guards + C2 no-semantic-repair boundary remain green",
        "",
        "---",
        "",
        "## Architecture target",
        "",
        "```mermaid",
        "flowchart TB",
        "  subgraph formatting [Formatting primitive]",
        "    FMT[\"final_emission_text_formatting\"]",
        "  end",
        "  subgraph policy [Validator policy vocabulary]",
        "    POL[\"final_emission_text_policy\"]",
        "  end",
        "  subgraph compat [Compat barrel - temporary]",
        "    LEG[\"final_emission_text\"]",
        "  end",
        "  GATE[\"final_emission_gate + preflight_*\"] --> FMT",
        "  VAL[\"final_emission_validators\"] --> FMT",
        "  VAL --> POL",
        "  FIN[\"final_emission_finalize\"] --> FMT",
        "  RPC[\"response_policy_contracts\"] --> POL",
        "  LEG -.-> FMT",
        "  LEG -.-> POL",
        "```",
        "",
        "## Phase 1 — Low-risk extraction (1 cycle)",
        "",
        "**FI target:** 52 → **52** (compat re-exports; measurable symbol split)",
        "",
        "| Step | Action | Verification |",
        "| --- | --- | --- |",
        "| 1.1 | Create `game/final_emission_text_formatting.py`; move whitespace/HTML/punctuation helpers | All existing tests green; no behavior change |",
        "| 1.2 | Create `game/final_emission_text_policy.py`; move pattern tuples + `_RESPONSE_TYPE_VALUES` | validators + response_policy_contracts green |",
        "| 1.3 | `final_emission_text` re-exports moved symbols (compat barrel) | AST FI unchanged; symbol FI split in artifact |",
        "| 1.4 | Move legacy semantic repair to `tests/helpers/legacy_semantic_repair_fixtures.py` OR `game/_legacy_semantic_repair_archive.py` | boundary_no_semantic_repair + visibility tests green |",
        "| 1.5 | Register modules in ownership registry + gate delegator governance map | ownership registry tests green |",
        "",
        "**Exit criteria:** New modules exist; combined symbol FI measurable; zero consumer import changes required.",
        "",
        "## Phase 2 — Consumer migration (1–2 cycles)",
        "",
        "**FI target:** 52 → **~5–8** on compat barrel",
        "",
        "| Wave | Consumers | Target import | Expected Δ FI |",
        "| --- | --- | --- | --- |",
        "| 2A | 24 gate-trunk modules (`final_emission_*`, preflight_*) | `final_emission_text_formatting` | −24 from compat |",
        "| 2B | 6 narrative/social upstream modules | formatting | −6 |",
        "| 2C | 6 validator/policy consumers | policy (+ formatting where needed) | −6 |",
        "| 2D | 3 fallback stock-line consumers | diegetic facade or fast_fallback owner | −3 |",
        "| 2E | 13 test modules | formatting (direct) | −13 |",
        "",
        "Migrate **gate preflight modules first** — aligns with existing BN9 extractions and ownership registry guards.",
        "",
        "**Exit criteria:** `final_emission_text` compat FI ≤ **8**; formatting module holds ≥45 direct importers.",
        "",
        "## Phase 3 — Governance lock (1 cycle)",
        "",
        "| Step | Action |",
        "| --- | --- |",
        "| 3.1 | Add `test_bv13_final_emission_text_direct_import_guard_*` — new consumers must import formatting/policy, not compat barrel |",
        "| 3.2 | Cap compat barrel FI ≤ **5** (delegate-only + ownership tests) |",
        "| 3.3 | Extend BN9 gate-context guard: forbid `_normalize_text` from compat in pregate modules (require formatting module) |",
        "| 3.4 | Document routing in ownership registry quick reference |",
        "",
        "**Exit criteria:** CI prevents hub FI regrowth; production-core top hotspot drops below **social_exchange_emission** tie line.",
    ]
    (AUDITS / "BV13_decomposition_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_projection(data: dict) -> None:
    lines = [
        "# BV13 — Decomposition Projection",
        "",
        "**Date:** 2026-06-21",
        "**Baseline:** BV11/BV12 post-closeout — `final_emission_text` FI **52** (tied #1 production hotspot)",
        "",
        "---",
        "",
        "## FI projection",
        "",
        "| Stage | `final_emission_text` FI | `formatting` FI | `policy` FI | Top production hotspot |",
        "| --- | --- | --- | --- | --- |",
        "| Current (BV13 baseline) | **52** | — | — | tied 52 (`social_exchange_emission`) |",
        "| After Phase 1 (extract + re-export) | 52 | ~47 | ~6 | unchanged (compat) |",
        "| After Phase 2 (migration) | **5–8** | **47** | **6** | `social_exchange_emission` **52** (text hub demoted) |",
        "| After Phase 3 (compat cap) | **≤5** | **47** | **6** | formatting primitive (legitimate) |",
        "",
        "## Scorecard impact (projected post-Phase 2)",
        "",
        "| Dimension | Projected delta | Rationale |",
        "| --- | --- | --- |",
        "| Maintenance drag | **+0.25 to +0.5** | Hub ambiguity removed; edits localize to formatting vs policy |",
        "| Operational simplicity | **+0.25** | Clear import routing for gate vs validator changes |",
        "| Maintenance economics | **+0.5** | Largest production FI node split into named concerns |",
        "| Ownership clarity | **+0.5** | BN9 guards align with module boundaries |",
        "",
        "## Replay risk assessment",
        "",
        "| Factor | Risk | Mitigation |",
        "| --- | --- | --- |",
        "| `_normalize_text` behavior change | **Low** | Extract-only Phase 1; golden hashes unchanged |",
        "| Fallback stock line relocation | **Medium** | Migrate last; diegetic contract tests first |",
        "| Policy tuple moves | **Low** | Constants-only; validator suites catch drift |",
        "| Legacy repair isolation | **None** | Not on production path (C2 boundary) |",
        "| Gate preflight import churn | **Low-medium** | Wave 2A isolated; BN9 guards updated in Phase 3 |",
        "",
        "## Success criteria",
        "",
        "**Clear determination:** `final_emission_text` should **undergo BV2/BV10-style decomposition** — not remain as a centralized authority module. The **formatting primitive** may remain a high-FI module by design (~47), but the current **mixed hub** (FI 52) should not persist.",
        "",
        "Recommended sequence: **BV13** (text/formatting/policy split) → **BV14** (`social_exchange_emission` parallel) → reassess gate owner FI (30) after production text choke resolved.",
    ]
    (AUDITS / "BV13_projection.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    print("Wrote 8 BV13 audit docs to docs/audits/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
