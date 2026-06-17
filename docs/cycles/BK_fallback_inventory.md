# BK — Fallback Inventory

**Cycle:** BK (Fallback Ownership Compression) — Discovery / Audit  
**Date:** 2026-06-16  
**Scope:** Inventory only. No refactors performed.

---

## Search methodology

Repository-wide grep for: `fallback`, `default`, `missing`, `empty`, `placeholder`, `synthetic`, `projection`, `selection`, `content`, `replay`. Cross-referenced with filename glob `*fallback*`, `*projection*`, prior cycle docs (AP, AB, AM, AU, AJ), and `docs/architecture_ownership_ledger.md`.

**Tier legend**

| Tier | Meaning |
|------|---------|
| **A** | Core runtime fallback owner |
| **B** | Adjacent runtime participant (selection, projection, emission path) |
| **C** | Test / replay / tooling support |
| **D** | Docs / audits / governance (reference only) |

---

## A. Policy & contract

| File | ~LOC | Tier | Responsibility | Fallback role | Primary owner |
|------|------|------|----------------|---------------|---------------|
| `game/fallback_behavior.py` | 436 | A | Deterministic fallback **policy contract** (uncertainty modes, hedge forms, authority bases) | **Contract creation** for prompt/policy; no prose | `game/fallback_behavior` |
| `game/response_policy_contracts.py` | — | B | Shipped policy reads; exposes `fallback_behavior` on contracts | **Consume** contract shape | `response_policy_contracts` |
| `game/response_policy_enforcement.py` | — | B | Post-GPT enforcement; projects `fallback_behavior_contract` into emission debug | **Project** policy metadata | `response_policy_enforcement` |
| `game/prompt_context.py` | — | B | Builds prompt bundle; calls `build_fallback_behavior_contract` | **Consume** contract for prompts | `prompt_context` |
| `docs/retry_fallback_selector_contract.md` | — | D | Prose contract for retry fallback selection | Governance | — |

---

## B. Content creation (prose & templates)

| File | ~LOC | Tier | Responsibility | Fallback role | Primary owner |
|------|------|------|----------------|---------------|---------------|
| `game/diegetic_fallback_narration.py` | 621 | A | **Diegetic template library**; `fallback_template_metadata`, render helpers | **Content SSOT** for diegetic lines & `fallback_family_used` taxonomy | `diegetic_fallback_narration` |
| `game/opening_deterministic_fallback.py` | 204 | A | Opening prose composer; curated-facts assembly | **Content** for opening deterministic fallback | `opening_deterministic_fallback` |
| `game/social_exchange_emission.py` | 3452 | A | Strict-social emission; `minimal_social_emergency_fallback_line`, terminal dialogue fallback | **Content + selection** for strict-social paths | `social_exchange_emission` |
| `game/gm_retry.py` | 2621 | A | Retry terminal fallback lines; `select_*_retry_fallback_line` | **Content + selection** for upstream/retry fast paths | `gm_retry` |
| `game/anti_reset_emission_guard.py` | — | B | `local_exchange_continuation_fallback_line`, intro suppression | **Content** for anti-reset continuation | `anti_reset_emission_guard` |
| `game/final_emission_text.py` | — | B | `_global_narrative_fallback_stock_line`, `render_global_scene_anchor_fallback` delegate | **Content** global stock line | `final_emission_text` → diegetic |
| `game/upstream_response_repairs.py` | 532 | A | Packages `upstream_prepared_opening_fallback`; stamps authorship | **Content packaging** upstream of gate | `upstream_response_repairs` |
| `game/final_emission_fast_fallback_composition.py` | 201 | B | Neutral composition layer on fast-fallback text | **Content composition** (non-prose policy) | `final_emission_fast_fallback_composition` |
| `game/output_sanitizer.py` | 1340 | B | `_diegetic_uncertainty_fallback`, `social_fallback_line_for_sanitizer`, empty-output fallback | **Content selection** at sanitizer boundary | `output_sanitizer` |

---

## C. Selection & routing

