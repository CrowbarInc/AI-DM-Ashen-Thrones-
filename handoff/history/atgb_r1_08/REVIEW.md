# Campaign

Campaign: ATGB-R1-08 Live Conversational Correction Validation
Identifier: `atgb_r1_08`
Date: 2026-10-19
Generated: 2026-10-19T10:46:32.689159+00:00
Purpose: Bounded live validation only; mandatory stop after provider failure.

# Executive Summary

L1 passed readiness but one admitted dispatch failed with APIConnectionError; usage unknown. L2/L3/L4 not run. Live repair effect remains unmeasured; gameplay state unchanged.

Objective status: `D — Inconclusive; await external review`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- One authorized measured admission, failed before model response.

## Tooling changes

- Validation-only adaptation of corrected R1-05 runner; offline packaging.

## Documentation changes

- Eight reports and canonical NEXT_SESSION update.

## Generated artifacts

- Complete available request/host/state/accounting evidence.

# What Was Tested

- **Focused tests:** Reviewed prior deterministic evidence; no new pytest run.
- **Broader relevant tests:** Not run.
- **Full suite:** Not run.
- **Runtime validation:** Direct production chat; one failed interpretation dispatch.
- **Model/runtime boundary:** Configured gpt-4.1-mini; returned version unavailable; retries zero.
- **New regressions:** None demonstrated; semantic behavior unmeasured.
- **Pre-existing failures:** Known historical conversational inadequacy remains untested by this failed call.
- **Self-contained bundle review:** Eight reports; full available transcript/messages/traces/before-after snapshots/ledger; historical comparison; protected hashes and explicit unknowns included.

# Behavioral Evidence

## Evidence Packet: atgb_r1_08

Runs / turns: `1` / `1`
Runtime/model boundary: One failed gpt-4.1-mini interpretation dispatch; deterministic host fallback

### Representative success

No example observed in this campaign.

### Representative failure

Example: `ATGB-R1-08-L1`
Player classification: `representative_player_behavior`
Player: I meant the people, not the weather.
GM: I couldn't interpret that just now, so no gameplay action was taken.
Automated result: `FAIL`
Human review: `UNREVIEWED` - Provisional AI-assisted analysis; no authenticated human review
Source: `artifacts/atgb/atgb_r1_08/L1/response.json`

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review inconclusive result; live repair acceptance withheld. Any next live pass needs separate authorization.

# Known Problems / Unresolved Findings

## Campaign-specific

- APIConnectionError; unknown usage; L2/L3/L4 not evaluated.
- Response completion counters report zero; durable ledger records one actual admission.

## Pre-existing baseline

- Broad conversational competence and authenticated human assessment remain unestablished.

# Missing Concepts / Future Capabilities

- None recorded.

# What This Campaign Does NOT Prove

- Live repair improvement/ineffectiveness, L4 preservation, broad reliability, independent generalization or benchmark performance.

# Recommended Next Step

External review, then separately authorize validation in a verified provider-capable environment with a new explicit budget. No automatic retry or implementation.

# Review Bundle Contents

