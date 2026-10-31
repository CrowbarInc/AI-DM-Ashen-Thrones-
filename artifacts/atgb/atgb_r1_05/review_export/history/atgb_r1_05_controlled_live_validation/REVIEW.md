# Campaign

Campaign: ATGB-R1-05 Controlled Live Validation Continuation
Identifier: `atgb_r1_05_controlled_live_validation`
Date: 2026-10-19
Generated: 2026-10-19T09:42:40.927604+00:00
Purpose: Three authorized live trials only; no production implementation authority.

# Executive Summary

Two exact S08.2 trials avoid mechanical misrouting but still ask redundant confirmation with empty evidence. L4 preserves legitimate pending revision. Three successful responses, 3/6 admissions, zero retries, 6475 tokens; gameplay unchanged.

Objective status: `B — PARTIAL; EXTERNAL REVIEW REQUIRED`.

# Changes Made

## Production changes

- None; all production entry hashes unchanged.

## Validation changes

- Three specified live trials; ten current import/mode safety tests.

## Tooling changes

- Evidence-local isolated runner using unchanged R1-04 gate/control; offline packaging script.

## Documentation changes

- Eight reports, index, canonical NEXT_SESSION.

## Generated artifacts

- Complete snapshots, raw/normalized traces, transcripts, ledger/accounting, behavioral packet, verified review ZIP.

# What Was Tested

- **Focused tests:** 10 import/mode safety tests passed; three live preflights ready.
- **Broader relevant tests:** Not rerun; prior 167-test R1-04 evidence preserved.
- **Full suite:** Not run.
- **Runtime validation:** L1/L2/L4 direct production chat; live interpretation in each measured step; L4 initial setup stub only.
- **Model/runtime boundary:** OpenAI Responses gpt-4.1-mini -> gpt-4.1-mini-2025-04-14; temperature 0/output cap 320; no SDK retries.
- **New regressions:** No observed authority or revision-routing regression in these three trials.
- **Pre-existing failures:** L1/L2 semantic failure matches R1-03 L3; global accounting manifest stale; HTTP not covered.
- **Self-contained bundle review:** All eight reports, exact transcripts, raw/normalized traces, snapshots, provider ledgers, source references and integrity hashes; ZIP CRC/source-hash/secret scan.

# Behavioral Evidence

## Evidence Packet: ATGB-R1-05

Runs / turns: `3` / `3`
Runtime/model boundary: Production host orchestration and existing final-emission boundary

### Representative success

No example observed in this campaign.

### Representative failure

Example: `ATGB-R1-05-L1`
Player classification: `representative_player_behavior, boundary_case`
Player: I meant the people, not the weather.
GM: Do you mean to clarify that your previous reference was to the people present rather than the weather conditions?
Automated result: `FAIL`
Human review: `UNREVIEWED` - AI-assisted provisional criteria analysis; no authenticated human adjudication.
Source: `artifacts/atgb/atgb_r1_05/L1/response.json`

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

Example: `ATGB-R1-05-L4`
Player classification: `synthetic_positive_control, boundary_case`
Player: Instead, make that a question about the lamp.
GM: I've revised that unexecuted intention. It has not been attempted. Which person do you mean: Sergeant Mara or Corporal Bren? Nothing has been attempted.
Automated result: `PASS`
Human review: `UNREVIEWED` - AI-assisted provisional criteria analysis; no authenticated human adjudication.
Source: `artifacts/atgb/atgb_r1_05/L4/response.json`

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review provisional B verdict and authorize only the proposed bounded offline ATGB-R1-06 investigation if desired. No follow-on work begins automatically.

# Known Problems / Unresolved Findings

## Campaign-specific

- L1/L2 subject recognized but evidence empty and response redundant.
- L4 model topic/recipient conflation retained; later execution untested.

## Pre-existing baseline

- Dirty worktree, unattested human assessment, stale global accounting manifest and historical HTTP coverage limitations.

