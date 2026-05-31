# Cycle AD — Test Authority Consolidation Recon

**Date:** 2026-05-31  
**Scope:** Recon only — no test or production changes.  
**Ground truth:** Live `pytest --collect-only` → **4297 tests** in **306** `tests/test_*.py` modules; **18** governed responsibility groups in `tests/test_ownership_registry.py`. Inventory snapshot in `tests/test_inventory.json` may be stale (`generated_utc`: 2026-04-25 per Cycle R notes) — regenerate via `py -3 tools/test_audit.py` before per-file inventory work.

**Relationship to prior work:** Cycle R (2026-05-30) thinned fanout and extracted `tests/helpers/final_emission_gate_fixtures.py`. Cycle AD focuses on **assertion authority boundaries** — who owns full invariants vs integration-visible smoke vs replay observation — and where downstream suites still restate owner matrices.

---

## Current Test Surface

### Totals

| Metric | Value |
| --- | --- |
| Test modules (`tests/test_*.py`) | **306** |
| Collected tests (live) | **4297** |
| Helper modules (`tests/helpers/*.py`) | **32** |
| Registry direct-owner groups | **18** |
| Test-to-test imports (anti-pattern) | **25** import edges across **22** consumer files |

### Major clusters (heuristic filename grouping)

| Cluster | Module count | Notes |
| --- | ---: | --- |
| other / misc | 112 | Outside filename heuristics; includes engine, API, lint, eval tooling |
| social / dialogue / speaker | 33 | Strict-social, speaker contract, dialogue plan blocks |
| narrative / planner | 30 | Prompt context, CTIR, narrative planning |
| fallback / retry | 22 | Upstream fast fallback, retry regressions, diegetic fallback |
| final_emission / gate | 18 | Gate orchestration, validators, repairs, visibility, meta |
| world / scene | 17 | Scene graph, transitions, entity lock |
| leads | 16 | Lead lifecycle, NPC payoff, relations |
| harness / transcript / gauntlet | 15 | Golden replay, synthetic, playability, transcript |
| validation layer | 14 | Validation contracts, closeout, audit smoke |
| prompt / guard | 9 | Pre-GM guard, retry prompts |
| ownership / registry | 6 | `test_ownership_registry.py`, validation coverage registry |
| provenance / lineage / telemetry | 6 | Runtime lineage, realization provenance, stage diff |
| combat | 4 | Combat resolution |
| clues | 3 | Clue discovery, idempotence |
| replay / golden (filename-only) | 1 | `test_golden_replay.py` (also counted under harness) |

### Top 20 largest test files (by line count)

| Lines | Assert signals* | File |
| ---: | ---: | --- |
| 6715 | 915 | `tests/test_final_emission_gate.py` |
| 3387 | 434 | `tests/test_prompt_context.py` |
| 2899 | 476 | `tests/test_golden_replay.py` |
| 2294 | 281 | `tests/test_social_exchange_emission.py` |
| 2140 | 333 | `tests/test_turn_pipeline_shared.py` |
| 1856 | 232 | `tests/test_prompt_and_guard.py` |
| 1725 | 47 | `tests/test_synthetic_smoke.py` |
| 1611 | 57 | `tests/test_narration_transcript_regressions.py` |
| 1477 | 206 | `tests/test_failure_classifier.py` |
| 1376 | 225 | `tests/test_run_scenario_spine_validation.py` |
| 1371 | 126 | `tests/test_final_emission_visibility_fallback.py` |
| 1224 | 138 | `tests/test_social_lead_landing.py` |
| 1108 | 255 | `tests/test_final_emission_meta.py` |
| 1059 | 139 | `tests/test_transcript_regression.py` |
| 1029 | 118 | `tests/test_api_narration_path_selection.py` |
| 967 | 233 | `tests/test_final_emission_visibility.py` |
| 949 | 118 | `tests/test_scene_transition_authority.py` |
| 907 | 171 | `tests/test_social.py` |
| 903 | 108 | `tests/test_answer_completeness_rules.py` |
| 869 | 107 | `tests/test_scene_destination_binding.py` |

