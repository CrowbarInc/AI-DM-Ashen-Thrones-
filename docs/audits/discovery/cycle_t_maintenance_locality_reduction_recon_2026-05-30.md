# Cycle T — Maintenance Locality Reduction Recon

Date: 2026-05-30  
Scope: Repository reconnaissance only. No runtime, test, fixture, snapshot, or CI behavior changes were made.

## Executive Summary

In the last 30 commits, **23 of 30 (77%)** touch **8+ files** by raw git path count. Raw metrics are skewed by bundled audit/docs/artifact paths (notably `29da646` at 267 files, almost entirely tracked hygiene artifacts). Using Cycle F “true source fanout” rules (`game/**`, `tests/**`, `tools/**`, `.github/**`, `pytest.ini`; excluding `docs/**`, `audits/**`, `artifacts/**`, `*.md`, `data/session*`, `data/combat*`), the picture is still broad but more actionable:

| Metric | Raw (all paths) | Source-only |
| --- | ---: | ---: |
| Median files/commit | 15.5 | 8.0 |
| Mean files/commit | 23.7 | 9.3 |
| Max files/commit | 267 | 35 |
| Commits ≥ 8 files | 23 | 16 |

The dominant fanout cluster is **golden replay + failure classification + final emission meta/gate observability**. Six files appear in **10+ commits** within this window: `tests/test_golden_replay.py` (16), `tests/helpers/golden_replay.py` (12), `tests/helpers/failure_dashboard_report.py` (10), `tests/test_final_emission_gate.py` (10), `game/final_emission_meta.py` (9), `tests/test_failure_classifier.py` (9).

Cycle T should prioritize **branch-local helpers and fixture factories** that absorb repeated projection/assertion/manifest edits—not further gate extraction unless a block is explicitly scoped to one runtime cluster.

---

## 1. Git Fanout Summary

Analysis command: `git log --name-only --pretty=format:'---COMMIT--- %h %s' -n 30`

### Aggregate statistics (raw)

- **Median files touched:** 15.5
- **Average files touched:** 23.7
- **Max files touched:** 267 (`29da646`)
- **Commits touching 8+ files:** 23 / 30

### Aggregate statistics (source-only, Cycle F counting rules)

- **Median:** 8.0 | **Mean:** 9.3 | **Max:** 35 (`673118e`) | **≥8:** 16 / 30

### Per-commit inventory (newest → oldest)

#### `1f4e94e` — Cycle S: Runtime Drift Compression — **12 files** ⚠️ 8+

- `docs/cycles/cycle_s_runtime_drift_compression_recon_2026-05-30.md`
- `docs/cycles/cycle_s_runtime_drift_compression_closure_2026-05-30.md`
- `docs/scenario_spine_validation.md`
- `docs/testing/protected_replay_manifest.md`
- `game/speaker_contract_enforcement.py`
- `tests/conftest.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_runtime_drift_seed_audit.py`
- `tools/compare_scenario_spine_reruns.py`

#### `92f7213` — Cycle U: Sustained Session Validation — **13 files** ⚠️ 8+

- `docs/cycles/cycle_n_block_n1_canonical_20_turn_replay_2026-05-27.md`
- `docs/cycles/cycle_n_block_n3_continuity_drift_bridge_2026-05-27.md`
- `docs/cycles/cycle_n_block_n4_fallback_escalation_guard_2026-05-27.md`
- `docs/cycles/cycle_n_long_session_stability_recon_2026-05-27.md`
- `docs/cycles/cycle_o_final_emission_gate_contraction_recon_2026-05-28.md`
- `docs/cycles/cycle_u_sustained_session_validation_closure_2026-05-30.md`
- `docs/cycles/cycle_u_sustained_session_validation_recon_2026-05-30.md`
- `docs/scenario_spine_validation.md`
- `docs/testing/protected_replay_manifest.md`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tools/run_scenario_spine_validation.py`

#### `6ecb98e` — Cycle Q replay cost compression — **7 files**

- `audits/cycle_q_replay_cost_compression_closure_2026-05-29.md`
- `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md`
- `docs/testing/protected_replay_manifest.md`
- `tests/README_TESTS.md`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`

#### `1c5b9d8` — P: Collapse fallback family ownership ambiguity — **15 files** ⚠️ 8+

- `docs/cycles/cycle_p_fallback_family_collapse_closure_2026-05-29.md`
- `docs/cycles/cycle_p_fallback_family_collapse_recon_2026-05-28.md`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `game/runtime_lineage_telemetry.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_failure_classifier.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_runtime_lineage_telemetry.py`

#### `77faefe` — O: Final Emission Gate Contraction — **9 files** ⚠️ 8+

- `docs/cycles/cycle_o_final_emission_gate_contraction_closure_2026-05-28.md`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `tests/test_final_emission_debt_retirement.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_observational_telemetry_confidence.py`
- `tests/test_run_scenario_spine_validation.py`

#### `3582d48` — Complete Cycle N long-session stability — **5 files**