| File | ~LOC | Tier | Responsibility | Fallback role | Primary owner |
|------|------|------|----------------|---------------|---------------|
| `game/final_emission_visibility_fallback.py` | 1627 | A | Visibility validation routing; `standard_visibility_safe_fallback`, candidate assembly | **Primary gate visibility selector** (coordinates sub-selectors) | `final_emission_visibility_fallback` |
| `game/final_emission_opening_fallback.py` | 372 | A | Opening selection; fail-closed policy; upstream-prepared snapshot pick | **Opening selector** | `final_emission_opening_fallback` |
| `game/final_emission_sealed_fallback.py` | 412 | A | Sealed terminal selection; provider assembly; realization family stamp | **Sealed selector** (wraps visibility selections) | `final_emission_sealed_fallback` |
| `game/final_emission_scene_emit_integrity.py` | — | B | `_scene_emit_integrity_global_fallback_selection` | **Sub-selector** for emit-integrity path | `final_emission_scene_emit_integrity` |
| `game/final_emission_first_mention_composition.py` | — | B | `_grounded_scene_intro_fallback_candidates` | **Sub-selector** for first-mention composition | `final_emission_first_mention_composition` |
| `game/final_emission_passive_scene_pressure.py` | — | B | `_passive_scene_pressure_fallback_candidates` | **Sub-selector** for passive pressure | `final_emission_passive_scene_pressure` |
| `game/final_emission_response_type.py` | — | B | Response-type contract; delegates opening selection | **Orchestration** calling opening selector | `final_emission_response_type` |
| `game/final_emission_generic_exit.py` | — | B | Non-strict replace path; calls sealed selection | **Emission path** consumer | `final_emission_generic_exit` |
| `game/final_emission_terminal_pipeline.py` | — | B | `apply_visibility_enforcement`, strict-social emergency patch | **Pipeline** invoking visibility module | `final_emission_terminal_pipeline` |
| `game/final_emission_acceptance_quality.py` | — | B | Calls `select_acceptance_quality_n4_sealed_fallback_line` | **Quality-path selector** consumer | `final_emission_acceptance_quality` |
| `game/api.py` | 5201 | B | `_fast_fallback_for_upstream_error`; attaches provenance | **Upstream fast-fallback trigger** | `api` |
| `game/opening_visible_fact_selection.py` | — | B | Curated fact selection feeding opening context | **Pre-selection** for opening content | `opening_visible_fact_selection` |

---

## D. Projection, metadata & provenance

| File | ~LOC | Tier | Responsibility | Fallback role | Primary owner |
|------|------|------|----------------|---------------|---------------|
| `game/final_emission_meta.py` | 1776 | A | FEM packaging; `OPENING_FALLBACK_PROJECTION_FIELDS`, owner-bucket mappers | **Metadata projection SSOT** | `final_emission_meta` |
| `game/final_emission_replay_projection.py` | 595 | A | `build_fem_runtime_lineage_events`; split selection/content owners on lineage | **Runtime lineage projection** | `final_emission_replay_projection` |
| `tests/helpers/golden_replay_projection.py` | 1377 | A | `project_turn_observation`, protected paths, `project_replay_fallback_family_from_fem` | **Acceptance/replay projection** (test-only authority) | `golden_replay_projection` |
| `game/fallback_provenance_debug.py` | 293 | B | `fallback_provenance_trace`; upstream fast-fallback fingerprinting | **Provenance packaging** (documented temporary seam) | `fallback_provenance_debug` |
| `game/realization_provenance.py` | — | B | `realization_fallback_family` stamps | **Governed family taxonomy** | `realization_provenance` |
| `game/realization_authority.py` | — | B | `FALLBACK_FAMILIES` registry | **Family registry** | `realization_authority` |
| `game/runtime_lineage_telemetry.py` | — | B | Lineage event envelope; attribution field vocabulary | **Telemetry transport** | `runtime_lineage_telemetry` |
| `game/stage_diff_telemetry.py` | — | B | Stage snapshots may include fallback-shaped telemetry | **Downstream consumer** | `stage_diff_telemetry` |
| `game/dead_turn_report_visibility.py` | — | B | Dead-turn reporting reads fallback meta | **Reporting consumer** | `dead_turn_report_visibility` |

---

## E. Validation, repair & gate orchestration