\*Assert signals = `assert` statements + `assert_*` helper calls + `pytest.raises(` (approximate density metric).

### Top 20 assertion-dense files (by total assert signals)

| Asserts | Density (/100 lines) | Lines | File |
| ---: | ---: | ---: | --- |
| 915 | 13.6 | 6715 | `tests/test_final_emission_gate.py` |
| 476 | 16.4 | 2899 | `tests/test_golden_replay.py` |
| 434 | 12.8 | 3387 | `tests/test_prompt_context.py` |
| 333 | 15.6 | 2140 | `tests/test_turn_pipeline_shared.py` |
| 281 | 12.2 | 2294 | `tests/test_social_exchange_emission.py` |
| 255 | 23.0 | 1108 | `tests/test_final_emission_meta.py` |
| 233 | 24.1 | 967 | `tests/test_final_emission_visibility.py` |
| 232 | 12.5 | 1856 | `tests/test_prompt_and_guard.py` |
| 225 | 16.4 | 1376 | `tests/test_run_scenario_spine_validation.py` |
| 206 | 13.9 | 1477 | `tests/test_failure_classifier.py` |
| 171 | 18.9 | 907 | `tests/test_social.py` |
| 165 | 22.7 | 727 | `tests/test_post_gm_adoption_gateway.py` |
| 148 | 22.8 | 650 | `tests/test_output_sanitizer.py` |
| 147 | 16.9 | 868 | `tests/test_intent_parser.py` |
| 146 | 19.2 | 761 | `tests/test_exploration_resolution.py` |
| 140 | 21.2 | 661 | `tests/test_world_updates_and_clue_normalization.py` |
| 139 | 13.1 | 1059 | `tests/test_transcript_regression.py` |
| 138 | 11.3 | 1224 | `tests/test_social_lead_landing.py` |
| 131 | 20.6 | 636 | `tests/test_manual_gauntlet_report.py` |
| 126 | 9.2 | 1371 | `tests/test_final_emission_visibility_fallback.py` |

### Helpers imported most often (cross-file reuse)

| Import count | Helper module | Distinct consumer files |
| ---: | --- | ---: |
| 17 | `tests/helpers/ctir_narration_bundle.py` | 17 |
| 15 | `tests/helpers/final_emission_gate_fixtures.py` | 15 |
| 8 | `tests/helpers/transcript_runner.py` | 8 |
| 8 | `tests/helpers/dialogue_social_plan.py` | 8 |
| 7–8 | `tests/helpers/opening_fallback_evidence.py` | 7 |
| 6 | `tests/helpers/objective7_referent_fixtures.py` | 6 |
| 3 | `tests/helpers/emission_smoke_assertions.py` | 3 |

**Repeated import pattern:** CTIR narration bundle helper (`ensure_narration_plan_bundle_for_manual_ctir_tests`) appears in 17 planner/prompt-context tests — already centralized; risk is **scenario-specific overrides** re-inlined beside the helper rather than competing definitions.

---

## Duplicate Assertion Clusters