- `docs/cycles/cycle_n_long_session_stability_closure_2026-05-27.md`
- `docs/testing/protected_replay_manifest.md`
- `tests/README_TESTS.md`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`

#### `76fe80a` — M: Reduce maintenance drag — **15 files** ⚠️ 8+

- `docs/cycles/cycle_m_block_m3_source_attribution_projection_recon_2026-05-27.md`
- `docs/cycles/cycle_m_block_m5_strict_social_boundary_recon_2026-05-27.md`
- `docs/cycles/cycle_m_maintenance_drag_reduction_closure_2026-05-27.md`
- `docs/cycles/cycle_m_maintenance_drag_reduction_recon_2026-05-27.md`
- `game/runtime_lineage_telemetry.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/opening_fallback_evidence.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_runtime_lineage_telemetry.py`
- `tools/run_scenario_spine_validation.py`

#### `f36e834` — Cycle L: Test Ownership Compression — **9 files** ⚠️ 8+

- `docs/cycles/cycle_l_block_l1_opening_adapter_gate_boundary_2026-05-26.md`
- `docs/cycles/cycle_l_block_l2_visibility_fallback_recon_2026-05-26.md`
- `docs/cycles/cycle_l_block_l3_visibility_helper_extraction_assessment_2026-05-26.md`
- `docs/cycles/cycle_l_block_l4_visibility_helper_owner_suite_extraction_2026-05-26.md`
- `docs/cycles/cycle_l_test_ownership_compression_closure_2026-05-27.md`
- `docs/cycles/cycle_l_test_ownership_compression_recon_2026-05-26.md`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_opening_fallback.py`
- `tests/test_final_emission_visibility_fallback.py`

#### `2619bb5` — K: Promote replay acceptance gate — **16 files** ⚠️ 8+

- `.github/workflows/convergence-checks.yml`
- `docs/audits/cycle_k_block_k1_protected_replay_declaration_2026-05-26.md`
- `docs/audits/cycle_k_block_k2_replay_ci_promotion_2026-05-26.md`
- `docs/audits/cycle_k_block_k3_failure_artifact_ergonomics_2026-05-26.md`
- `docs/audits/cycle_k_block_k3a_reporting_bridge_2026-05-26.md`
- `docs/audits/cycle_k_block_k3b_failure_artifact_retention_2026-05-26.md`
- `docs/audits/cycle_k_block_k4_drift_threshold_policy_2026-05-26.md`
- `docs/audits/cycle_k_block_k5_longitudinal_replay_decision_2026-05-26.md`
- `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md`
- `docs/convergence_ci_inventory.md`
- `docs/testing/protected_replay_manifest.md`
- `tests/README_TESTS.md`
- `tests/conftest.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`

#### `6074e9e` — J: Gate Cluster Extraction — **5 files**

- `docs/cycles/cycle_j_gate_cluster_extraction_closure_2026-05-26.md`
- `docs/cycles/cycle_j_gate_cluster_extraction_recon_2026-05-26.md`
- `game/final_emission_gate.py`
- `game/final_emission_opening_fallback.py`
- `tests/test_final_emission_opening_fallback.py`

#### `fd5f1a9` — Cycle I: Contract opening fallback authorship attribution — **16 files** ⚠️ 8+

- `docs/cycles/cycle_i_a_opening_owner_semantics_contract_2026-05-26.md`
- `docs/cycles/cycle_i_fallback_authorship_contraction_closure_2026-05-26.md`
- `docs/cycles/cycle_i_fallback_authorship_recon_2026-05-25.md`
- `game/final_emission_meta.py`
- `game/runtime_lineage_telemetry.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_runtime_lineage_telemetry.py`
- `tools/run_scenario_spine_validation.py`

#### `b086b75` — H: Runtime Lineage Instrumentation — **12 files** ⚠️ 8+

- `docs/cycles/cycle_h_runtime_lineage_closure_2026-05-25.md`
- `docs/cycles/cycle_h_runtime_lineage_instrumentation_recon_2026-05-23.md`
- `game/final_emission_meta.py`
- `game/runtime_lineage_telemetry.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_failure_classifier.py`
- `tests/test_final_emission_meta.py`
- `tests/test_golden_replay.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_runtime_lineage_telemetry.py`
- `tools/run_scenario_spine_validation.py`

#### `6a402d2` — config: lazy-load OpenAI API key for import-safe tests — **9 files** ⚠️ 8+

- `docs/reports/openai_api_key_lazy_config_fix_20260520.md`
- `game/api_upstream_preflight.py`
- `game/config.py`
- `game/gm.py`
- `tests/test_api_upstream_preflight.py`
- `tests/test_model_routing_config.py`
- `tests/test_model_routing_escalation.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_realization_provenance.py`

#### `aa9095a` — test: isolate snapshot helpers from live API imports — **5 files**

- `docs/reports/openai_api_key_ci_import_fix_20260520.md`
- `docs/reports/openai_api_key_ci_import_recon_20260520.md`
- `tests/helpers/transcript_runner.py`
- `tests/helpers/transcript_snapshots.py`
- `tests/test_dead_turn_evaluation_threading.py`

#### `cf6a89c` — ci: update actions for Node 24 runner compatibility — **2 files**

- `.github/workflows/content-lint.yml`
- `.github/workflows/convergence-checks.yml`

#### `90adbbb` — G: Runtime Stability and Full-Suite Hygiene — **22 files** ⚠️ 8+

