# Campaign

Campaign: ATGB-R1-04 Validation Readiness Recovery
Identifier: `atgb_r1_04_validation_readiness_recovery`
Date: 2026-10-19
Generated: 2026-10-19T09:29:42.332808+00:00
Purpose: Validation infrastructure only; no live provider authority.

# Executive Summary

Import-safe replacement control and fail-closed gate demonstrated. 167 deterministic tests pass. HTTP slice incomplete; provider root causes unresolved. No production edits or live calls; all 3,996 protected entry files unchanged.

Objective status: `B — CONDITIONALLY READY; EXTERNAL REVIEW REQUIRED`.

# Changes Made

## Production changes

- None.

## Validation changes

- 36 new readiness tests; frozen mechanical correction inputs exercised through direct chat.

## Tooling changes

- tools/atgb/readiness.py: scoped execution mode, checked imports, preflight, guarded callback, isolated control seed.

## Documentation changes

- Eight reports, index, canonical NEXT_SESSION.

## Generated artifacts

- Test, preflight, control state, provider assessment, preservation and selected-source export.

# What Was Tested

- **Focused tests:** 167 passed; 36 new + 105 R1-02 + 26 state authority; exit 0; zero failed/skipped.
- **Broader relevant tests:** HTTP authorization slice interrupted at TestClient boundary; incomplete.
- **Full suite:** Not run.
- **Runtime validation:** Direct production chat with stubbed interpretation; no live endpoint calls.
- **Model/runtime boundary:** No model execution; gpt-4.1-mini configuration inspected only.
- **New regressions:** None in completed slice.
- **Pre-existing failures:** HTTP environment limitation; global source manifest stale.
- **Self-contained bundle review:** Eight reports, selected source/diffs, final JUnit/logs, preflight failures/success, state evidence, provider diagnosis and source hashes; CRC and secret scan.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review conditional readiness and whether to authorize bounded ATGB-R1-05 live continuation. No execution follows automatically.

# Known Problems / Unresolved Findings

## Campaign-specific

- Future live runner must use new gate/control; old runner remains historical and unsafe.
- Provider reachability and L1/L2 causes unresolved.

## Pre-existing baseline

- HTTP TestClient incomplete; source manifest stale; human assessment unattested; dirty worktree.

# Missing Concepts / Future Capabilities

- No new gameplay owner proposed.

# What This Campaign Does NOT Prove

- Provider health, live original/control success, model response adequacy, full-suite green, independent generalization or benchmark performance.

# Recommended Next Step

External review; separately authorize bounded ATGB-R1-05 using the new gate/control. Stop now; no live calls.

# Review Bundle Contents