| Invariant | Current Files | Probable Owner | Downstream / Smoke Candidates | Duplication Type | Consolidation Risk | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **`apply_final_emission_gate` orchestration + layer order** | `test_final_emission_gate.py`, private step probes in block S/T/U, `test_fallback_behavior_gate.py` | `test_final_emission_gate.py` (registry) | `test_final_emission_boundary_convergence.py` (smoke), block S/T/U equivalence | Partial — convergence tests call public gate only | **High** if step-order asserts removed from owner | Gate file is 6715 lines / 915 asserts; owner must stay intact |
| **FEM `final_route` exact value (`replaced`, `accept_candidate`)** | `test_final_emission_gate.py` (25+), `test_final_emission_meta.py` (14), `test_social_exchange_emission.py`, `test_answer_completeness_rules.py` (5), `test_response_delta_requirement.py`, `test_c4_narrative_mode_live_pipeline.py`, `test_diegetic_fallback_narration.py`, `test_interaction_continuity_repair.py`, `test_golden_replay.py`, `test_narration_transcript_regressions.py`, `test_run_scenario_spine_validation.py` | Gate for orchestration semantics; `test_final_emission_meta.py` for read/normalize | Completeness, response-delta, C4 pipeline, continuity repair, turn-packet integration | Partial — downstream restates exact route where branch is not under test | **Medium** | Downstream should use `assert_final_route_replaced_or_not_accept` from `emission_smoke_assertions.py` unless testing a distinct branch |
| **Global visibility stock ban (`for a breath, the scene holds`)** | `test_final_emission_visibility.py`, `test_output_sanitizer.py`, `test_turn_pipeline_shared.py`, `test_social_exchange_emission.py`, `helpers/emission_smoke_assertions.py` | Visibility semantics: `test_final_emission_visibility.py`; string cleanup: `test_output_sanitizer.py` | `test_turn_pipeline_shared.py` (HTTP smoke via helper) | Partial — pipeline uses shared helper; social_exchange still inlines | **Low–Medium** | Pipeline already delegates to `assert_global_visibility_stock_absent` |
| **Scaffold label leak (`planner:`, `validator:`, `router`)** | `test_output_sanitizer.py`, `test_turn_pipeline_shared.py`, `helpers/emission_smoke_assertions.py`, golden replay projection | `test_output_sanitizer.py` | Turn pipeline HTTP smoke | Partial — helper centralizes 3 checks; sanitizer owns full matrix | **Low** | Extend smoke helper use; do not remove sanitizer phrase tables |
| **Unresolved-answer stock phrases** | `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `helpers/emission_smoke_assertions.py` | `test_social_exchange_emission.py` (legality) + sanitizer (string) | Turn pipeline | Partial | **Low** | `truth is still buried beneath rumor and rain` only in social_exchange + turn_pipeline helper |
| **Procedural phrase bans (`state exactly what you do`, `nothing in the scene points`, `no answer presents itself`)** | `test_output_sanitizer.py`, `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py`, `test_broad_address_social_bid.py`, transcript modules | `test_output_sanitizer.py` | Social emission (application paths), pipeline HTTP | Partial — social owner checks player-facing legality on strict-social paths | **Medium** | Intentional overlap where route differs (unit vs application vs HTTP); narrow pipeline to smoke |
| **`response_delta_unsatisfied_at_boundary_no_reorder`** | `test_response_delta_requirement.py`, `test_final_emission_boundary_convergence.py`, `helpers/emission_smoke_assertions.py` | `test_response_delta_requirement.py` (registry downstream of gate) | Boundary convergence smoke | Exact via `assert_response_delta_boundary_validate_only` | **Low** | Helper already exists (Cycle AE3) |
| **Answer completeness / response-delta + `final_route`** | `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_social_exchange_emission.py` | Social emission + gate for legality; completeness file for delta semantics | Registry lists both as gate downstream consumers | Partial — completeness tests lock `final_route == "replaced"` while primary concern is delta fields | **Medium** | Thin to delta/completeness fields; route → smoke helper |
| **Opening fallback source `opening_deterministic_fallback`** | `test_final_emission_gate.py`, `test_final_emission_meta.py`, `test_final_emission_opening_fallback.py`, `test_final_emission_visibility_fallback.py`, `test_upstream_response_repairs.py`, `test_diegetic_fallback_narration.py`, `test_golden_replay.py`, `test_failure_classifier.py`, `test_run_scenario_spine_validation.py`, `test_api_narration_path_selection.py` | Gate (selection/orchestration); upstream repairs (packaging); meta (projection) | Replay, classifier, API narration path | Partial — different layers assert different fields | **Medium** | Fixtures in `opening_fallback_evidence.py` + `final_emission_gate_fixtures.py`; avoid prose re-lock in downstream |
| **`EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` canonical prose** | `helpers/final_emission_gate_fixtures.py`, `test_final_emission_gate.py`, consumers via fixture import (golden, upstream repairs, API narration, run_scenario_spine) | Gate + fixture module (support residue) | Golden replay, scenario spine validation | Exact text lock in one constant | **Low** (already extracted) | Changing constant breaks 6+ files — document as shared contract pin |
| **`opening_fallback_owner_bucket` projection** | `test_opening_fallback_owner_bucket.py`, `test_final_emission_meta.py`, `test_failure_classifier.py`, `test_failure_dashboard_controlled_failures.py`, `test_golden_replay.py`, `test_failure_classification_contract.py`, `helpers/golden_replay_projection.py` | `test_opening_fallback_owner_bucket.py` (read mapping); meta for normalization | Classifier, dashboard, golden replay | **Intentional candidate** — cross-layer contract locks | **High** if removed from replay/classifier | Module docstring explicitly marks replay/dashboard locks as intentional |
| **`sealed_fallback_owner_bucket` / visibility fallback buckets** | `test_final_emission_visibility.py`, `test_final_emission_meta.py`, `helpers/final_emission_gate_fixtures.py` (`assert_sealed_fallback_owner_bucket`), `helpers/golden_replay_projection.py`, `helpers/failure_classifier.py` | Visibility + meta | Golden replay, classifier | Partial — gate fixture helper duplicates meta assertions | **Medium** | Prefer meta owner for projection tables; visibility keeps semantic classification |
| **Repair tag `final_emission_gate_replaced`** | `test_final_emission_gate.py`, `test_final_emission_visibility.py`, `test_final_emission_visibility_fallback.py`, `test_interaction_continuity_repair.py`, `test_turn_pipeline_shared.py` | Gate | Pipeline, continuity, visibility integration | Partial | **Low–Medium** | Pipeline uses `assert_emission_repair_evidence` helper |
| **`question_resolution_rule_check` legality table** | `test_social_exchange_emission.py` (large), `test_prompt_and_guard.py` (smoke), `test_broadcast_open_call_social.py`, `test_turn_pipeline_shared.py` | `test_social_exchange_emission.py` | Broadcast, prompt/guard smoke | Partial — broadcast calls checker directly | **Medium** | Broadcast → outcome smoke (`ok` + one reason code) |
| **Golden replay observation / `golden_text_hash` / drift** | `test_golden_replay.py`, `helpers/golden_replay.py`, `helpers/golden_replay_projection.py`, `test_failure_dashboard_controlled_failures.py` | `test_golden_replay.py` + projection helpers | Dashboard controlled failures | **Intentional candidate** — replay protection | **High** | Do not thin golden replay structural invariants |
| **Runtime lineage / provenance telemetry** | `test_runtime_lineage_telemetry.py`, `test_final_emission_meta.py`, `test_golden_replay.py`, `test_failure_classifier.py`, `test_observational_telemetry_confidence.py`, `test_run_scenario_spine_validation.py`, `helpers/runtime_lineage_reporting.py` | `test_runtime_lineage_telemetry.py` + meta read path | Golden, classifier, scenario spine | Partial | **Medium** | Classifier consumes lineage for diagnostics — intentional |
| **Realization provenance audit fields** | `test_realization_provenance.py`, `test_realization_provenance_audit.py`, `test_realization_authority.py`, `test_realization_layer_audit.py` | `test_realization_provenance.py` | Audit/layer tests | Partial | **Low** | Orthogonal audit surfaces |
| **Ownership registry governance** | `test_ownership_registry.py`, `test_test_audit_tool.py`, `test_architecture_audit_tool.py`, `test_gate_convergence_closeout.py`, `test_state_authority.py` | `test_ownership_registry.py` | Audit tools | Exact for registry rows | **High** if registry tests weakened | Machine-checked direct_owner uniqueness |

### Useful grep anchors

```text
# final_route replaced locks (sample)
rg 'final_route.*replaced|get\("final_route"\).*replaced' tests/

