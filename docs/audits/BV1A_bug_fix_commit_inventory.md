# BV1A — Bug-Fix Commit Inventory

**Date:** 2026-06-21
**Scope:** Measurement only. Classifies commits after BI (`f7e73fb`) through HEAD using BR heuristics.

## Executive summary

Post-BI window contains **10** commits and **zero** classified **bug fix** commits. The corrective cohort remains **N = 0**; pre-BI BR baseline retains **11** bug-fix commits (median **9** files).

Program work in the window splits into **5 architecture** commits (BJ–BN–BM–BK–BL) and **5 refactor** commits (BP–BU governance/instrumentation). These measure migration and observability cost, not demonstrated defect-repair locality.

## Methodology

- Boundary: `f7e73fb..HEAD` (BI exclusive).
- Classification precedence matches BR/BRL1 (`docs/reports/BR_commit_classification.csv` where available).
- **bug fix** — explicit corrective signals (fix, repair, preserve, guard, …).
- **architecture** — planned extraction, decomposition, ownership compression (BJ–BM).
- **refactor** — governance, audit, telemetry, incidence instrumentation (BP–BU).
- **feature** — new capability work (none in post-BI window).
- Files and directories from `git diff-tree --no-commit-id --name-only -r <sha>`.

## Post-BI commit inventory (full cohort)

| commit | date | classification | files touched | directories touched |
|---|---|---|---:|---|
| `22cd49a` | 2026-06-21 | refactor | 75 | .github/workflows, Makefile, docs/README.md, docs/architecture_ownership_ledger.md, docs/audits, docs/convergence_ci_inventory.md, docs/cycles, docs/testing, game/final_emission_fem_assembly.py, game/final_emission_finalize.py … (+44 more) |
| `ea80d52` | 2026-06-20 | refactor | 6 | docs/audits, tests/helpers, tests/test_block_u_finalize_stack_divergence.py, tests/test_speaker_contract_risk.py |
| `adc374b` | 2026-06-20 | refactor | 50 | artifacts/attribution_completeness_report.md, artifacts/attribution_regression_guard_report.md, artifacts/bs3_contract_compliance_report.md, artifacts/bs4_producer_stamp_report.md, artifacts/bs5_projection_convergence_report.md, artifacts/bs_attribution_baseline_report.md, artifacts/bug_fix_locality_regression_guard_report.md, artifacts/bug_fix_locality_report.md, docs/audits/metrics/BR1_attribution_completeness_metric.md, docs/audits/metrics/BR2_attribution_regression_guard.md … (+33 more) |
| `3f5ee0c` | 2026-06-20 | refactor | 31 | artifacts/golden_replay, docs/audits, tests/helpers, tests/test_backfill_bug_recurrence_history.py, tests/test_expand_protected_replay_observations.py, tests/test_failure_dashboard_report.py, tests/test_golden_replay_protected_bridge.py, tests/test_migrate_bug_recurrence_event_log.py, tests/test_recurrence_trajectory_history.py, tests/test_replay_bug_class_recurrence.py … (+5 more) |
| `d65a535` | 2026-06-19 | refactor | 59 | artifacts/bo_maintenance_audit.json, artifacts/golden_replay, docs/audits, docs/cycles, tests/test_fallback_incidence_anomalies.py, tests/test_fallback_incidence_report.py, tests/test_fallback_incidence_trends.py, tests/test_fallback_maintenance_economics.py, tests/test_fallback_portfolio_benefit.py, tests/test_fallback_projection_coverage_audit.py … (+20 more) |
| `b7c5b2c` | 2026-06-17 | architecture | 16 | docs/architecture_ownership_ledger.md, docs/refactor, tests/test_final_emission_gate.py, tests/test_final_emission_gate_delegator_regression.py, tests/test_final_emission_gate_diagnostics.py, tests/test_final_emission_gate_n4.py, tests/test_final_emission_gate_orchestration_order.py, tests/test_final_emission_gate_selector_snapshots.py, tests/test_golden_replay.py, tests/test_golden_replay_direct_seam.py … (+5 more) |
| `b88a560` | 2026-06-17 | architecture | 18 | game/final_emission_gate_context.py, game/final_emission_gate_preflight_branch_flags.py, game/final_emission_gate_preflight_defaults.py, game/final_emission_gate_preflight_interaction.py, game/final_emission_gate_preflight_pregate_text.py, game/final_emission_gate_preflight_strict_social.py, game/final_emission_gate_preflight_telemetry.py, game/final_emission_gate_preflight_turn_packet.py, game/final_emission_gate_preflight_upstream.py, game/final_emission_non_strict_stack.py … (+8 more) |
| `683c8df` | 2026-06-17 | architecture | 26 | docs/cycles, game/fallback_provenance_debug.py, game/final_emission_meta.py, game/final_emission_opening_fallback.py, game/final_emission_replay_projection.py, game/final_emission_response_type.py, game/final_emission_sealed_fallback.py, game/final_emission_visibility_fallback.py, game/opening_deterministic_fallback.py, game/output_sanitizer.py … (+8 more) |
| `97b1836` | 2026-06-16 | architecture | 14 | tests/helpers, tests/test_dead_turn_evaluation_threading.py, tests/test_failure_classification_contract.py, tests/test_failure_dashboard_controlled_failures.py, tests/test_golden_replay.py, tests/test_golden_replay_projection.py, tests/test_ownership_registry.py, tests/test_run_scenario_spine_validation.py, tests/test_transcript_gauntlet_actor_addressing.py, tools/refresh_protected_replay_manifest.py |
| `11ff282` | 2026-06-16 | architecture | 92 | game/dialogue_social_plan.py, game/fallback_provenance_debug.py, game/final_emission_acceptance_quality.py, game/final_emission_answer_shape_primacy.py, game/final_emission_anti_railroading.py, game/final_emission_context_separation.py, game/final_emission_fast_fallback_composition.py, game/final_emission_fem_assembly.py, game/final_emission_finalize.py, game/final_emission_first_mention_composition.py … (+75 more) |

