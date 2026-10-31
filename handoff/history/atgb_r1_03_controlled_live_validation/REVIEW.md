# Campaign

Campaign: ATGB-R1-03 Controlled Live Conversational Validation
Identifier: `atgb_r1_03_controlled_live_validation`
Date: 2026-10-19
Generated: 2026-10-19T09:11:57.662695+00:00
Purpose: Bounded validation only; no implementation authority.

# Executive Summary

Original-wording L1/L2 failed upstream before interpretation. L3 correctly identified people but selected no evidence and asked redundant confirmation. L4 control invalid due to test-import environment leakage; generic fallback mutated isolated state. Repaired gate not demonstrated live. Three admissions of eight maximum; one valid completed live trial. Production and all protected baseline/experimental files unchanged. No secrets packaged; no commit/push. Stop for external review.

Objective status: `D — INCONCLUSIVE; EXTERNAL REVIEW REQUIRED`.

# Changes Made

## Production changes

- None. Reviewed R1-02 source unchanged.

## Validation changes

- Controlled designated attempts and AI-assisted six-dimension judgments; no scorer/expectation edits.

## Tooling changes

- Campaign-local observer, bounded SDK transport constructor and reporting/export scripts only.

## Documentation changes

- Eight reports, index and canonical session handoff.

## Generated artifacts

- Raw and normalized traces, transcripts, accounting, state snapshots, hashes and standard review export.

# What Was Tested

- **Focused tests:** 102 non-HTTP boundary tests passed, 3 API tests deselected, exit 0.
- **Broader relevant tests:** Initial 133-test HTTP slice interrupted at Windows TestClient boundary; no completed result.
- **Full suite:** Not run.
- **Runtime validation:** Four designated attempts: two upstream failures, one inadequate live paraphrase, one invalid live control.
- **Model/runtime boundary:** OpenAI gpt-4.1-mini; only L3 returned actual gpt-4.1-mini-2025-04-14; SDK retries zero.
- **New regressions:** No production change; L4 invalid harness cannot establish a new production regression.
- **Pre-existing failures:** Global accounting source manifest stale solely for the reviewed routing repair; dispatch fingerprints unchanged.
- **Self-contained bundle review:** ZIP contains all eight reports, exact exchanges, raw/normalized traces, full pre/post state, accounting and status; source hashes and CRC verified.

# Behavioral Evidence

## Evidence Packet: atgb_r1_03

Runs / turns: `4` / `4`
Runtime/model boundary: Actual provider calls for L1-L3; L4 invalid disabled interpretation.

### Representative success

No example observed in this campaign.

### Representative failure

Example: `L1`
Player classification: `representative_player_behavior, boundary_case`
Player: I meant the people, not the weather.
GM: I couldn't interpret that just now, so no gameplay action was taken.
Automated result: `FAIL`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Source: `artifacts/atgb/atgb_r1_03/L1/response.json`

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

Example: `L4`
Player classification: `synthetic_positive_control, boundary_case`
Player: Instead, make that a question about the lamp.
GM: The action was resolved, but live narration was not requested because it would exceed the provider budget.
Automated result: `INVALID_RUN`
Human review: `UNREVIEWED` - External review pending; AI-assisted assessment only.
Source: `artifacts/atgb/atgb_r1_03/L4/response.json`

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review D inconclusive verdict and invalid-control authority evidence.
- Decide whether to authorize bounded ATGB-R1-04 validation-readiness recovery; no implementation follows automatically.

# Known Problems / Unresolved Findings

## Campaign-specific

- Missing successful original-wording trials.
- L3 redundant clarification and ignored available people evidence.
- L4 fixture import disabled interpretation and isolated fallback mutated state.
- Failed-call token usage/billing unavailable.

## Pre-existing baseline

- Human ATGB review remains unattested.
- Extensive dirty worktree preserved.
- PR-EG integration ban remains.

# Missing Concepts / Future Capabilities

- No new semantic subsystem or authority proposed.

# What This Campaign Does NOT Prove

- Original repair reproduced live, valid mechanical control, broad conversation quality, independent generalization, full-suite green, unconditional authority preservation or exact total cost.

# Recommended Next Step

External review, then separately authorized bounded validation-readiness recovery and missing original/control trials in ATGB-R1-04. Do not implement semantic repairs.

# Review Bundle Contents