| File | ~LOC | Tier | Responsibility | Fallback role | Primary owner |
|------|------|------|----------------|---------------|---------------|
| `game/final_emission_gate.py` | 308 | B | Gate orchestration; calls visibility/opening/response-type paths | **Orchestrator** (not content owner) | `final_emission_gate` |
| `game/final_emission_repairs.py` | 1123 | B | `repair_fallback_behavior`; fallback-behavior layer in non-strict stack | **Repair** of fallback-behavior contract compliance | `final_emission_repairs` |
| `game/final_emission_validators.py` | 1942 | B | `validate_fallback_behavior`; validator debug mirrors | **Validate** fallback-behavior contract | `final_emission_validators` |
| `game/final_emission_non_strict_stack.py` | — | B | Applies fallback-behavior + fast-fallback composition layers | **Stack consumer** | `final_emission_non_strict_stack` |
| `game/final_emission_strict_social_stack.py` | — | B | Fast-fallback composition + provenance realign | **Stack consumer** | `final_emission_strict_social_stack` |
| `game/final_emission_gate_context.py` | — | B | Gate context; fast-fallback composition meta defaults | **Context packaging** | `final_emission_gate_context` |
| `game/final_emission_boundary_contract.py` | — | B | Registers disallowed semantic mutations (e.g. compatibility-local compose) | **Boundary registry** | `final_emission_boundary_contract` |
| `game/interaction_continuity.py` | — | B | Continuity repair may interact with fallback-shaped outputs | **Adjacent repair** | `interaction_continuity` |
| `game/narration_visibility.py` | — | B | Visibility validators driving fallback routing decisions | **Validation input** to visibility fallback | `narration_visibility` |

---

## F. Replay construction, assertion & manifest support

| File | Tier | Responsibility | Fallback role |
|------|------|----------------|---------------|
| `tests/helpers/golden_replay.py` | C | Golden replay harness; assembles observed turns | **Replay construction** |
| `tests/helpers/golden_replay_api.py` | C | API-level golden replay helpers | **Replay construction** |
| `tests/helpers/golden_replay_fixtures.py` | C | Fixture payloads for golden scenarios | **Replay fixtures** |
| `tests/helpers/golden_replay_profiles.py` | C | Profile wiring for replay runs | **Replay config** |
| `tests/helpers/opening_fallback_evidence.py` | 207 | Canonical FEM-shaped opening evidence builders | **Assertion fixtures** |
| `tests/helpers/opening_fallback_gate_harness.py` | 54 | Attach-then-gate opening harness | **Integration harness** |
| `tests/helpers/fallback_behavior_fixtures.py` | 123 | Fallback-behavior contract fixtures | **Assertion fixtures** |
| `tests/helpers/replay_observed_row_fixtures.py` | C | Observed-row builders for classifier/dashboard | **Replay row fixtures** |
| `tests/helpers/failure_classification_sync.py` | C | Syncs failure classification with replay projection | **Classifier bridge** |
| `tests/helpers/failure_classifier.py` | C | Uses `opening_fallback_owner_bucket_from_meta` | **Classifier consumer** |
| `tests/helpers/emission_smoke_assertions.py` | C | Smoke assertions on emission surfaces | **Assertion support** |
| `tests/helpers/runtime_lineage_reporting.py` | C | Lineage reporting for tests | **Assertion support** |
| `tests/helpers/replay_drift_taxonomy.py` | C | Drift bucket taxonomy | **Classification support** |
| `tests/helpers/replay_drift_rows.py` | C | Drift row builders | **Assertion support** |
| `tests/replay_governance_registry.py` | C | Replay governance contract registry | **Manifest governance** |
| `tests/failure_classification_contract.py` | C | Allowed bucket values; classifier contract | **Assertion contract** |
| `tools/refresh_protected_replay_manifest.py` | C | Refreshes protected replay field manifest from projection module | **Manifest tooling** |
| `tools/run_scenario_spine_validation.py` | C | Scenario spine validation; imports replay projection | **Validation tooling** |
| `tools/final_emission_ownership_audit.py` | C | Advisory ownership drift scan | **Audit tooling** |
| `tools/realization_provenance_audit.py` | C | Provenance gap reports | **Audit tooling** |

---

## G. Direct-owner test suites (fallback-themed)

