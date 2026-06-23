# Cycle M - Maintenance Drag Reduction Recon

Date: 2026-05-27  
Scope: Repository reconnaissance only. This report introduces no runtime, test, fixture, or CI behavior change.

## Executive Summary

Cycles C-L have reduced some ownership ambiguity, but maintenance drag has shifted into repeated downstream evidence edits. In the ten cycle commits from C through L, the most repeatedly touched files are `tests/test_golden_replay.py` (7 commits), `tests/test_failure_classifier.py` (6), `tests/test_final_emission_gate.py` (5), `tests/helpers/golden_replay.py` (5), `tests/helpers/failure_dashboard_report.py` (5), and `tests/test_failure_dashboard_controlled_failures.py` (5). The leading production hotspots are `game/final_emission_meta.py` (4), `game/final_emission_gate.py` (3), and `game/runtime_lineage_telemetry.py` (2).

The gate has improved boundaries: Cycle J extracted opening selection/fail-closed policy into `game/final_emission_opening_fallback.py`, and Cycle L relocated pure visibility-helper tests into `tests/test_final_emission_visibility_fallback.py`. The clearest low-risk next reduction is now outside runtime decisions: both `tools/run_scenario_spine_validation.py` and `tests/helpers/failure_dashboard_report.py` independently aggregate the same runtime-lineage frequency and recurrence buckets that belong conceptually with `game/runtime_lineage_telemetry.py`.

## 1. Current Branch / Baseline

Baseline captured before creating this report:

| Item | Value |
| --- | --- |
| Current branch | `feature/failure-locality` tracking `origin/feature/failure-locality` |
| Latest commit | `f36e83436de9172c1dcdf88224cecd161128518a` (`Cycle L: Test Ownership Compression`) |
| Working tree status | Clean (`git status --short --branch --untracked-files=all` reported only the branch/tracking line) |
| Modified or untracked files at baseline | None |

After this reconnaissance step, this report file is the only intended new working-tree artifact.

## 2. Recent Maintenance Drag Evidence

Meaningful recent cycle window: Cycle C through Cycle L (`a5c9146` through `f36e834`), with support commits between F and H excluded from the primary table because they concern CI/import hygiene rather than maintenance-drag ownership.

| Commit | Title | Files touched | Production/tool files | Test files | Likely subsystem | Localized? |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `f36e834` | Cycle L: Test Ownership Compression | 9 | 0 | 3 | Opening/visibility test ownership | Localized, test/report-only |
| `2619bb5` | K: Promote replay acceptance gate | 16 | 0 | 5 | Golden replay, reporting bridge, CI/docs | Cross-cutting acceptance/reporting |
| `6074e9e` | J: Gate Cluster Extraction | 5 | 2 | 1 | Opening fallback adapter extraction | Localized |
| `fd5f1a9` | Cycle I: Contract opening fallback authorship attribution | 16 | 3 | 10 | Opening authorship lineage and diagnostics | Cross-cutting projection fan-out |
| `b086b75` | H: Runtime Lineage Instrumentation | 12 | 3 | 7 | FEM lineage, scenario/replay/dashboard reporting | Cross-cutting observability |
| `90adbbb` | G: Runtime Stability and Full-Suite Hygiene | 22 | 0 | 6 | Suite hygiene and stored audit evidence | Cross-cutting artifacts/tests |
| `1ae07ea` | Cycle F: Maintenance Drag Measurement and Opening Routing Closure | 16 | 0 | 7 | Failure classification and opening routing diagnostics | Cross-cutting tests/reports |
| `8ddb183` | E: Test Signal Ownership Thinning | 23 | 0 | 13 | Fallback/gate diagnostic ownership | Cross-cutting tests |
| `6c00e6e` | D: Final Emission Gate Pressure Reduction | 17 | 5 | 10 | Gate, visibility/sealed fallback extraction | Cross-cutting extraction |
| `a5c9146` | Cycle C: contract fallback ownership and mutation lineage | 18 | 3 | 11 | Fallback ownership, mutation lineage, dashboard | Cross-cutting contract/projection |