### Post-BI commit subjects

| commit | subject |
|---|---|
| `22cd49a` | BU: Post-BJ Fan-In / Fan-Out Validation |
| `ea80d52` | BT: Speaker Finalization Divergence Audit |
| `adc374b` | BS: Semantic Replacement Attribution Completeness |
| `3f5ee0c` | BQ: Recurrence History Population |
| `d65a535` | BP: Runtime Fallback Incidence Instrumentation |
| `b7c5b2c` | BM: Large Test File Decomposition |
| `b88a560` | BN — Gate Fan-Out Reduction |
| `683c8df` | BK: Fallback Ownership Compression |
| `97b1836` | BL: Replay Projection Simplification |
| `11ff282` | BJ: Final Emission Gate Responsibility Extraction |

## Pre-BI bug-fix inventory (BR baseline cohort)

Included for comparison — these are the 11 commits that establish the BR median of **9 files**.

| commit | date | classification | files touched | directories touched |
|---|---|---|---:|---|
| `09863c6` | 2026-03-21 | bug fix | 7 | data/scenes, data/session.json, data/session_log.jsonl, game/adjudication.py, game/api.py, game/gm.py, game/prompt_context.py |
| `ceecc57` | 2026-04-16 | bug fix | 20 | data/scenes, data/session.json, data/session_log.jsonl, data/world.json, docs/current_focus.md, docs/narrative_integrity_architecture.md, game/api.py, game/api_upstream_preflight.py … (+12 more) |
| `6351b33` | 2026-04-25 | bug fix | 16 | data/combat.json, data/session.json, data/session_log.jsonl, game/api.py, game/diegetic_fallback_narration.py, game/final_emission_gate.py, game/final_emission_meta.py, game/final_emission_text.py … (+8 more) |
| `2013258` | 2026-04-25 | bug fix | 7 | data/combat.json, data/session.json, data/session_log.jsonl, game/gm.py, game/opening_visible_fact_selection.py, tests/test_opening_visible_fact_selection.py, tests/test_start_campaign_api.py |
| `2b293b2` | 2026-04-25 | bug fix | 3 | data/combat.json, data/session.json, data/session_log.jsonl |
| `9e83820` | 2026-04-26 | bug fix | 7 | data/combat.json, data/session.json, data/session_log.jsonl, game/api.py, game/final_emission_gate.py, game/prompt_context.py, tests/test_start_campaign_api.py |
| `1b3b3ee` | 2026-04-26 | bug fix | 5 | data/combat.json, data/session.json, data/session_log.jsonl, game/final_emission_gate.py, tests/test_final_emission_gate.py |
| `f487f4d` | 2026-04-26 | bug fix | 216 | codex_pytest_tmp19/test_start_campaign_emits_open0, codex_pytest_tmp20/test_compose_state_ui_campaign0, codex_pytest_tmp20/test_failed_start_campaign_doe0, codex_pytest_tmp20/test_new_campaign_leaves_log_e0, codex_pytest_tmp20/test_second_start_campaign_rej0, codex_pytest_tmp20/test_start_campaign_emits_open0, codex_pytest_tmp20/test_start_campaign_frontier_g0, codex_pytest_tmp20/test_start_campaign_log_has_no0 … (+19 more) |
| `f3fa4b1` | 2026-04-26 | bug fix | 52 | codex_pytest_tmp30/test_api_state_projection_play0, codex_pytest_tmp30/test_endpoint_guards_author_de0, codex_pytest_tmp30/test_public_log_exposes_player0, codex_pytest_tmp30/test_state_leakage_guards_by_m0, data/combat.json, data/session.json, data/session_log.jsonl, data/world.json … (+4 more) |
| `5cb8444` | 2026-04-26 | bug fix | 538 | codex_pytest_tmp36/test_chat_mixed_scene_object_i0, codex_pytest_tmp36/test_chat_mixed_scene_object_i1, codex_pytest_tmp36/test_chat_mixed_scene_object_i2, codex_pytest_tmp36/test_chat_mixed_scene_object_i3, codex_pytest_tmp37/test_chat_mixed_scene_object_i0, codex_pytest_tmp37/test_chat_mixed_scene_object_i1, codex_pytest_tmp37/test_chat_mixed_scene_object_i2, codex_pytest_tmp37/test_chat_mixed_scene_object_i3 … (+60 more) |
| `6a402d2` | 2026-05-20 | bug fix | 9 | docs/reports, game/api_upstream_preflight.py, game/config.py, game/gm.py, tests/test_api_upstream_preflight.py, tests/test_model_routing_config.py, tests/test_model_routing_escalation.py, tests/test_model_routing_runtime.py … (+1 more) |

## Classification summary

| classification | post-BI count | pre-BI bug-fix count |
|---|---:|---:|
| bug fix | 0 | 11 |
| architecture | 5 | — |
| refactor | 5 | — |
| feature | 0 | — |

## Evidence

| Command | Result |
|---|---|
| `git log --format=%h|%ad|%s f7e73fb..HEAD` | 10 commits |
| `docs/reports/BR_commit_classification.csv` | 11 pre-BI `bug_fix` rows |
| `artifacts/bv1a_analysis.json` | Machine-readable inventory |