- 15× `audits/cycle_g_*` validation/debt audit files
- `pytest.ini`
- `tests/README_TESTS.md`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_final_emission_debt_retirement.py`
- `tests/test_narrative_authenticity_eval.py`
- `tests/test_run_scenario_spine_validation.py`
- `tests/test_scene_destination_binding.py`

#### `1ae07ea` — Cycle F: Maintenance Drag Measurement and Opening Routing Closure — **16 files** ⚠️ 8+

- 8× `audits/cycle_f_*` recon/closure files
- `audits/failure_owner_matrix.md`
- `tests/helpers/failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_golden_replay.py`

#### `8ddb183` — E: Test Signal Ownership Thinning — **23 files** ⚠️ 8+

- 10× `audits/cycle_e_*` recon/closure files
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_fallback_behavior_gate.py`
- `tests/test_fallback_behavior_repairs.py`
- `tests/test_fallback_behavior_validator.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_repairs.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_golden_replay.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_upstream_fast_fallback_block_l.py`

#### `6c00e6e` — D: Final Emission Gate Pressure Reduction — **17 files** ⚠️ 8+

- `audits/cycle_d_sealed_fallback_contraction_closure_2026-05-13.md`
- `audits/cycle_d_visibility_fallback_contraction_closure_2026-05-13.md`
- `game/diegetic_fallback_narration.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_golden_replay.py`

#### `a5c9146` — Cycle C: contract fallback ownership and mutation lineage — **18 files** ⚠️ 8+

- 4× `audits/cycle_c_*` / fallback surface inventory files
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/output_sanitizer.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_final_emission_gate.py`
- `tests/test_golden_replay.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_output_sanitizer.py`

#### `98bc059` — Failure Classification Dashboard — **28 files** ⚠️ 8+

- 17× `audits/failure_*` inventory/contract files
- `pytest.ini`
- `tests/README_TESTS.md`
- `tests/conftest.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/golden_replay.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_golden_replay.py`

#### `ac1ba90` — Add Golden Replay Scenario-Spine Baseline Suite — **6 files**

- `audits/golden_replay_baseline_2026-05-11.md`
- `audits/golden_replay_readiness_2026-05-11.md`
- `pytest.ini`
- `tests/README_TESTS.md`
- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`

#### `f04ef66` — Converge evaluator boundaries, telemetry, and governance — **16 files** ⚠️ 8+

- `.github/workflows/convergence-checks.yml`
- 4× `artifacts/*_audit/*.{json,md}`
- 7× `docs/*` convergence/governance docs
- `tests/TEST_AUDIT.md`
- `tools/run_governance_audits.py`

#### `792de85` — Freeze Evaluator Convergence and Boundary Governance — **22 files** ⚠️ 8+