# Missing Concepts / Future Capabilities

- No new gameplay owner or binding architecture proposed.

# What This Campaign Does NOT Prove

- Broad conversational reliability, independent generalization, full ATGB benchmark score, full-suite green, later L4 execution correctness, price/billing or performance improvement.

# Recommended Next Step

External review, then separately authorized offline causal investigation/contract proposal for saved L1/L2 interpretation/evidence defect against R1-03 L3. No implementation or further live calls now.

# Review Bundle Contents

Bundle file count: `105`
Bundle ZIP size: `000000480445` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r1_05_controlled_live_validation.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r1_05_controlled_live_validation.md`.
- `support/artifacts/validation_evidence/atgb_r1_05/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_05/evidence_summary.md`.
- `support/artifacts/validation_evidence/atgb_r1_05/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_05/evidence_manifest.json`.
- `support/artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S08/result.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_03c/S08/result.json`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/artifacts/atgb/atgb_r1_03/L3/response.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_03/L3/response.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/setup.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_03/L3/setup.json`.
- `support/artifacts/atgb/atgb_r1_03/L3/trace.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_03/L3/trace.json`.
- `support/artifacts/atgb/atgb_r1_05/authorization_and_launches.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/authorization_and_launches.json`.
- `support/artifacts/atgb/atgb_r1_05/baseline_comparison.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/baseline_comparison.json`.
- `support/artifacts/atgb/atgb_r1_05/commands.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/commands.json`.
- `support/artifacts/atgb/atgb_r1_05/entry_hashes.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/entry_hashes.json`.
- `support/artifacts/atgb/atgb_r1_05/integrity.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/integrity.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/accounting.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/accounting.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/after.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/after.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/before.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/before.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/configuration.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/configuration.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/normalized.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/normalized.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/preflight.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/preflight.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/provider_usage.jsonl`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_05/L1/response.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/response.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/setup.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/setup.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/state_integrity.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/state_integrity.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/timing.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/timing.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/traces.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/traces.json`.
- `support/artifacts/atgb/atgb_r1_05/L1/transcript.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L1/transcript.md`.
- `support/artifacts/atgb/atgb_r1_05/L2/accounting.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/accounting.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/after.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/after.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/before.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/before.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/configuration.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/configuration.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/normalized.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/normalized.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/provider_usage.jsonl`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_05/L2/response.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/response.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/setup.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/setup.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/timing.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/timing.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/traces.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/traces.json`.
- `support/artifacts/atgb/atgb_r1_05/L2/transcript.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L2/transcript.md`.
- `support/artifacts/atgb/atgb_r1_05/L4/accounting.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/accounting.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/after.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/after.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/before.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/before.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/configuration.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/configuration.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/normalized.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/normalized.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/provider_usage.jsonl`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_05/L4/response.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/response.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/setup_before.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/setup_before.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/setup_response.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/setup_response.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/state_integrity.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/state_integrity.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/timing.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/timing.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/traces.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/traces.json`.
- `support/artifacts/atgb/atgb_r1_05/L4/transcript.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/L4/transcript.md`.
- `support/artifacts/atgb/atgb_r1_05/NEXT_SESSION_before.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/NEXT_SESSION_before.md`.
- `support/artifacts/atgb/atgb_r1_05/normalized_results.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/normalized_results.json`.
- `support/artifacts/atgb/atgb_r1_05/package_review.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/package_review.py`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/accounting.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/accounting.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/after.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/after.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/configuration.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/configuration.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/preflight.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/preflight.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/provider_usage.jsonl`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/setup.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/setup.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/state_integrity.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/state_integrity.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview/timing.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview/timing.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/accounting.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/accounting.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/after.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/after.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/before.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/before.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/configuration.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/configuration.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/provider_usage.jsonl`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/request_payload.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/request_payload.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/response.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/response.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/setup.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/setup.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/state_integrity.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/state_integrity.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/timing.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/timing.json`.
- `support/artifacts/atgb/atgb_r1_05/payload_preview_corrected/traces.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/payload_preview_corrected/traces.json`.
- `support/artifacts/atgb/atgb_r1_05/provider_accounting.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/provider_accounting.json`.
- `support/artifacts/atgb/atgb_r1_05/readiness_tests.xml`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/readiness_tests.xml`.
- `support/artifacts/atgb/atgb_r1_05/repository_status_after.txt`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/repository_status_after.txt`.
- `support/artifacts/atgb/atgb_r1_05/repository_status_before.txt`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/repository_status_before.txt`.
- `support/artifacts/atgb/atgb_r1_05/run_trial.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `artifacts/atgb/atgb_r1_05/run_trial.py`.
- `support/development/reports/atgb_r1_01_s08_2_causal_trace.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_01_s08_2_causal_trace.md`.
- `support/development/reports/atgb_r1_02/08_final_verdict.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_02/08_final_verdict.md`.
- `support/development/reports/atgb_r1_03/05_failure_localization.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_03/05_failure_localization.md`.
- `support/development/reports/atgb_r1_04/08_final_verdict.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_04/08_final_verdict.md`.
- `support/development/reports/atgb_r1_05/01_execution_readiness.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/01_execution_readiness.md`.
- `support/development/reports/atgb_r1_05/02_live_trial_results.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/02_live_trial_results.md`.
- `support/development/reports/atgb_r1_05/03_execution_traces.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/03_execution_traces.md`.
- `support/development/reports/atgb_r1_05/04_historical_comparison.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/04_historical_comparison.md`.
- `support/development/reports/atgb_r1_05/05_failure_localization.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/05_failure_localization.md`.
- `support/development/reports/atgb_r1_05/06_authority_and_state_integrity.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/06_authority_and_state_integrity.md`.
- `support/development/reports/atgb_r1_05/07_provider_accounting.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/07_provider_accounting.md`.
- `support/development/reports/atgb_r1_05/08_final_verdict.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `development/reports/atgb_r1_05/08_final_verdict.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/product_realization_validation.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `docs/product_realization_validation.md`.
- `support/docs/validation_evidence_standard.md`: R1-05 direct execution or read-only comparison provenance. Canonical source: `docs/validation_evidence_standard.md`.
- `support/game/api.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `game/api.py`.
- `support/game/conversational_orchestration.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `game/conversational_orchestration.py`.
- `support/game/live_chat_interpretation.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `game/live_chat_interpretation.py`.
- `support/game/provider_budget.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `game/provider_budget.py`.
- `support/tests/fixtures/pr_ef_r4_holdouts.json`: R1-05 direct execution or read-only comparison provenance. Canonical source: `tests/fixtures/pr_ef_r4_holdouts.json`.
- `support/tests/test_atgb_r1_04_readiness.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `tests/test_atgb_r1_04_readiness.py`.
- `support/tools/atgb/isolation.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `tools/atgb/isolation.py`.
- `support/tools/atgb/readiness.py`: R1-05 direct execution or read-only comparison provenance. Canonical source: `tools/atgb/readiness.py`.

## Explicit omissions

- `artifacts/atgb/atgb_r1_05/L2/inherited_environment_names.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/L2/preflight.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/preflight.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/L2/state_integrity.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/state_integrity.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/L4/inherited_environment_names.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/L4/preflight.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/preflight.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/payload_preview/before.json`: duplicate content of artifacts/atgb/atgb_r1_05/payload_preview/after.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/payload_preview/inherited_environment_names.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/payload_preview/response.json`: duplicate content of artifacts/atgb/atgb_r1_05/payload_preview/preflight.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/payload_preview/traces.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/payload_preview_corrected/inherited_environment_names.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/inherited_environment_names.json; canonical reference retained
- `artifacts/atgb/atgb_r1_05/payload_preview_corrected/preflight.json`: duplicate content of artifacts/atgb/atgb_r1_05/L1/preflight.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