| File | Fallback role | Asserts |
|------|---------------|---------|
| `tests/test_diegetic_fallback_narration.py` | Diegetic content | Template metadata, render lines |
| `tests/test_final_emission_opening_fallback.py` | Opening selection | Meta composition, fail-closed, no local compose |
| `tests/test_final_emission_sealed_fallback.py` | Sealed selection | Route meta, provider assembly |
| `tests/test_final_emission_visibility_fallback.py` | Visibility routing | Candidate order, owner buckets |
| `tests/test_final_emission_fast_fallback_composition.py` | Fast-fallback composition | Neutral composition layer |
| `tests/test_fallback_behavior_gate.py` | Fallback-behavior at gate | Contract activation at gate |
| `tests/test_fallback_behavior_repairs.py` | Fallback-behavior repairs | Repair layer semantics |
| `tests/test_fallback_behavior_validator.py` | Fallback-behavior validation | Validator verdicts |
| `tests/test_fallback_shipped_contract_propagation.py` | Shipped contract propagation | Policy → prompt path |
| `tests/test_fallback_overwrite_containment.py` | Provenance containment | Fast-fallback overwrite guards |
| `tests/test_fallback_continuity_guard.py` | Continuity guard | Diegetic continuity |
| `tests/test_opening_fallback_owner_bucket.py` | Owner buckets | Read-side bucket mapping |
| `tests/test_upstream_fast_fallback_block_l.py` | Upstream fast fallback | API/retry provenance |
| `tests/test_strict_social_emergency_fallback_dialogue.py` | Strict-social emergency | Social content path |
| `tests/test_social_fallback_leak_containment.py` | Social leak containment | Repair consumer |
| `tests/test_golden_replay_fallback_projection.py` | Replay projection | Protected fallback fields |
| `tests/test_golden_replay_projection.py` | Full projection surface | Observation paths |
| `tests/test_golden_replay.py` | Protected replay scenarios | End-to-end authorship/buckets |
| `tests/test_final_emission_meta.py` | FEM + lineage | Split-owner lineage shape |
| `tests/test_emergency_fallback_registry_static_drift.py` | Registry drift | Static family registry |
| `tests/test_diegetic_fallback_block4.py` | Block-4 diegetic | Global anchor fallback |
| `tests/test_lead_npc_payoff_and_fallback.py` | Lead NPC payoff | Integration fallback |
| `tests/test_retry_social_fallback_block3_scope.py` | Retry social scope | Retry boundary |
| `tests/test_ownership_registry.py` | Governance | BA-7 gate/projection import fences |

**Additional downstream consumers (partial list):** 80+ test modules grep-match `fallback`; most are integration/transcript/regression consumers rather than semantic owners.

---

## H. Emission paths (fallback touch without owning selection)

| File | Fallback role |
|------|---------------|
| `game/final_emission_fem_assembly.py` | FEM assembly; passes through fallback meta |
| `game/final_emission_finalize.py` | Finalize; provenance debug hooks |
| `game/final_emission_contract.py` | Contract surface |
| `game/narrative_authenticity.py` | Meta-fallback voice detection (validator adjacency) |
| `game/narrative_planning.py` | `fallback_opener` planning markers |
| `game/scenario_spine_opening_convergence.py` | Stock fallback hit detection (eval) |
| `game/scenario_spine_eval.py` | Spine eval fallback indicators |
| `game/planner_input_manifest.py` | Manifest classifications |
| `game/planner_ctir_projection.py` | CTIR projection (adjacent) |
| `game/turn_packet.py` | Packet accessors for fallback-shaped debug |

---

## I. Docs & prior-cycle artifacts (reference)

| Path | Notes |
|------|-------|
| `docs/cycles/cycle_ap_fallback_authorship_resolution_recon.md` | Authorship vocabulary recon |
| `docs/cycles/cycle_ab_fallback_topology_collapse_*.md` | Topology collapse |
| `docs/cycles/cycle_am_fallback_adapter_retirement_*.md` | Adapter retirement |
| `docs/cycles/cycle_au_golden_replay_ownership_compression_*.md` | Replay ownership |
| `docs/cycles/cycle_aj_opening_fallback_metadata_consolidation_*.md` | Opening metadata |
| `audits/opening_fallback_surface_inventory_2026-05-11.md` | Historical surface inventory |
| `audits/cycle_au_golden_replay_owner_mapping.md` | Owner mapping |
| `docs/architecture_ownership_ledger.md` | Module ownership declarations |

---

## Summary counts

| Category | Runtime (`game/`) | Tests (`tests/`) | Tools |
|----------|-------------------|------------------|-------|
| Files with `fallback` match | 82 | 120+ | 12 |
| Files with `*fallback*` in name | 12 | 28 | 0 |
| Core tier-A owners | 10 | 3 (projection) | 0 |

**Observed concentration:** Fallback behavior spans **10 tier-A runtime modules** but **visibility + meta + diegetic** account for the majority of cross-cutting imports and commit co-touch.
