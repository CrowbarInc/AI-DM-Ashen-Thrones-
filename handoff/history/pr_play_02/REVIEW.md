# Campaign

Campaign: PR-PLAY-02 - Controlled Live-Play Readiness
Identifier: `pr_play_02`
Date: 2026-10-19
Generated: 2026-10-19T22:28:12.210455+00:00
Purpose: Bounded offline testing infrastructure preparation; external review before live test

# Executive Summary

SDK retries can be disabled for all seven production callers. Existing atomic six-admission budget reused; rejection diagnostics and nonmutating exhaustion gates added. 30 focused tests pass; total completed slices 354 passed and two failures reproduced on entry source. HTTP blocked at 15s. 445 protected files unchanged. Zero live/provider-connectivity calls; no prompt/schema/gameplay/model/endpoint changes. Stop for external review.

Objective status: `B - Conditionally ready`.

# Changes Made

## Production changes

- Opt-in max_retries=0 constructor kwargs across all seven existing callers.
- Reuse atomic six-request budget; add playtest-only refusal telemetry and safe exhausted-submission gates.

## Validation changes

- 30 new deterministic production-boundary checks; existing regression and entry-source comparisons.

## Tooling changes

- Existing ledger inspector accepts distinct rejection events; no new exporter framework.

## Documentation changes

- Eight reports, manual procedure and canonical session orientation.

## Generated artifacts

- Entry diff/snapshots, mock ledger, constructor/isolation/integrity evidence, regression results and review ZIP.

# What Was Tested

- **Focused tests:** 30 passed; 3.428s. All seven production constructor/dispatch paths; concurrency and real SDK mocked transport.
- **Broader relevant tests:** 301 passed/1 preexisting failed in non-HTTP slice; 23 passed/1 preexisting failed in routing/interpretation compatibility; 354 total passes including focused.
- **Full suite:** Not run.
- **Runtime validation:** Controlled production API/functions and isolated real reset; no live UI or opening.
- **Model/runtime boundary:** No live calls. Real SDK request handling uses local MockTransport only.
- **New regressions:** None observed in completed slices.
- **Pre-existing failures:** Stale ATGB source attestation and exact provider_call metadata assertion reproduced on entry source; HTTP TestClient blocked at 15s.
- **Self-contained bundle review:** Eight reports, instructions, source diff/snapshots, tests and raw evidence selected; final verification checks ZIP CRC, manifest hashes and secret exclusions.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review safeguards and documented gaps, then approve one isolated manual six-attempt session. No live test performed now.

# Known Problems / Unresolved Findings

## Campaign-specific

- One continuous process required; no restart continuation. Legacy contract path retains SDK long timeout; operator stops at 60s.

## Pre-existing baseline

- HTTP environment gap, stale ATGB fingerprint, exact metadata regression assertion; live R1/R2 acceptance remains pending.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Live provider reachability, UI behavior, semantic gameplay quality, provider latency/cost, full regression, refreshed ATGB-worker attestation or benchmark improvement.

# Recommended Next Step

External review of this ZIP, then separately approve operator-run PR_PLAY_02_LIVE_PLAYTEST.txt.

# Review Bundle Contents