- 7× `docs/*` evaluator/validation docs
- `game/playability_eval.py`
- `game/scenario_spine_eval.py`
- `tests/helpers/behavioral_gauntlet_eval.py`
- `tests/test_architecture_audit_tool.py`
- `tests/test_behavioral_gauntlet_eval.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `tests/test_evaluator_convergence_closeout.py`
- `tests/test_final_emission_meta.py`
- `tests/test_playability_eval.py`
- `tests/test_scenario_spine_eval.py`
- `tests/test_validation_layer_audit_smoke.py`
- `tools/architecture_audit.py`
- `tools/run_playability_validation.py`
- `tools/run_scenario_spine_validation.py`
- `tools/validation_layer_audit.py`

#### `c89f2f4` — Complete Gate Convergence, Semantic Fencing, and Relocation Readiness Hardening — **24 files** ⚠️ 8+

- `docs/gate_cleanup_inventory.md`
- `docs/gate_convergence_closeout.md`
- `game/dialogue_social_plan.py`
- `game/final_emission_boundary_contract.py`
- `game/final_emission_gate.py`
- `game/final_emission_validators.py`
- `game/gm.py`
- `game/speaker_contract_enforcement.py`
- `game/upstream_response_repairs.py`
- `tests/helpers/dialogue_social_plan.py`
- `tests/helpers/post_speaker_finalize_probe.py`
- `tests/helpers/speaker_gate_order.py`
- `tests/helpers/speaker_relocation_shadow_harness.py`
- `tests/test_block_s_speaker_local_rebind_equivalence.py`
- `tests/test_block_t_speaker_relocation_shadow_equivalence.py`
- `tests/test_block_u_finalize_stack_divergence.py`
- `tests/test_dialogue_plan_final_emission_gate.py`
- `tests/test_dialogue_social_plan_block_x_contract_pins.py`
- `tests/test_dialogue_social_plan_block_y.py`
- `tests/test_dialogue_social_plan_block_z.py`
- `tests/test_final_emission_gate.py`
- `tests/test_gate_convergence_closeout.py`
- `tests/test_speaker_contract_enforcement_extraction.py`
- `tests/test_upstream_response_repairs.py`

#### `0f03dd6` — Gate Boundary Convergence and Compatibility Fencing — **18 files** ⚠️ 8+

- 4× `docs/*gate*` / `response_policy*` plans
- `game/api.py`
- `game/final_emission_boundary_contract.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_validators.py`
- `game/gm.py`
- `game/opening_deterministic_fallback.py`
- `game/response_policy_enforcement_manifest.py`
- `game/upstream_response_repairs.py`
- `tests/test_api_narration_path_selection.py`
- `tests/test_diegetic_fallback_narration.py`
- `tests/test_final_emission_gate.py`
- `tests/test_response_policy_enforcement_mutation.py`
- `tests/test_upstream_response_repairs.py`

#### `177099a` — Close Out Realization Failure-Locality — **7 files**

- 4× `artifacts/realization_*_audit/*.{json,md}`
- `docs/realization_cursor_handoff.md`
- `docs/realization_failure_locality_closeout.md`
- `docs/realization_triage_ledger.md`

#### `0f80564` — Realization Layer Failure-Locality Hardening — **36 files** ⚠️ 8+

- 4× `artifacts/realization_*_audit/*.{json,md}`
- `data/scenes/watch_post.json`
- 5× `docs/realization_*` / contract docs
- `game/api.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_validators.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/response_policy_enforcement_manifest.py`
- `game/social_exchange_emission.py`
- `game/upstream_response_repairs.py`
- 10× `tests/test_*` realization/gate/repair suites
- `tools/realization_layer_audit.py`
- `tools/realization_provenance_audit.py`

#### `673118e` — PLANNER: Stabilize Failure Locality Seam — **41 files** ⚠️ 8+

- `.gitignore`
- `data/combat.json`, `data/session.json`, `data/session_log.jsonl`, `data/world.json`
- `data/scenes/frontier_gate.json`, `data/scenes/scene_investigate.json`
- 16× `game/*` planner/gate/prompt modules
- 17× `tests/test_*` planner/prompt/gate regressions
- `tools/_bisect_suite_pollution.py`

#### `29da646` — Adoption Gateway (Finalized) — **267 files** ⚠️ 8+

- **263 paths** under `artifacts/**` (scene_canon_hygiene_runtime snapshots, manual gauntlets, playability validation, architecture audit)
- **4 source paths:** `game/api.py`, `game/gm.py`, `tests/test_post_gm_adoption_gateway.py`, `tests/test_world_updates_and_clue_normalization.py`
- **1 doc:** `docs/citr_post_objective_3_audit.md`

---

## 2. Hotspot File Recurrence

Files touched **3+ times** in the last 30 commits, ranked by frequency.

| Rank | File | Commits | Likely role |
| ---: | --- | ---: | --- |
| 1 | `tests/test_golden_replay.py` | 16 | test |
| 2 | `tests/helpers/golden_replay.py` | 12 | adapter/helper |
| 3 | `tests/helpers/failure_dashboard_report.py` | 10 | adapter/helper |
| 4 | `tests/test_final_emission_gate.py` | 10 | test |
| 5 | `game/final_emission_meta.py` | 9 | runtime gate/orchestration |
| 6 | `tests/test_failure_classifier.py` | 9 | test |
| 7 | `game/final_emission_gate.py` | 8 | runtime gate/orchestration |
| 8 | `tests/test_run_scenario_spine_validation.py` | 7 | test |
| 9 | `tests/test_final_emission_meta.py` | 7 | test |
| 10 | `tests/test_failure_dashboard_controlled_failures.py` | 7 | test |
| 11 | `tests/README_TESTS.md` | 6 | documentation |
| 12 | `tests/helpers/failure_classifier.py` | 6 | adapter/helper |
| 13 | `game/gm.py` | 6 | runtime gate/orchestration |
| 14 | `docs/testing/protected_replay_manifest.md` | 5 | registry/manifest |
| 15 | `tools/run_scenario_spine_validation.py` | 5 | adapter/helper |
| 16 | `tests/failure_classification_contract.py` | 5 | registry/manifest |
| 17 | `tests/test_failure_classification_contract.py` | 5 | test |
| 18 | `game/runtime_lineage_telemetry.py` | 4 | runtime gate/orchestration |
| 19 | `tests/test_runtime_lineage_telemetry.py` | 4 | test |
| 20 | `game/final_emission_validators.py` | 4 | runtime gate/orchestration |
| 21 | `docs/scenario_spine_validation.md` | 3 | documentation |
| 22 | `tests/conftest.py` | 3 | fixture |
| 23 | `tests/test_dead_turn_evaluation_threading.py` | 3 | test |
| 24 | `.github/workflows/convergence-checks.yml` | 3 | registry/manifest |
| 25 | `pytest.ini` | 3 | registry/manifest |
| 26 | `tests/test_diegetic_fallback_narration.py` | 3 | test |
| 27 | `tests/test_final_emission_visibility.py` | 3 | test |
| 28 | `artifacts/realization_layer_audit/*` (json+md) | 3 each | documentation |
| 29 | `artifacts/realization_provenance_audit/*` (json+md) | 3 each | documentation |
| 30 | `game/upstream_response_repairs.py` | 3 | runtime gate/orchestration |
| 31 | `tests/test_upstream_response_repairs.py` | 3 | test |
| 32 | `game/api.py` | 3 | runtime gate/orchestration |

**Observation:** The top 10 hotspots form a closed loop: runtime meta/gate emits observability → golden replay projects it → failure classifier/dashboard consume it → multiple owner tests re-assert the same fields.

---

## 3. Co-Touch Clusters

Clusters appearing together in **3+ commits** (pairs/triples with highest co-occurrence).

### Cluster A — Golden replay acceptance lane (9–12 co-touch commits)

**Files:** `tests/helpers/golden_replay.py` + `tests/test_golden_replay.py` (+ often `tests/helpers/failure_dashboard_report.py`, `tests/test_failure_classifier.py`, `docs/testing/protected_replay_manifest.md`, `tests/README_TESTS.md`)

**Likely maintenance reason:** shared fixture dependency + registry drift + duplicated test setup. Any new protected observation field or drift bucket requires synchronized edits across helper, owner test, manifest doc, and README.

### Cluster B — Failure classification dashboard chain (5–7 co-touch commits)

**Files:** `tests/failure_classification_contract.py` + `tests/helpers/failure_classifier.py` + `tests/helpers/failure_dashboard_report.py` + `tests/test_failure_classifier.py` + `tests/test_failure_dashboard_controlled_failures.py` + `tests/test_golden_replay.py`

**Likely maintenance reason:** registry drift + scattered assertion updates. Contract constants, classifier rules, dashboard rendering, and replay integration tests must stay aligned when a new failure category or owner bucket appears.

### Cluster C — FEM meta / gate / replay projection (5–6 co-touch commits)

**Files:** `game/final_emission_meta.py` + `game/final_emission_gate.py` + `tests/test_final_emission_gate.py` + `tests/test_golden_replay.py` (+ `game/final_emission_replay_projection.py` in P/O cycles)

**Likely maintenance reason:** repeated route/gate ownership update + helper ownership ambiguity. Meta field additions propagate to gate tests, replay projection, and golden expectations separately.

### Cluster D — Runtime lineage telemetry reporting (4 co-touch commits)

**Files:** `game/runtime_lineage_telemetry.py` + `tests/test_runtime_lineage_telemetry.py` + `tests/helpers/failure_dashboard_report.py` + `tools/run_scenario_spine_validation.py` + `tests/test_run_scenario_spine_validation.py`

**Likely maintenance reason:** duplicated test setup. Lineage summarization logic is mirrored in runtime module, dashboard helper, and scenario-spine tool (identified in Cycle M recon).

### Cluster E — Gate convergence seam (3–4 co-touch commits)

**Files:** `game/final_emission_gate.py` + `game/final_emission_validators.py` + `game/gm.py` + `game/upstream_response_repairs.py` + paired `tests/test_*`

**Likely maintenance reason:** legitimate cross-cutting behavior change during gate boundary work; less recurring now but still a risk if new gate branches bypass existing test adapters.

### Cluster F — Scenario spine manifest/doc refresh (5 co-touch commits)

**Files:** `docs/testing/protected_replay_manifest.md` + `docs/scenario_spine_validation.md` + `tests/test_run_scenario_spine_validation.py` + `tools/run_scenario_spine_validation.py`

**Likely maintenance reason:** registry/manifest synchronization bundled with replay/scenario changes.

### Cluster G — Artifact audit regeneration (3 co-touch commits)

**Files:** `artifacts/realization_layer_audit/*` + `artifacts/realization_provenance_audit/*`

**Likely maintenance reason:** documentation/reporting only; pollutes raw fanout metrics but not source fanout.

---

## 4. Fix Fanout Root Causes

Classification of high-fanout commits (source-only ≥ 8 or raw ≥ 15).

| Commit | Source files | Primary root cause |
| --- | ---: | --- |
| `673118e` | 35 | legitimate cross-cutting behavior change (planner seam + many paired tests) |
| `0f80564` | 24 | legitimate cross-cutting behavior change (realization authority seam) |
| `c89f2f4` | 22 | legitimate cross-cutting behavior change (gate convergence + speaker relocation tests) |
| `6c00e6e` | 15 | runtime helper not localized (gate extraction + dashboard/replay cascade) |
| `792de85` | 15 | legitimate cross-cutting behavior change (evaluator boundary freeze) |
| `a5c9146` | 14 | test expectation cascade + registry/manifest synchronization |
| `0f03dd6` | 14 | legitimate cross-cutting behavior change (gate boundary fencing) |
| `1c5b9d8` | 13 | test expectation cascade + runtime helper not localized (fallback family collapse) |
| `fd5f1a9` | 13 | test expectation cascade + registry drift (opening authorship contract) |
| `8ddb183` | 13 | scattered assertion updates (ownership comment/thinning across many test files) |
| `b086b75` | 10 | test expectation cascade (lineage instrumentation → replay/dashboard/tool) |
| `98bc059` | 10 | fixture cascade (foundational dashboard + golden replay introduction) |
| `76fe80a` | 11 | test expectation cascade + duplicated reporting (Cycle M lineage dedup target) |
| `1f4e94e` | 8 | test expectation cascade + manifest refresh (drift compression) |
| `77faefe` | 8 | test expectation cascade (gate contraction → replay/meta tests) |
| `6a402d2` | 8 | runtime helper not localized (config lazy-load ripples through import graph) |
| `1ae07ea` | 7 | scattered assertion updates |
| `90adbbb` | 6 | documentation/reporting only (stored audit txt/md evidence) |
| `2619bb5` | 5 raw / 16 total | documentation/reporting only + registry/manifest synchronization (Cycle K docs dominate) |
| `29da646` | 4 raw / 267 total | fixture cascade (tracked artifact hygiene snapshots; not recurring source pattern) |

### Recurring fanout patterns (by frequency in last 30 commits)

1. **Test expectation cascade (most common):** FEM meta/gate/lineage field change → `golden_replay.py` projection → `failure_classifier.py` rules → 4–6 test files + manifest README updates. Seen in C, D, F, H, I, M, O, P, S, U.
2. **Registry/manifest synchronization:** `failure_classification_contract.py` + classifier + dashboard + `protected_replay_manifest.md` + `tests/README_TESTS.md`. Seen in C, D, K, Q, S, U.
3. **Runtime helper not localized:** Logic duplicated across `failure_dashboard_report.py`, `golden_replay.py`, and `tools/run_scenario_spine_validation.py` for lineage aggregation (Cycle M identified; still co-touched 4×).
4. **Documentation/reporting bundled with behavior:** Cycle closure/recon markdown bundled in same commit as source edits (inflates raw counts; separable by policy).
5. **Legitimate cross-cutting changes:** Gate convergence (`c89f2f4`, `0f03dd6`), planner seam (`673118e`), realization hardening (`0f80564`) — high fanout justified but should not set the baseline expectation for maintenance cycles.

---

## 5. Candidate Locality Reductions

Prioritized small, safe extractions that reduce *future* fanout without changing runtime behavior in the recon pass.

### C1 — Replay observation projection adapter (branch-local)

| Field | Value |
| --- | --- |
| **Files involved** | `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_run_scenario_spine_validation.py` |
| **Current fanout pattern** | New FEM meta/lineage field → edit projection in `golden_replay.py`, drift buckets, classifier field paths, and multiple test expectations independently (6+ files, 6+ commits historically) |
| **Proposed locality mechanism** | Add `tests/helpers/golden_replay_projection.py` (branch-local) exporting `project_turn_observation(turn_payload) -> dict` and `protected_field_paths() -> tuple`. Golden replay + classifier tests import single projection surface. |
| **Expected future reduction** | Meta/lineage observation changes drop from ~6 files to ~2 (projection helper + one owner test) |
| **Risk level** | Low — test-only, no runtime change |
| **Replay/test protection** | `pytest tests/test_golden_replay.py tests/test_failure_classifier.py -q` |

### C2 — Classification contract refresh helper

| Field | Value |
| --- | --- |
| **Files involved** | `tests/failure_classification_contract.py`, `tests/helpers/failure_classifier.py`, `tests/test_failure_classification_contract.py`, `tests/test_failure_classifier.py` |
| **Current fanout pattern** | New category/owner bucket → constant tuple + classifier rule + contract test + classifier test (5 files, 5+ commits) |
| **Proposed locality mechanism** | Branch-local `tests/helpers/failure_classification_sync.py` with `assert_contract_classifier_alignment()` used by contract test; single place to register new allowed values and sample classification fixtures. |
| **Expected future reduction** | Contract expansions: 5 files → 2–3 |
| **Risk level** | Low |
| **Replay/test protection** | `pytest tests/test_failure_classification_contract.py tests/test_failure_classifier.py -q` |

### C3 — Protected replay manifest refresh helper

| Field | Value |
| --- | --- |
| **Files involved** | `docs/testing/protected_replay_manifest.md`, `tests/README_TESTS.md`, `docs/scenario_spine_validation.md` |
| **Current fanout pattern** | Replay policy change manually edits 2–3 markdown registries in same commit as code (5 co-touch commits) |
| **Proposed locality mechanism** | `tools/refresh_protected_replay_manifest.py` (or test-local generator) emitting manifest sections from `golden_replay.PROTECTED_*` constants; docs become generated or single-source referenced. |
| **Expected future reduction** | Manifest cycles: 3 doc files → 1 generator + 1 verification test |
| **Risk level** | Low–medium (doc drift if generator not run) |
| **Replay/test protection** | `pytest tests/test_golden_replay.py -k protected -q`; content-lint if applicable |

### C4 — Runtime lineage summary dedup (reporting-only)

| Field | Value |
| --- | --- |
| **Files involved** | `game/runtime_lineage_telemetry.py`, `tests/helpers/failure_dashboard_report.py`, `tools/run_scenario_spine_validation.py`, `tests/helpers/golden_replay.py` |
| **Current fanout pattern** | Lineage bucket/frequency logic duplicated; changes touch dashboard + tool + replay helper (Cycle M recon) |
| **Proposed locality mechanism** | Require dashboard/tool/replay paths to call `summarize_runtime_lineage_events()` from runtime module only; delete parallel aggregators in helpers (test-only/reporting paths). |
| **Expected future reduction** | Lineage reporting changes: 4 files → 1 runtime + 1 consumer test |
| **Risk level** | Medium — must preserve reporting output shape |
| **Replay/test protection** | `pytest tests/test_runtime_lineage_telemetry.py tests/test_run_scenario_spine_validation.py -q` |

### C5 — Final emission gate assertion facade expansion

| Field | Value |
| --- | --- |
| **Files involved** | `tests/helpers/final_emission_gate_fixtures.py`, `tests/test_final_emission_gate.py`, `tests/test_final_emission_visibility.py`, `tests/test_opening_fallback_owner_bucket.py`, scattered fallback behavior tests |
| **Current fanout pattern** | Cycle E touched 13 test files for ownership-comment/thinning; gate-adjacent tests duplicate harness setup |
| **Proposed locality mechanism** | Expand existing `final_emission_gate_fixtures.py` with branch-local assertion helpers (`assert_fallback_owner_bucket`, `assert_visibility_pool`) so downstream tests import rather than re-assert raw meta keys. |
| **Expected future reduction** | Fallback ownership edits: 8–13 test files → 1 fixture module + 1–2 owner tests |
| **Risk level** | Low |
| **Replay/test protection** | `pytest tests/test_final_emission_gate.py tests/test_final_emission_opening_fallback.py tests/test_final_emission_visibility_fallback.py -q` |

### C6 — FEM replay projection field registry (runtime-adjacent, read-only)

| Field | Value |
| --- | --- |
| **Files involved** | `game/final_emission_replay_projection.py`, `game/final_emission_meta.py`, `tests/helpers/golden_replay.py` |
| **Current fanout pattern** | P/O cycles co-touch projection + meta + golden replay when contraction changes observed fields |
| **Proposed locality mechanism** | Central `REPLAY_OBSERVATION_FIELDS` tuple in `final_emission_replay_projection.py`; golden replay imports for drift path enumeration (read-only re-export). |
| **Expected future reduction** | Projection field changes: 3 files always co-touched → 1 runtime registry + golden import |
| **Risk level** | Low–medium — must not create import cycles |
| **Replay/test protection** | `pytest tests/test_golden_replay.py tests/test_final_emission_meta.py -q` |

---

## 6. Patch Surface Minimization Rules

Recommended rules for Cycle T and subsequent maintenance blocks:

1. **One runtime cluster per block** — e.g., FEM meta, or lineage telemetry, or speaker enforcement; never two gate subsystems in one block.
2. **No mixed runtime/test/documentation changes unless required** — closure/recon markdown in a follow-up commit or separate docs-only commit.
3. **No fixture broadening without owner test** — new golden observation fields land in projection helper first; exactly one owner test (`test_golden_replay.py`) validates before classifier/dashboard consumers update.
4. **No manifest refresh bundled with behavior changes** — run manifest generator (C3) as its own block or CI check after code block merges.
5. **Prefer branch-local helpers before global helpers** — new adapters live under `tests/helpers/<subsystem>_*.py` adjacent to owner test, not in `conftest.py`.
6. **Contract-before-consumer ordering** — update `failure_classification_contract.py` + sync helper before classifier, dashboard, and golden replay in separate commits within a cycle.
7. **Count source fanout, not raw fanout** — use Cycle F rules when evaluating block success; artifact/doc paths tracked separately.
8. **Cap test file fanout at 3 per block** — if a block needs more, split into projection block + consumer thinning block (Cycle L pattern).
9. **No tracked artifact snapshots in source commits** — follow `29da646` lesson; hygiene artifacts stay untracked or in dedicated artifact commits.
10. **Replay-green before classifier-green** — golden replay must pass before failure classifier/dashboard tests are updated for new fields.

---

## 7. Edit Concentration Tracking Proposal

Lightweight tracking to verify Cycle T reduces maintenance fanout over time.

### Commands — files touched per commit

```powershell
# Last 10 commits: hash, subject, raw file count
git log --pretty=format:"%h|%s" -n 10 | ForEach-Object {
  $h = $_.Split('|')[0]
  $c = (git show --name-only --pretty=format: $h | Where-Object { $_ -ne "" }).Count
  "$h|$c|$_"
}
```

```powershell
# Source-only count for last 10 (Python one-liner preferred on Windows)
python -c "import subprocess,statistics; ..."
# Or reuse Cycle F rules in tools/fanout_report.py (proposed, not yet implemented)
```

### Commands — hotspot recurrence

```powershell
git log --name-only --pretty=format:--- %h -n 20 |
  Select-String -NotMatch '^---' |
  Group-Object | Sort-Object Count -Descending |
  Select-Object -First 15 Count, Name
```

### Recommended thresholds for concern

| Metric | Green | Yellow | Red |
| --- | --- | --- | --- |
| Source-only files/commit (median, last 10) | ≤ 5 | 6–8 | ≥ 9 |
| Single maintenance block source fanout | ≤ 5 | 6–7 | ≥ 8 |
| Hotspot file touches (last 10 commits) | ≤ 2 | 3–4 | ≥ 5 |
| Commits ≥ 8 source files (last 10) | 0–1 | 2–3 | ≥ 4 |

### Suggested post-block report format

```markdown
## Cycle T Block Tx Closure — Fanout Check
- Block: T2 — Classification contract refresh helper
- Source files touched: 3 (target ≤ 5)
- Hotspot delta: test_failure_classifier.py 9→9 (unchanged), failure_classifier.py 6→6
- Tests run: pytest tests/test_failure_classification_contract.py tests/test_failure_classifier.py -q
- Manifest/doc commits bundled: no
- Replay protected: yes (golden replay green before merge)
```

Store these one-page closures alongside existing `docs/cycles/cycle_*_closure_*.md` files.

---

## 8. Recommended Cycle T Blocks

Six small, ordered, independently testable blocks. Blocks T1–T3 target the highest co-touch cluster (golden replay + classification). T4–T6 address reporting duplication and gate test facades.

### T1 — Golden replay projection adapter

| Field | Value |
| --- | --- |
| **Purpose** | Centralize turn observation projection and protected field path enumeration |
| **Files likely touched** | `tests/helpers/golden_replay_projection.py` (new), `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py` |
| **Non-goals** | No runtime changes; no classifier/dashboard edits in same block |
| **Tests to run** | `pytest tests/test_golden_replay.py -q` |
| **Expected locality improvement** | Future meta/lineage observation edits: −4 files per change |
| **Parallel with** | T2 (after T1 merges) |

### T2 — Classification contract sync helper

| Field | Value |
| --- | --- |
| **Purpose** | Single alignment gate between contract constants and classifier rules |
| **Files likely touched** | `tests/helpers/failure_classification_sync.py` (new), `tests/failure_classification_contract.py`, `tests/test_failure_classification_contract.py`, `tests/helpers/failure_classifier.py` |
| **Non-goals** | No golden replay or dashboard changes |
| **Tests to run** | `pytest tests/test_failure_classification_contract.py tests/test_failure_classifier.py -q` |
| **Expected locality improvement** | New failure categories: −2–3 files per change |
| **Parallel with** | T5 (orthogonal) |

### T3 — Classifier/dashboard consumer thinning

| Field | Value |
| --- | --- |
| **Purpose** | Rewire classifier and dashboard tests to use T1 projection + T2 sync helpers instead of inline field assertions |
| **Files likely touched** | `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/helpers/failure_dashboard_report.py` |
| **Non-goals** | No runtime gate changes |
| **Tests to run** | `pytest tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_golden_replay.py -q` |
| **Expected locality improvement** | Downstream field edits: −3 files per change |
| **Parallel with** | None (depends on T1, T2) |

### T4 — Lineage summary dedup (reporting paths)

| Field | Value |
| --- | --- |
| **Purpose** | Remove duplicated lineage aggregation from dashboard helper, golden replay, and scenario-spine tool |
| **Files likely touched** | `tests/helpers/failure_dashboard_report.py`, `tests/helpers/golden_replay.py`, `tools/run_scenario_spine_validation.py`, `tests/test_runtime_lineage_telemetry.py` |
| **Non-goals** | No changes to `game/runtime_lineage_telemetry.py` public semantics |
| **Tests to run** | `pytest tests/test_runtime_lineage_telemetry.py tests/test_run_scenario_spine_validation.py -q` |
| **Expected locality improvement** | Lineage reporting edits: −3 files per change |
| **Parallel with** | T2, T5 |

### T5 — Gate fixture assertion facade

| Field | Value |
| --- | --- |
| **Purpose** | Expand `tests/helpers/final_emission_gate_fixtures.py` for fallback owner/pool assertions consumed by gate-adjacent tests |
| **Files likely touched** | `tests/helpers/final_emission_gate_fixtures.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_final_emission_visibility.py`, optionally 1–2 fallback behavior tests |
| **Non-goals** | No gate runtime extraction; max 3 test files migrated |
| **Tests to run** | `pytest tests/test_final_emission_gate.py tests/test_final_emission_opening_fallback.py tests/test_final_emission_visibility_fallback.py tests/test_opening_fallback_owner_bucket.py -q` |
| **Expected locality improvement** | Fallback ownership comment/thinning cycles: −5–10 test files |
| **Parallel with** | T2, T4 |

### T6 — Protected replay manifest generator (docs-only block)

| Field | Value |
| --- | --- |
| **Purpose** | Generate or verify `docs/testing/protected_replay_manifest.md` sections from golden replay constants |
| **Files likely touched** | `tools/refresh_protected_replay_manifest.py` (new), `docs/testing/protected_replay_manifest.md`, `tests/test_golden_replay.py` (verification test only) |
| **Non-goals** | No runtime or classifier logic changes |
| **Tests to run** | `pytest tests/test_golden_replay.py -k manifest -q` (add test) |
| **Expected locality improvement** | Manifest cycles: −2 manual doc files per change |
| **Parallel with** | T4, T5 (after T1 defines constants) |

### Suggested execution order

```
T1 → T2 → T3 → T6
         ↘ T4 (parallel after T1)
         ↘ T5 (parallel anytime)
```

**Success criterion for Cycle T:** Over the next 10 maintenance commits after T6, source-only median ≤ 6 and no single block exceeds 7 source files unless explicitly tagged `cross-cutting`.

---

## Appendix — Methodology Notes

- **Data source:** `git log --name-only --pretty=format:'---COMMIT--- %h %s' -n 30` on branch `feature/failure-locality` at recon time (HEAD `1f4e94e`).
- **Related prior recon:** `audits/cycle_f_source_fanout_refinement_20260518.md`, `docs/cycles/cycle_m_maintenance_drag_reduction_recon_2026-05-27.md`.
- **Existing branch-local helpers worth extending (not replacing):** `tests/helpers/final_emission_gate_fixtures.py`, `tests/helpers/opening_fallback_evidence.py`, `tests/helpers/speaker_relocation_shadow_harness.py`.