# response-delta boundary reason
rg 'response_delta_unsatisfied_at_boundary_no_reorder' tests/

# opening fallback owner bucket (intentional cross-layer)
rg 'opening_fallback_owner_bucket|sealed_fallback_owner_bucket' tests/

# visibility stock ban
rg 'for a breath, the scene holds|assert_global_visibility_stock' tests/

# test-to-test imports (authority ambiguity)
rg 'from tests\.test_|import tests\.test_' tests/
```

---

## Helper Ownership Clusters

| Helper / Fixture | Defined In | Used By (representative) | Probable Owner | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- |
| **`runner_strict_bundle`, `opening_gm_output`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK`** | `helpers/final_emission_gate_fixtures.py` | Gate, golden replay, block S/T/U, upstream repairs, API narration, boundary convergence, realization provenance | Gate orchestration (`test_final_emission_gate.py`); fixtures are support residue | **Low** | Already extracted (Cycle R R1). Keep semantic ownership in gate; do not move orchestration asserts into helper |
| **`assert_fallback_owner_bucket`, `assert_visibility_pool`, `assert_sealed_fallback_owner_bucket`** | `helpers/final_emission_gate_fixtures.py` | `test_opening_fallback_owner_bucket.py`, opening fallback tests, visibility fallback | Owner-bucket mapping: `test_opening_fallback_owner_bucket.py`; visibility pool: visibility owner | **Medium** | Split assertion helpers by owner: bucket mapping → colocate with owner-bucket tests or `opening_fallback_evidence.py`; visibility pool stays visibility-adjacent |
| **`successful_opening_fem_meta`, `fail_closed_opening_fem_meta`, observed field builders** | `helpers/opening_fallback_evidence.py` | Gate, meta, golden, classifier, dashboard, scenario spine | FEM evidence shape: meta + opening owner-bucket | **Low** | Prefer helper over inline FEM dicts in downstream tests |
| **`assert_player_text_present`, `assert_no_internal_scaffold_labels`, `assert_emission_repair_evidence`, `assert_response_delta_boundary_validate_only`, `assert_final_route_replaced_or_not_accept`** | `helpers/emission_smoke_assertions.py` | `test_turn_pipeline_shared.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py` | Downstream HTTP/pipeline smoke (documented Cycle AE3) | **Low** | AD-2: migrate remaining inline downstream phrase/route checks to this module |
| **`ensure_narration_plan_bundle_for_manual_ctir_tests`** | `helpers/ctir_narration_bundle.py` | 17 planner/prompt-context tests | Planner prompt bundle (`test_prompt_context.py` / structural readiness owner) | **Low** | Already canonical; audit for local CTIR shell duplicates in `test_planner_input_manifest_ctir.py`, C4 pipeline |
| **`make_valid_dialogue_social_plan`, attach helpers** | `helpers/dialogue_social_plan.py` | Dialogue plan blocks, strict-social, golden, block S/T/U | `test_dialogue_social_plan.py` | **Low** | Do not re-inline |
| **`project_turn_observation`, `golden_text_hash`, drift buckets** | `helpers/golden_replay_projection.py` | `test_golden_replay.py`, failure dashboard | Golden replay | **High** | Do not merge into gate fixtures |
| **`classify_replay_failure`, row validation** | `helpers/failure_classifier.py` | `test_failure_classifier.py`, golden replay | Failure classifier owner | **Low** | Preserve classifier ≠ dashboard split |
| **`build_runtime_lineage_summary`, lineage reporting** | `helpers/runtime_lineage_reporting.py` | `test_runtime_lineage_telemetry.py`, golden, scenario spine | Runtime lineage telemetry owner | **Low** | Extend rather than duplicate lineage summaries in tests |
| **`minimal_full_referent_artifact`, `referent_compact_mirror`** | `helpers/objective7_referent_fixtures.py` | Gate, validators, prompt context, referent clarity tests | `test_referent_tracking.py` / RT7-R split | **Low** | Orthogonal seams — do not merge |
| **`_response_type_contract` (local)** | `test_fallback_behavior_gate.py`, `test_fallback_behavior_repairs.py` | Same two files only | Fallback behavior gate/repairs owners | **Medium** | Extract to shared helper or `final_emission_gate_fixtures.response_type_contract` (already exists) — remove duplicate local defs |
| **Test-to-test imports (e.g. `_chat`, seeds from `test_turn_pipeline_shared`)** | Various test modules | 22 files import from other test modules | Should be helper-owned | **Medium–High** | AD-1: extract imported symbols to `tests/helpers/` — see list below |