Bundle file count: `85`
Bundle ZIP size: `000000590583` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/pr_play_02/08_final_verdict_and_handoff.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/pr_play_02/08_final_verdict_and_handoff.md`.
- `support/development/reports/pr_play_02/01_baseline_and_provider_path_inventory.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/01_baseline_and_provider_path_inventory.md`.
- `support/development/reports/pr_play_02/02_retry_control_implementation.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/02_retry_control_implementation.md`.
- `support/development/reports/pr_play_02/03_admission_budget_implementation.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/03_admission_budget_implementation.md`.
- `support/development/reports/pr_play_02/04_deterministic_validation.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/04_deterministic_validation.md`.
- `support/development/reports/pr_play_02/05_campaign_isolation_and_manual_procedure.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/05_campaign_isolation_and_manual_procedure.md`.
- `support/development/reports/pr_play_02/06_diagnostics_and_evidence_export.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/06_diagnostics_and_evidence_export.md`.
- `support/development/reports/pr_play_02/07_regression_and_performance.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/07_regression_and_performance.md`.
- `support/development/reports/pr_play_02/PR_PLAY_02_LIVE_PLAYTEST.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `development/reports/pr_play_02/PR_PLAY_02_LIVE_PLAYTEST.txt`.
- `support/artifacts/pr_play_02/baseline.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/baseline.json`.
- `support/artifacts/pr_play_02/campaign_isolation_evidence.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/campaign_isolation_evidence.json`.
- `support/artifacts/pr_play_02/capture_controls.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/capture_controls.py`.
- `support/artifacts/pr_play_02/changed_sources.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/changed_sources.json`.
- `support/artifacts/pr_play_02/compatibility.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/compatibility.txt`.
- `support/artifacts/pr_play_02/compatibility.xml`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/compatibility.xml`.
- `support/artifacts/pr_play_02/compatibility_command.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/compatibility_command.json`.
- `support/artifacts/pr_play_02/constructor_evidence.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/constructor_evidence.json`.
- `support/artifacts/pr_play_02/entry_compatibility.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/entry_compatibility.txt`.
- `support/artifacts/pr_play_02/entry_compatibility.xml`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/entry_compatibility.xml`.
- `support/artifacts/pr_play_02/entry_compatibility_setup_block.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/entry_compatibility_setup_block.txt`.
- `support/artifacts/pr_play_02/entry_hashes.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/entry_hashes.json`.
- `support/artifacts/pr_play_02/entry_to_final.diff`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/entry_to_final.diff`.
- `support/artifacts/pr_play_02/failure_classification.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/failure_classification.json`.
- `support/artifacts/pr_play_02/focused.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/focused.txt`.
- `support/artifacts/pr_play_02/focused.xml`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/focused.xml`.
- `support/artifacts/pr_play_02/http.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/http.txt`.
- `support/artifacts/pr_play_02/http_result.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/http_result.json`.
- `support/artifacts/pr_play_02/integrity.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/integrity.json`.
- `support/artifacts/pr_play_02/mock_concurrent_ledger.jsonl`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/mock_concurrent_ledger.jsonl`.
- `support/artifacts/pr_play_02/mock_concurrent_snapshot.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/mock_concurrent_snapshot.json`.
- `support/artifacts/pr_play_02/nonhttp.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/nonhttp.txt`.
- `support/artifacts/pr_play_02/nonhttp.xml`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/nonhttp.xml`.
- `support/artifacts/pr_play_02/nonhttp_command.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/nonhttp_command.json`.
- `support/artifacts/pr_play_02/performance.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/performance.json`.
- `support/artifacts/pr_play_02/provider_inventory.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/provider_inventory.txt`.
- `support/artifacts/pr_play_02/readiness_comparison.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/readiness_comparison.json`.
- `support/artifacts/pr_play_02/regression.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/regression.txt`.
- `support/artifacts/pr_play_02/regression_command.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/regression_command.json`.
- `support/artifacts/pr_play_02/repository_status_after.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/repository_status_after.txt`.
- `support/artifacts/pr_play_02/repository_status_before.txt`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/repository_status_before.txt`.
- `support/artifacts/pr_play_02/sdk_configuration_evidence.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/sdk_configuration_evidence.json`.
- `support/artifacts/pr_play_02/test_summary.json`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/test_summary.json`.
- `support/artifacts/pr_play_02/source_before/docs/NEXT_SESSION.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/docs/NEXT_SESSION.md`.
- `support/artifacts/pr_play_02/source_before/game/api.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/api.py`.
- `support/artifacts/pr_play_02/source_before/game/api_upstream_preflight.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/api_upstream_preflight.py`.
- `support/artifacts/pr_play_02/source_before/game/expressive_dialogue.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/expressive_dialogue.py`.
- `support/artifacts/pr_play_02/source_before/game/gm.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/gm.py`.
- `support/artifacts/pr_play_02/source_before/game/host_constrained_candidates.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/host_constrained_candidates.py`.
- `support/artifacts/pr_play_02/source_before/game/live_chat_interpretation.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/live_chat_interpretation.py`.
- `support/artifacts/pr_play_02/source_before/game/provider_budget.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/provider_budget.py`.
- `support/artifacts/pr_play_02/source_before/game/semantic_interpreter.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/semantic_interpreter.py`.
- `support/artifacts/pr_play_02/source_before/game/unified_semantic_planning.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/game/unified_semantic_planning.py`.
- `support/artifacts/pr_play_02/source_before/tools/atgb/accounting.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `artifacts/pr_play_02/source_before/tools/atgb/accounting.py`.
- `support/tests/test_pr_play_02_controls.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_pr_play_02_controls.py`.
- `support/tests/conftest.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/conftest.py`.
- `support/tests/helpers/live_model_guard.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/helpers/live_model_guard.py`.
- `support/tests/test_provider_accounting_integrity.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_provider_accounting_integrity.py`.
- `support/tests/test_api_upstream_preflight.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_api_upstream_preflight.py`.
- `support/tests/test_campaign_reset.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_campaign_reset.py`.
- `support/tests/test_atgb_r1_02_revision_boundary.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_atgb_r1_02_revision_boundary.py`.
- `support/tests/test_atgb_r1_07_correction_contract.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_atgb_r1_07_correction_contract.py`.
- `support/tests/test_atgb_r2_02_speech_participant_grounding.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_atgb_r2_02_speech_participant_grounding.py`.
- `support/tests/test_atgb_r2_04_question_evidence_contract.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_atgb_r2_04_question_evidence_contract.py`.
- `support/tests/test_pr_ed_provider_efficiency.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_pr_ed_provider_efficiency.py`.
- `support/tests/test_pr_ef_gm_authority.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_pr_ef_gm_authority.py`.
- `support/tests/test_final_emission_gate_diagnostics.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_final_emission_gate_diagnostics.py`.
- `support/tests/test_model_routing_config.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_model_routing_config.py`.
- `support/tests/test_model_routing_runtime.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_model_routing_runtime.py`.
- `support/tests/test_model_routing_escalation.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_model_routing_escalation.py`.
- `support/tests/test_pr_dh_live_interpretation.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tests/test_pr_dh_live_interpretation.py`.
- `support/docs/NEXT_SESSION.md`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `docs/NEXT_SESSION.md`.
- `support/game/api.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/api.py`.
- `support/game/api_upstream_preflight.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/api_upstream_preflight.py`.
- `support/game/expressive_dialogue.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/expressive_dialogue.py`.
- `support/game/gm.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/gm.py`.
- `support/game/host_constrained_candidates.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/host_constrained_candidates.py`.
- `support/game/live_chat_interpretation.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/live_chat_interpretation.py`.
- `support/game/provider_budget.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/provider_budget.py`.
- `support/game/semantic_interpreter.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/semantic_interpreter.py`.
- `support/game/unified_semantic_planning.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `game/unified_semantic_planning.py`.
- `support/tools/atgb/accounting.py`: Explicit PR-PLAY-02 source, entry snapshot, tests, diagnostic or manual handoff evidence. Canonical source: `tools/atgb/accounting.py`.
- `support/artifacts/pr_play_02/review_config.json`: Explicit review configuration and source checks. Canonical source: `artifacts/pr_play_02/review_config.json`.
- `support/artifacts/pr_play_02/prepackage_checks.json`: Explicit review configuration and source checks. Canonical source: `artifacts/pr_play_02/prepackage_checks.json`.

## Explicit omissions

- `development/reports/pr_play_02/08_final_verdict_and_handoff.md`: duplicate content of development/reports/pr_play_02/08_final_verdict_and_handoff.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