Bundle file count: `73`
Bundle ZIP size: `000000315137` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r1_04_validation_readiness_recovery.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r1_04_validation_readiness_recovery.md`.
- `support/artifacts/atgb/atgb_r1_03/L1/accounting.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/provider_usage.jsonl`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_03/L1/response.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/trace.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/trace.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/accounting.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/provider_usage.jsonl`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_03/L2/response.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/trace.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/trace.json`.
- `support/artifacts/atgb/atgb_r1_03/execute_trial.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_03/execute_trial.py`.
- `support/artifacts/atgb/atgb_r1_04/NEXT_SESSION_before.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/NEXT_SESSION_before.md`.
- `support/artifacts/atgb/atgb_r1_04/baseline_comparison.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/baseline_comparison.json`.
- `support/artifacts/atgb/atgb_r1_04/commands.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/commands.json`.
- `support/artifacts/atgb/atgb_r1_04/entry_hashes.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/entry_hashes.json`.
- `support/artifacts/atgb/atgb_r1_04/final.txt`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/final.txt`.
- `support/artifacts/atgb/atgb_r1_04/final.xml`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/final.xml`.
- `support/artifacts/atgb/atgb_r1_04/final_exit.txt`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/final_exit.txt`.
- `support/artifacts/atgb/atgb_r1_04/integrity.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/integrity.json`.
- `support/artifacts/atgb/atgb_r1_04/package_review.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/package_review.py`.
- `support/artifacts/atgb/atgb_r1_04/pending_control.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/pending_control.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_actor.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_actor.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_executed.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_executed.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_import.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_import.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_ledger.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_ledger.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_limit.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_limit.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_mode.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_mode.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_model.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_model.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_pending.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_pending.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_provider.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_provider.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_provider_disabled.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_provider_disabled.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_retries.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_retries.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_scene.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_scene.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_stale.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_stale.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_startup.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_startup.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_store.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_store.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_target.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_target.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_tokens.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_tokens.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_failure_used_budget.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_failure_used_budget.json`.
- `support/artifacts/atgb/atgb_r1_04/preflight_valid.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/preflight_valid.json`.
- `support/artifacts/atgb/atgb_r1_04/provider_assessment.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/provider_assessment.json`.
- `support/artifacts/atgb/atgb_r1_04/regression.txt`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/regression.txt`.
- `support/artifacts/atgb/atgb_r1_04/repository_status_after.txt`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/repository_status_after.txt`.
- `support/artifacts/atgb/atgb_r1_04/repository_status_before.txt`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/repository_status_before.txt`.
- `support/artifacts/atgb/atgb_r1_04/scoped_changes.patch`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/scoped_changes.patch`.
- `support/artifacts/atgb/atgb_r1_04/targeted.txt`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/targeted.txt`.
- `support/artifacts/atgb/atgb_r1_04/targeted.xml`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `artifacts/atgb/atgb_r1_04/targeted.xml`.
- `support/development/reports/atgb_r1_03/05_failure_localization.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_03/05_failure_localization.md`.
- `support/development/reports/atgb_r1_04/01_baseline_and_scope.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/01_baseline_and_scope.md`.
- `support/development/reports/atgb_r1_04/02_environment_leakage_root_cause.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/02_environment_leakage_root_cause.md`.
- `support/development/reports/atgb_r1_04/03_harness_repair.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/03_harness_repair.md`.
- `support/development/reports/atgb_r1_04/04_preflight_verification.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/04_preflight_verification.md`.
- `support/development/reports/atgb_r1_04/05_pending_action_control.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/05_pending_action_control.md`.
- `support/development/reports/atgb_r1_04/06_provider_failure_assessment.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/06_provider_failure_assessment.md`.
- `support/development/reports/atgb_r1_04/07_regression_evidence.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/07_regression_evidence.md`.
- `support/development/reports/atgb_r1_04/08_final_verdict.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `development/reports/atgb_r1_04/08_final_verdict.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/product_realization_validation.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `docs/product_realization_validation.md`.
- `support/docs/validation_evidence_standard.md`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `docs/validation_evidence_standard.md`.
- `support/experiments/pr_dq/__init__.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `experiments/pr_dq/__init__.py`.
- `support/game/conversational_orchestration.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `game/conversational_orchestration.py`.
- `support/game/live_chat_interpretation.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `game/live_chat_interpretation.py`.
- `support/game/provider_budget.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `game/provider_budget.py`.
- `support/game/semantic_interpreter.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `game/semantic_interpreter.py`.
- `support/tests/fixtures/pr_ef_r4_holdouts.json`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tests/fixtures/pr_ef_r4_holdouts.json`.
- `support/tests/test_atgb_r1_02_revision_boundary.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tests/test_atgb_r1_02_revision_boundary.py`.
- `support/tests/test_atgb_r1_04_readiness.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tests/test_atgb_r1_04_readiness.py`.
- `support/tests/test_pr_du_player_pipeline.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tests/test_pr_du_player_pipeline.py`.
- `support/tests/test_pr_ef_gm_authority.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tests/test_pr_ef_gm_authority.py`.
- `support/tests/test_pr_ef_r4_authorization.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tests/test_pr_ef_r4_authorization.py`.
- `support/tools/atgb/readiness.py`: R1-04 scoped recovery, failure provenance or deterministic evidence. Canonical source: `tools/atgb/readiness.py`.

## Explicit omissions

- `artifacts/atgb/atgb_r1_04/targeted_exit.txt`: duplicate content of artifacts/atgb/atgb_r1_04/final_exit.txt; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