Bundle file count: `54`
Bundle ZIP size: `000000243817` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r1_08/08_final_verdict.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r1_08/08_final_verdict.md`.
- `support/artifacts/validation_evidence/atgb_r1_08/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_08/evidence_summary.md`.
- `support/artifacts/validation_evidence/atgb_r1_08/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r1_08/evidence_manifest.json`.
- `support/development/reports/atgb_r1_08/01_baseline_and_readiness.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/01_baseline_and_readiness.md`.
- `support/development/reports/atgb_r1_08/02_live_trial_results.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/02_live_trial_results.md`.
- `support/development/reports/atgb_r1_08/03_interpretation_and_evidence_analysis.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/03_interpretation_and_evidence_analysis.md`.
- `support/development/reports/atgb_r1_08/04_response_adequacy_and_naturalness.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/04_response_adequacy_and_naturalness.md`.
- `support/development/reports/atgb_r1_08/05_mechanical_revision_and_authority.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/05_mechanical_revision_and_authority.md`.
- `support/development/reports/atgb_r1_08/06_historical_comparison.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/06_historical_comparison.md`.
- `support/development/reports/atgb_r1_08/07_provider_accounting.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_08/07_provider_accounting.md`.
- `support/artifacts/atgb/atgb_r1_08/baseline.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/baseline.json`.
- `support/artifacts/atgb/atgb_r1_08/commands.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/commands.json`.
- `support/artifacts/atgb/atgb_r1_08/entry_hashes.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/entry_hashes.json`.
- `support/artifacts/atgb/atgb_r1_08/integrity.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/integrity.json`.
- `support/artifacts/atgb/atgb_r1_08/NEXT_SESSION_before.md`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/NEXT_SESSION_before.md`.
- `support/artifacts/atgb/atgb_r1_08/package_review.py`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/package_review.py`.
- `support/artifacts/atgb/atgb_r1_08/provider_accounting.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/provider_accounting.json`.
- `support/artifacts/atgb/atgb_r1_08/repository_status_after.txt`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/repository_status_after.txt`.
- `support/artifacts/atgb/atgb_r1_08/repository_status_before.txt`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/repository_status_before.txt`.
- `support/artifacts/atgb/atgb_r1_08/run_trial.py`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/run_trial.py`.
- `support/artifacts/atgb/atgb_r1_08/trial_disposition.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/trial_disposition.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/accounting.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/accounting.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/after.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/after.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/before.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/before.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/configuration.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/configuration.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/evidence_selection.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/evidence_selection.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/inherited_environment_names.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/inherited_environment_names.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/preflight.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/preflight.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/provider_usage.jsonl`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_r1_08/L1/request_messages.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/request_messages.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/response.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/response.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/setup.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/setup.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/state_integrity.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/state_integrity.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/timing.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/timing.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/traces.json`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/traces.json`.
- `support/artifacts/atgb/atgb_r1_08/L1/transcript.md`: Explicit scope-relevant review source. Canonical source: `artifacts/atgb/atgb_r1_08/L1/transcript.md`.
- `support/docs/NEXT_SESSION.md`: Explicit scope-relevant review source. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Explicit scope-relevant review source. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/validation_evidence_standard.md`: Explicit scope-relevant review source. Canonical source: `docs/validation_evidence_standard.md`.
- `support/docs/product_realization_validation.md`: Explicit scope-relevant review source. Canonical source: `docs/product_realization_validation.md`.
- `support/game/live_chat_interpretation.py`: Explicit scope-relevant review source. Canonical source: `game/live_chat_interpretation.py`.
- `support/game/conversational_orchestration.py`: Explicit scope-relevant review source. Canonical source: `game/conversational_orchestration.py`.
- `support/tools/atgb/readiness.py`: Explicit scope-relevant review source. Canonical source: `tools/atgb/readiness.py`.
- `support/data/validation/atgb/visible/S08.json`: Explicit scope-relevant review source. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`: Explicit scope-relevant review source. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`.
- `support/development/reports/atgb_r1_05/02_live_trial_results.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_05/02_live_trial_results.md`.
- `support/development/reports/atgb_r1_05/07_provider_accounting.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_05/07_provider_accounting.md`.
- `support/development/reports/atgb_r1_03/02_live_trial_results.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_03/02_live_trial_results.md`.
- `support/development/reports/atgb_r1_04/05_pending_action_control.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_04/05_pending_action_control.md`.
- `support/development/reports/atgb_r1_06/04_evidence_selection_analysis.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_06/04_evidence_selection_analysis.md`.
- `support/development/reports/atgb_r1_07/08_final_verdict.md`: Explicit scope-relevant review source. Canonical source: `development/reports/atgb_r1_07/08_final_verdict.md`.
- `support/artifacts/atgb/atgb_r1_08/review_config.json`: Explicit bundle selection. Canonical source: `artifacts/atgb/atgb_r1_08/review_config.json`.

## Explicit omissions

- `development/reports/atgb_r1_08/08_final_verdict.md`: duplicate content of development/reports/atgb_r1_08/08_final_verdict.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