Bundle file count: `65`
Bundle ZIP size: `000000343283` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r1_03_controlled_live_validation.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r1_03_controlled_live_validation.md`.
- `support/artifacts/validation_evidence/atgb_r1_03/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_03/evidence_summary.md`.
- `support/artifacts/validation_evidence/atgb_r1_03/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_03/evidence_manifest.json`.
- `support/development/reports/atgb_r1_03/01_execution_readiness.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/01_execution_readiness.md`.
- `support/development/reports/atgb_r1_03/02_live_trial_results.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/02_live_trial_results.md`.
- `support/development/reports/atgb_r1_03/03_execution_traces.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/03_execution_traces.md`.
- `support/development/reports/atgb_r1_03/04_s08_2_historical_comparison.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/04_s08_2_historical_comparison.md`.
- `support/development/reports/atgb_r1_03/05_failure_localization.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/05_failure_localization.md`.
- `support/development/reports/atgb_r1_03/06_authority_and_state_integrity.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/06_authority_and_state_integrity.md`.
- `support/development/reports/atgb_r1_03/07_provider_accounting.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/07_provider_accounting.md`.
- `support/development/reports/atgb_r1_03/08_final_verdict.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `development/reports/atgb_r1_03/08_final_verdict.md`.
- `support/artifacts/atgb/atgb_r1_03/accounting_readiness.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/accounting_readiness.json`.
- `support/artifacts/atgb/atgb_r1_03/entry_hashes.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/entry_hashes.json`.
- `support/artifacts/atgb/atgb_r1_03/integrity.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/integrity.json`.
- `support/artifacts/atgb/atgb_r1_03/normalized_results.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/normalized_results.json`.
- `support/artifacts/atgb/atgb_r1_03/provider_accounting.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/provider_accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/validation_commands.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/validation_commands.json`.
- `support/artifacts/atgb/atgb_r1_03/deterministic.txt`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/deterministic.txt`.
- `support/artifacts/atgb/atgb_r1_03/deterministic_non_http.txt`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/deterministic_non_http.txt`.
- `support/artifacts/atgb/atgb_r1_03/repository_status_after.txt`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/repository_status_after.txt`.
- `support/artifacts/atgb/atgb_r1_03/repository_status_before.txt`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/repository_status_before.txt`.
- `support/artifacts/atgb/atgb_r1_03/transcripts.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/transcripts.md`.
- `support/artifacts/atgb/atgb_r1_03/execute_trial.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/execute_trial.py`.
- `support/artifacts/atgb/atgb_r1_03/prepare_review.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/prepare_review.py`.
- `support/game/conversational_orchestration.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `game/conversational_orchestration.py`.
- `support/game/live_chat_interpretation.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `game/live_chat_interpretation.py`.
- `support/experiments/pr_dq/__init__.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `experiments/pr_dq/__init__.py`.
- `support/tests/test_atgb_r1_02_revision_boundary.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `tests/test_atgb_r1_02_revision_boundary.py`.
- `support/tests/test_pr_ef_r4_authorization.py`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `tests/test_pr_ef_r4_authorization.py`.
- `support/tests/fixtures/pr_ef_r4_holdouts.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `tests/fixtures/pr_ef_r4_holdouts.json`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/data/validation/atgb/visible/S08.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/docs/NEXT_SESSION.md`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `docs/NEXT_SESSION.md`.
- `support/artifacts/atgb/atgb_r1_03/L1/accounting.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/after.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/after.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/before.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/before.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/response.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/setup.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/setup.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/trace.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/trace.json`.
- `support/artifacts/atgb/atgb_r1_03/L1/provider_usage.jsonl`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L1/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_03/L2/accounting.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/after.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/after.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/before.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/before.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/response.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/setup.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/setup.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/trace.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/trace.json`.
- `support/artifacts/atgb/atgb_r1_03/L2/provider_usage.jsonl`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L2/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_03/L3/accounting.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/after.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/after.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/before.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/before.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/response.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/setup.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/setup.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/trace.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/trace.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/provider_usage.jsonl`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L3/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_03/L4/accounting.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/accounting.json`.
- `support/artifacts/atgb/atgb_r1_03/L4/after.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/after.json`.
- `support/artifacts/atgb/atgb_r1_03/L4/before.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/before.json`.
- `support/artifacts/atgb/atgb_r1_03/L4/response.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L4/setup.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/setup.json`.
- `support/artifacts/atgb/atgb_r1_03/L4/trace.json`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/trace.json`.
- `support/artifacts/atgb/atgb_r1_03/L4/provider_usage.jsonl`: Required controlled trial, authority, accounting or baseline evidence. Canonical source: `artifacts/atgb/atgb_r1_03/L4/provider_usage.jsonl`.
- `support/tests/test_pr_du_player_pipeline.py`: Shows the import of experiments.pr_dq.world which executes the package initializer. Canonical source: `tests/test_pr_du_player_pipeline.py`.
- `support/artifacts/atgb/atgb_r1_03/export_review.py`: Export integrity or invalid fixture environment provenance. Canonical source: `artifacts/atgb/atgb_r1_03/export_review.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