Supporting non-cycle commits in the immediate twenty-commit history:

| Commit | Title | Files touched | Classification |
| --- | --- | ---: | --- |
| `6a402d2` | config: lazy-load OpenAI API key for import-safe tests | 9 | Import/test environment fix |
| `aa9095a` | test: isolate snapshot helpers from live API imports | 5 | Test infrastructure fix |
| `cf6a89c` | ci: update actions for Node 24 runner compatibility | 2 | CI maintenance |
| `98bc059` | Failure Classification Dashboard | 28 | Foundational reporting fan-out |
| `ac1ba90` | Add Golden Replay Scenario-Spine Baseline Suite | 6 | Foundational replay lane |

### Touch Concentration Across Cycles C-L

| Touch count | File | Interpretation |
| ---: | --- | --- |
| 7 | `tests/test_golden_replay.py` | Replay acceptance plus new runtime evidence repeatedly needs projection assertions. |
| 6 | `tests/test_failure_classifier.py` | Ownership/taxonomy diagnostics change with each new emitted signal. |
| 5 | `tests/test_final_emission_gate.py` | Gate remains the main final-output orchestration assertion surface. |
| 5 | `tests/helpers/golden_replay.py` | Observed-turn schema is a repeated diagnostic integration point. |
| 5 | `tests/helpers/failure_dashboard_report.py` | Report shape and new diagnostic summaries fan out here. |
| 5 | `tests/test_failure_dashboard_controlled_failures.py` | Controlled report cases repeat emitted-signal expectations. |
| 4 | `game/final_emission_meta.py` | FEM projection is the current metadata/lineage runtime hotspot. |
| 4 | `tests/helpers/failure_classifier.py` | Classification routing changes alongside FEM vocabulary. |
| 4 | `tests/test_failure_classification_contract.py` | Contract vocabulary grows with diagnostic evidence. |
| 3 | `game/final_emission_gate.py` | Reduced relative to earlier history, but still hot for sequencing/extraction. |
| 3 | `tests/test_run_scenario_spine_validation.py` | Lineage/artifact evidence is duplicated into longitudinal reporting. |

The range `a5c9146^..HEAD` contains 118 changed files overall, heavily inflated by reports and stored Cycle G outputs. The actionable signal is not total range size but recurring edits to gate/FEM/replay/classifier/dashboard surfaces whenever one fallback or lineage contract changes.

## 3. Hotspot File Inventory