### Test-to-test import edges (consolidation targets)

| Consumer | Imports from | Likely extraction target |
| --- | --- | --- |
| `test_playability_smoke.py`, `test_start_campaign_api.py`, `test_manual_play_latency.py`, `test_empty_social_retry_regressions.py`, `test_new_campaign_silent_reset_nc2.py`, `test_opening_start_seam_regressions.py`, `test_turn_trace_contract.py` | `test_turn_pipeline_shared` | `tests/helpers/turn_pipeline_http_fixtures.py` |
| `test_golden_replay.py`, `test_block_t_*`, `test_block_u_*` | `test_block_s_speaker_local_rebind_equivalence` | `tests/helpers/speaker_equivalence_harness.py` (extend existing shadow harness) |
| `test_narration_transcript_regressions.py` | `test_turn_pipeline_shared`, `test_fallback_behavior_gate` | Transcript + fallback HTTP fixtures |
| `test_answer_completeness_rules.py`, `test_strict_social_answer_pressure_cashout.py` | `test_social_escalation` | Social escalation fixture helper |
| `test_final_emission_gate.py`, `test_final_emission_boundary_no_semantic_repair.py`, `test_c4_narrative_mode_live_pipeline.py` | `test_narrative_mode_output_validator` | Narrative mode validator stubs helper |
| `test_gauntlet_regressions.py` | gate test functions | Already partially fixed via `run_strict_social_motive_overclaim_gate_case` in fixtures |