| Path | Why it is hot | Repeated change type | Surface role |
| --- | --- | --- | --- |
| `game/final_emission_gate.py` | Canonical final orchestration owner; still integrates strict-social, visibility, opening, fallback behavior, metadata, logging, and final output. | Selection/order/wrapper wiring, `final_emitted_source`, fallback metadata, visibility dispatch. | Orchestration with remaining mixed policy/mutation/logging. |
| `game/final_emission_meta.py` | Packages FEM schema and projects lineage/owner buckets consumed everywhere downstream. | New metadata fields, owner buckets, runtime-lineage projection. | Projection/helper owner. |
| `game/runtime_lineage_telemetry.py` | New read-side event vocabulary introduced in H. | Event fields and recurrence identity. | Read-side helper owner. |
| `game/final_emission_opening_fallback.py` | J extraction isolates prepared opening selection/fail-closed decisions. | Opening selection/fail-closed policy only. | Policy adapter owner. |
| `game/final_emission_visibility_fallback.py` | D extraction isolates visibility route payloads and stamping. | Visibility route/payload/metadata helpers. | Helper owner. |
| `game/final_emission_sealed_fallback.py` | Extracted terminal/visibility-safe sealed route assembly. | Source-family and terminal replacement metadata. | Helper/policy adapter. |
| `game/upstream_response_repairs.py` | Owns upstream-prepared opening payload and strict-social answer-pressure cash-out. | Prepared payload/authorship and upstream repair text. | Repair/prose packaging owner. |
| `tests/test_final_emission_gate.py` | Historical broad gate owner suite, reduced by L but still central. | Orchestration order, wrapper integration, final FEM/source and compatibility pins. | Assertion/integration owner. |
| `tests/test_final_emission_opening_fallback.py` | Direct J adapter tests. | Prepared/fail-closed adapter result contracts. | Assertion owner. |
| `tests/test_final_emission_visibility_fallback.py` | New L direct helper suite. | Visibility route/payload/metadata helper contracts. | Assertion owner. |
| `tests/test_final_emission_visibility.py` | Visibility, first-mention and referential legality pipeline coverage. | Semantic visibility and fallback survival. | Semantic assertion owner/integration. |
| `tests/test_golden_replay.py` | Seven of ten cycle touches; now a protected replay lane. | Observed fallback/lineage/source fields and replay failure artifacts. | Acceptance/projection assertion surface. |
| `tests/helpers/golden_replay.py` | Converts runtime payload into replay observations. | Projection fields and lineage forwarding. | Test projection helper. |
| `tests/helpers/failure_classifier.py` | Routes projected failures to likely owners. | Taxonomy and `investigate_first` logic. | Diagnostic policy helper. |
| `tests/helpers/failure_dashboard_report.py` | Renders classified/lineage diagnostic output. | Report columns and runtime-lineage aggregation. | Reporting helper. |
| `tools/run_scenario_spine_validation.py` | Persists and summarizes longitudinal evidence. | Runtime-lineage aggregation/artifact fields. | Reporting/tooling helper. |

## 4. Gate Edit Concentration

### Current Decision Ownership

| Responsibility | Current owner(s) | Evidence |
| --- | --- | --- |
| Final sequencing, accepted/replaced final text, final integration | `game/final_emission_gate.py::apply_final_emission_gate` | Module declares itself canonical orchestration owner. |
| Opening fallback prose/content | `game/opening_deterministic_fallback.py` | Cycle J/I ownership contract and module comments. |
| Opening fallback upstream packaging | `game/upstream_response_repairs.py` | `build_upstream_prepared_opening_fallback_payload`. |
| Opening selection and fail-closed adapter policy | `game/final_emission_opening_fallback.py` | Extracted in Cycle J. |
| Visibility legality semantics | `game/narration_visibility.py` | Cycle F/L maps identify it as semantic validator owner. |
| Visibility fallback route/payload shaping | `game/final_emission_visibility_fallback.py` | Extracted helper module and L owner test suite. |
| Sealed terminal fallback assembly | `game/final_emission_sealed_fallback.py` | Extracted selection/stamping helpers. |
| Strict-social terminal prose and primary emitted legality | `game/social_exchange_emission.py` | Imported into the gate; `tests/test_social_exchange_emission.py` is named direct semantics owner. |
| FEM schema, owner-bucket read paths and lineage projection | `game/final_emission_meta.py` | Metadata-only owner and `build_fem_runtime_lineage_events`. |
| Lineage vocabulary/normalization | `game/runtime_lineage_telemetry.py` | Read-side leaf module. |
| Replay/classification/dashboard evidence only | `tests/helpers/golden_replay.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/failure_dashboard_report.py` | Diagnostic consumers, not runtime decision owners. |

### Mixed-Responsibility Concentration

`game/final_emission_gate.py` remains the concentration point. It correctly owns orchestration, but it also contains:

- strict-social branches invoking terminal fallback and repeatedly computing final source/metadata;
- `_try_strict_social_local_pronoun_substitution_repair`, a referential repair behavior adjacent to visibility semantics;
- `_apply_visibility_enforcement`, which combines dispatch with final text mutation and logging;
- final emitted-source precedence blocks repeated across accepted/strict-social/non-strict paths;
- final metadata merge and output logging in the same control flow.

The extracted opening and visibility helpers reduced gate-owned leaf policy, but the remaining strict-social and final-source paths are not low-risk first extraction targets.

### Assertion-Only Surfaces

The following files assert or project decisions rather than own runtime selection:

- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_visibility_fallback.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_run_scenario_spine_validation.py`

## 5. Recurring Repair Surfaces

| Surface | Files involved | Canonical owner if obvious | Duplicate or near-duplicate drag | Tests affected by consolidation |
| --- | --- | --- | --- | --- |
| Opening fallback | `game/opening_deterministic_fallback.py`, `game/upstream_response_repairs.py`, `game/final_emission_opening_fallback.py`, `game/final_emission_gate.py`, `game/final_emission_meta.py`, replay/classifier helpers | Split intentionally: composer, packager, selector, projection | Runtime ownership is now mostly clear; downstream opening ownership/lineage fields still recur through replay, classifier and scenario reporting. | `tests/test_final_emission_opening_fallback.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_final_emission_meta.py`, `tests/test_golden_replay.py`, `tests/test_run_scenario_spine_validation.py`, classifier/dashboard suites. |
| Visibility fallback | `game/narration_visibility.py`, `game/final_emission_visibility_fallback.py`, `game/final_emission_gate.py` | Validator semantics: `narration_visibility`; helper routing: `final_emission_visibility_fallback` | Cycle L removed the clearest test co-location problem; gate still mutates/logs final visibility replacement integration. | `tests/test_final_emission_visibility.py`, `tests/test_final_emission_visibility_fallback.py`, `tests/test_final_emission_gate.py`. |
| Strict-social fallback | `game/social_exchange_emission.py`, `game/final_emission_gate.py`, `game/final_emission_repairs.py`, `game/upstream_response_repairs.py`, `game/anti_reset_emission_guard.py` | Primary emitted prose/legality appears to be `social_exchange_emission`; integration remains gate-owned | Broad, not yet demonstrably duplicate: terminal fallback, answer-pressure repair, first-mention exemption and referential local repair cross boundaries. Requires recon before consolidation. | `tests/test_social_exchange_emission.py`, `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_strict_social_answer_pressure_cashout.py`, `tests/test_referential_clarity_strict_social_local_repair.py`, gate/replay tests. |
| Referential clarity local repair | `game/narration_visibility.py`, `game/final_emission_gate.py`, `game/final_emission_repairs.py` | Validation: `narration_visibility`; strict-social substitution presently in gate | `_try_strict_social_local_pronoun_substitution_repair` remains gate-local while related repair vocabulary is in repair/visibility surfaces. | `tests/test_referential_clarity_strict_social_local_repair.py`, `tests/test_final_emission_visibility.py`, `tests/test_final_emission_gate.py`. |
| Fallback source-family/owner tagging | `game/final_emission_meta.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_opening_fallback.py`, classifier/replay helpers | FEM read/projection owner is clearest canonical read-side owner | Similar source/owner fields must be carried and asserted in several downstream lanes. | `tests/test_final_emission_meta.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_golden_replay.py`, classifier/dashboard tests. |
| Runtime-lineage/replay decision metadata | `game/runtime_lineage_telemetry.py`, `game/final_emission_meta.py`, `tools/run_scenario_spine_validation.py`, `tests/helpers/golden_replay.py`, `tests/helpers/failure_dashboard_report.py` | Event vocabulary: `runtime_lineage_telemetry`; FEM projection: `final_emission_meta` | Confirmed near-duplicate frequency/recurrence aggregation in scenario-spine tool and failure-dashboard helper. | `tests/test_runtime_lineage_telemetry.py`, `tests/test_final_emission_meta.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_failure_classifier.py`, `tests/test_golden_replay.py`. |
| Passive pressure/fallback behavior repairs | `game/fallback_behavior.py`, `game/final_emission_repairs.py`, `game/final_emission_gate.py` | Policy contract: `fallback_behavior`; gate integration is final sequencer | Gate carries merge and final-source implications; no small duplicate leaf established in this recon. | `tests/test_fallback_behavior_validator.py`, `tests/test_fallback_behavior_repairs.py`, `tests/test_fallback_behavior_gate.py`, gate suite. |

## 6. Files-Touched-Per-Fix Reduction Opportunities

| Candidate reduction | Files likely touched now | Files likely touched after reduction | Risk | Why Cycle M scope |
| --- | --- | --- | --- | --- |
| **M1: Canonical read-side runtime-lineage summary helper** in `game/runtime_lineage_telemetry.py` (or a small adjacent read-only module) | `tools/run_scenario_spine_validation.py`, `tests/helpers/failure_dashboard_report.py`, their tests whenever a bucket/field is added | One canonical summarizer plus thin consumer rendering/artifact tests | Low | Consolidates already-duplicated diagnostic aggregation; no runtime decision or prose change. |
| **M2: Shared opening-lineage evidence fixture builder** for downstream tests | FEM, golden replay, scenario-spine, classifier/dashboard tests each construct similar opening-success/fail-closed evidence | One test helper plus consumer-specific assertion files only when their contract changes | Low-medium | Reduces test setup churn while preserving distinct downstream assertions. |
| **M3: Source-family/owner-bucket projection contract table** owned by FEM read-side projection | FEM, sealed/opening helpers, replay/classifier contract checks | Canonical projection constants/table plus consumers | Medium | The vocabulary already exists; Cycle M can inventory and characterize before any behavior-neutral consolidation. |
| **M4: Final-source precedence characterization before extraction** | Multiple branches inside `game/final_emission_gate.py` and broad gate tests | Future single selector/helper and focused tests, if equivalence is proven | High | Repeated precedence blocks are clear drag, but only characterization/recon is appropriate until equivalence is locked. |
| **M5: Strict-social ownership map and direct-owner boundary test plan** | Gate, social emission, upstream repairs, visibility/referential tests, replay | Potentially one narrow owner suite or adapter later; no immediate source change | Medium-high | Cycle L explicitly deferred it; Cycle M can make a bounded decision without changing behavior. |

Strongest first implementation candidate: **M1**, because it is confirmed duplicated code in read-only/reporting surfaces and was already identified as an optional follow-up in the Cycle H closure.

## 7. Recommended Cycle M Block Plan

| Block | Goal | Exact files likely involved | Acceptance criteria | Tests to run | Parallel? |
| --- | --- | --- | --- | --- | --- |
| **M1 - Runtime Lineage Summary Leaf Consolidation** | Put frequency/recurrence bucket aggregation behind one read-side helper while retaining consumer input adapters/rendering. | `game/runtime_lineage_telemetry.py`; `tools/run_scenario_spine_validation.py`; `tests/helpers/failure_dashboard_report.py`; `tests/test_runtime_lineage_telemetry.py`; `tests/test_run_scenario_spine_validation.py`; `tests/test_failure_classifier.py` | Scenario and dashboard summaries remain byte-for-field equivalent for covered event inputs; no final-emission/gate files change; no scoring or pass/fail semantics change. | `python -m pytest tests/test_runtime_lineage_telemetry.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_golden_replay.py -q --tb=short` | No with another lineage/reporting block; yes with docs-only M5 recon. |
| **M2 - Opening Evidence Fixture Fan-Out Reduction** | Introduce one test-only fixture/helper for canonical successful and fail-closed opening FEM/lineage observations. | New `tests/helpers/opening_fallback_evidence.py` or existing fixture helper after review; `tests/test_final_emission_meta.py`; `tests/test_golden_replay.py`; `tests/test_run_scenario_spine_validation.py`; optionally classifier/dashboard tests | Assertions remain consumer-specific; fixture replaces only repeated setup literals; collected scenarios and expected owner/source fields remain unchanged. | `python -m pytest tests/test_final_emission_meta.py tests/test_golden_replay.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q --tb=short` | After M1 preferred; overlaps the same tests. |
| **M3 - Source Attribution Projection Recon/Contract Lock** | Determine whether source-family and owner-bucket projection can be made table-driven without altering selection. | Report plus inspection of `game/final_emission_meta.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_opening_fallback.py`, relevant tests | Produce a precise equivalence map and proposed owner; no production edits unless a separately approved tiny extraction is demonstrably identical. | Recon only: no mandatory tests; if a test-only characterization is added, run `tests/test_final_emission_meta.py tests/test_opening_fallback_owner_bucket.py`. | Yes with M5 if reports do not overlap. |
| **M4 - Final-Source Precedence Characterization** | Lock existing repeated `final_emitted_source` precedence outcomes before considering a selector extraction. | `tests/test_final_emission_gate.py` and report only initially; inspect `game/final_emission_gate.py` | Representative accept/strict-social/non-strict replacement branches have focused precedence expectations; runtime source remains untouched. | `python -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_golden_replay.py -q --tb=short` | No with any gate-test edit. |
| **M5 - Strict-Social Boundary Recon** | Classify strict-social terminal prose, local repair, visibility exemption, upstream cash-out, gate integration, and diagnostics before any move. | New report; inspect `game/social_exchange_emission.py`, `game/final_emission_gate.py`, `game/upstream_response_repairs.py`, `game/final_emission_repairs.py`, and strict-social tests | Canonical owner matrix, duplicate-versus-legitimate fan-out finding, and go/no-go extraction recommendation. No source/test behavior changes. | None for report-only work. | Yes with M1 or M3. |

## 8. Files to Pass Back to ChatGPT

### Primary handoff set

1. `docs/cycles/cycle_m_maintenance_drag_reduction_recon_2026-05-27.md` - this Cycle M decision basis.
2. `docs/cycles/cycle_h_runtime_lineage_closure_2026-05-25.md` - explicitly identifies duplicate reporting aggregation as a follow-up.
3. `game/runtime_lineage_telemetry.py` - natural read-side owner for M1.
4. `tools/run_scenario_spine_validation.py` - one duplicated lineage summary implementation.
5. `tests/helpers/failure_dashboard_report.py` - the second duplicated lineage summary implementation.
6. `tests/test_runtime_lineage_telemetry.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_failure_classifier.py`, `tests/test_golden_replay.py` - focused M1 regression set.

### Gate/fallback hotspot context

7. `game/final_emission_gate.py` - orchestration hotspot and future high-risk characterization surface.
8. `game/final_emission_meta.py` - FEM/source/lineage projection hotspot.
9. `game/final_emission_opening_fallback.py`, `tests/test_final_emission_opening_fallback.py` - successful bounded extraction pattern from J/L.
10. `game/final_emission_visibility_fallback.py`, `tests/test_final_emission_visibility_fallback.py`, `tests/test_final_emission_visibility.py` - successful helper/test-ownership separation pattern.
11. `game/upstream_response_repairs.py`, `game/social_exchange_emission.py`, `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_referential_clarity_strict_social_local_repair.py` - strict-social/opening repair boundary context for later recon.

### Existing drag and ownership reports/docs

12. `audits/cycle_f_maintenance_drag_recon_20260517.md`
13. `audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md`
14. `audits/cycle_f_maintenance_drag_closure_20260519.md`
15. `docs/cycles/cycle_j_gate_cluster_extraction_closure_2026-05-26.md`
16. `docs/cycles/cycle_l_test_ownership_compression_closure_2026-05-27.md`
17. `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md`
18. `tests/README_TESTS.md` and `docs/testing.md` - testing/ownership expectations and protected replay lane guidance.

## Recommended Pre-Implementation Baseline Tests

Before implementing M1, run exactly:

```powershell
python -m pytest tests/test_runtime_lineage_telemetry.py tests/test_final_emission_meta.py tests/test_run_scenario_spine_validation.py tests/test_failure_classifier.py tests/test_golden_replay.py -q --tb=short
```

This baseline covers the canonical lineage vocabulary, FEM event producer, both current summary/report consumers, and protected replay projection without invoking a broad behavior-changing gate exercise.