---

## Boundary Proposal

| Subsystem / Invariant | Owner Test | Downstream Tests | Smoke Tests | Candidate Reductions |
| --- | --- | --- | --- | --- |
| Final emission gate orchestration | `test_final_emission_gate.py` | `test_interaction_continuity_repair.py`, `test_diegetic_fallback_narration.py`, block S/T/U (equivalence only) | `test_final_emission_boundary_convergence.py` | None in gate owner; downstream may drop private step imports |
| FEM read/projection/normalize | `test_final_emission_meta.py` | `test_turn_packet_stage_diff_integration.py`, classifier rows | Meta unit tests in meta file | Duplicate projection tables in visibility file → mapping smoke only |
| Visibility fallback semantics | `test_final_emission_visibility.py` | `test_turn_pipeline_shared.py` (HTTP) | `assert_global_visibility_stock_absent` | Visibility file: keep semantics; thin FEM route smoke to helper |
| Opening owner-bucket read mapping | `test_opening_fallback_owner_bucket.py` | Classifier, dashboard, golden (observation) | `assert_fallback_owner_bucket` helper | **No reduction** in golden/classifier — intentional candidate |
| Output sanitizer phrase matrix | `test_output_sanitizer.py` | `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py` | `emission_smoke_assertions` scaffold checks | Pipeline: one smoke per route class for phrase bans |
| Strict-social emission legality | `test_social_exchange_emission.py` | `test_answer_completeness_rules.py`, `test_response_delta_requirement.py` | `test_prompt_and_guard.py`, C4 pipeline | Broadcast open-call: thin direct `question_resolution_rule_check` table |
| Response delta / completeness | `test_response_delta_requirement.py`, `test_answer_completeness_rules.py` | Gate integration paths | C4 narrative-mode pipeline | Replace exact `final_route` locks with smoke helper where delta is primary |
| Golden replay observation | `test_golden_replay.py` | Failure dashboard controlled failures | Scenario spine structural smoke | **No reduction** |
| Failure classifier routing | `test_failure_classifier.py` | Dashboard, golden replay hooks | Classification contract | **No reduction** of FEM bucket validation |
| Runtime lineage telemetry | `test_runtime_lineage_telemetry.py` | Golden, scenario spine, meta | Observational confidence smoke | Downstream: presence/summary only unless testing lineage semantics |
| Ownership registry | `test_ownership_registry.py` | `test_test_audit_tool.py` | Gate convergence closeout | **No reduction** |
| Turn pipeline HTTP orchestration | — (no single owner; integration harness) | `test_turn_pipeline_shared.py` | Playability smoke, API tests importing its fixtures | Contraction: dedupe phrase/route asserts via `emission_smoke_assertions`; extract shared HTTP fixtures |
| CTIR / prompt context bundle | `test_prompt_context.py` | Many CTIR consumption tests | Plan-only convergence smoke | Keep CTIR helper; avoid second CTIR shell helpers |
| Registry governance (Objective #12) | `test_validation_coverage_registry.py` | Audit CLI tools | — | Orthogonal to emission authority |

---

## Test Run Report

**Command:**

```powershell
py -3 -m pytest tests/test_ownership_registry.py tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_final_emission_visibility.py tests/test_opening_fallback_owner_bucket.py tests/test_golden_replay.py tests/test_response_delta_requirement.py tests/test_answer_completeness_rules.py tests/test_turn_pipeline_shared.py tests/test_failure_classifier.py tests/test_runtime_lineage_telemetry.py tests/test_realization_provenance.py tests/test_final_emission_opening_fallback.py tests/test_final_emission_boundary_convergence.py tests/test_social_exchange_emission.py tests/test_output_sanitizer.py -q --tb=line
```

| Metric | Result |
| --- | --- |
| Tests collected | **809** |
| Outcome | **PASS** (all) |
| Failures | None |
| Runtime | **~24 s** (wall clock) |

**Not run:** Full 4297-test suite (deferred — subset covers registry, gate, meta, visibility, opening fallback, golden replay, downstream consumers, classifier, lineage, provenance, social emission legality, sanitizer).

**Suggested fast loop for implementation blocks:**

```powershell
py -3 -m pytest tests/test_ownership_registry.py -q
py -3 -m pytest tests/helpers/ -q   # if helper-only changes
# + affected owner module from table above
```

---

## Recommended Implementation Blocks

### AD-1: Lowest-risk helper consolidation

| Field | Detail |
| --- | --- |
| **Target files** | `test_fallback_behavior_gate.py`, `test_fallback_behavior_repairs.py` (dedupe `_response_type_contract` → use `final_emission_gate_fixtures.response_type_contract`); `test_turn_pipeline_shared.py` + 7 consumers (extract HTTP/chat fixtures from test-to-test imports) |
| **Intended changes** | Import-only moves; replace local `_response_type_contract` with shared helper; create `tests/helpers/turn_pipeline_http_fixtures.py` for symbols currently imported from `test_turn_pipeline_shared` |
| **Tests to run** | `test_fallback_behavior_gate.py`, `test_fallback_behavior_repairs.py`, `test_turn_pipeline_shared.py`, `test_playability_smoke.py`, `test_start_campaign_api.py` |
| **Risk** | **Low** |
| **Parallel with** | AD-3 (registry doc updates) |

### AD-2: Duplicate downstream assertion thinning

| Field | Detail |
| --- | --- |
| **Target files** | `test_turn_pipeline_shared.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_interaction_continuity_repair.py`, `test_broadcast_open_call_social.py`, `test_c4_narrative_mode_live_pipeline.py` |
| **Intended changes** | Replace inline `final_route == "replaced"` with `assert_final_route_replaced_or_not_accept` where branch is not under test; replace duplicate phrase bans with `emission_smoke_assertions` calls; broadcast social → `question_resolution_rule_check` outcome smoke only |
| **Tests to run** | AD subset command above (809 tests) |
| **Risk** | **Medium** — must preserve distinct branch coverage |
| **Parallel with** | AD-1 after fixtures extracted |

### AD-3: Owner/downstream/smoke formalization

| Field | Detail |
| --- | --- |
| **Target files** | `tests/test_ownership_registry.py` (extend `downstream_consumer_suites` / smoke notes), `tests/README_TESTS.md`, `tests/TEST_AUDIT.md`, module docstrings in `test_turn_pipeline_shared.py`, `test_answer_completeness_rules.py`, `helpers/emission_smoke_assertions.py` |
| **Intended changes** | Document allowed assertion depth per neighbor field; add `opening_fallback_owner_bucket` and golden replay as explicit **intentional candidate** overlaps; regenerate `test_inventory.json` |
| **Tests to run** | `test_ownership_registry.py`, `test_test_audit_tool.py`, `py -3 tools/test_audit.py` |
| **Risk** | **Low** (docs + registry metadata only) |
| **Parallel with** | AD-1 |

### AD-4: Cleanup/deletion pass (owner-protected only)

| Field | Detail |
| --- | --- |
| **Target files** | Parametrized duplicate blocks in `test_turn_pipeline_shared.py`; redundant FEM dict literals in classifier/dashboard tests already covered by `opening_fallback_evidence.py`; optional contraction in `test_final_emission_visibility.py` FEM smoke |
| **Intended changes** | Delete only after AD-2 smoke helpers prove equivalent; **never** touch `@pytest.mark.golden_replay` items or classifier bucket contracts |
| **Tests to run** | Full AD subset + `pytest -m golden_replay` |
| **Risk** | **Medium–High** |
| **Parallel with** | **No** — run after AD-2 verification |

---

## Files to Pass Back to ChatGPT

Prioritized for follow-up planning and implementation:

1. **This recon:** `cycle_ad_test_authority_consolidation_recon_2026-05-31.md`
2. **Governance anchor:** `tests/test_ownership_registry.py`, `tests/README_TESTS.md`, `tests/TEST_AUDIT.md`
3. **Top duplicate-assertion owners:** `tests/test_final_emission_gate.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_golden_replay.py`, `tests/test_social_exchange_emission.py`, `tests/test_final_emission_meta.py`, `tests/test_final_emission_visibility.py`, `tests/test_answer_completeness_rules.py`, `tests/test_response_delta_requirement.py`
4. **Helper/fixture modules:** `tests/helpers/final_emission_gate_fixtures.py`, `tests/helpers/opening_fallback_evidence.py`, `tests/helpers/emission_smoke_assertions.py`, `tests/helpers/golden_replay_projection.py`, `tests/helpers/failure_classifier.py`, `tests/helpers/ctir_narration_bundle.py`
5. **Intentional-overlap / high-risk (do not thin blindly):** `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_failure_dashboard_controlled_failures.py`
6. **Test-to-test import hubs:** `tests/test_turn_pipeline_shared.py`, `tests/test_block_s_speaker_local_rebind_equivalence.py`
7. **Prior Cycle R context:** `tests/cycle_r_test_fanout_reduction_recon_2026-05-30.md`, `tests/cycle_r_block_r1a_fixture_dependency_map_2026-05-30.md`

---

## Summary

The suite is **governed at the seam level** (18 registry groups) but **~288 modules sit outside direct registry ownership**, many asserting downstream outcomes through HTTP, replay, and transcript harnesses. The highest authority ambiguity concentrates in:

1. **`test_turn_pipeline_shared.py`** — mixes routing, continuity, sanitizer phrase bans, and FEM fields (333 asserts); partially mitigated by `emission_smoke_assertions.py` but still a second home for legality signals.
2. **`test_final_emission_gate.py`** — correct owner but oversized (6715 lines); fixtures already extracted; orchestration asserts must not move downstream.
3. **Cross-layer FEM bucket / opening fallback fields** — duplicated across owner-bucket tests, meta, classifier, and golden replay; **marked intentional** where replay/diagnostics require observation locks.
4. **25 test-to-test imports** — obscure helper ownership and create pytest collection coupling.

Cycle AD can proceed safely in **four small blocks**: helper import cleanup (AD-1), downstream thinning via existing smoke helpers (AD-2), registry/doc formalization (AD-3), and owner-protected deletion only after verification (AD-4). No production changes required; no tests deleted in this recon pass.
