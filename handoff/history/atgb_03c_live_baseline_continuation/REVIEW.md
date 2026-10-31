# Campaign

Campaign: ATGB-03C Initial Live Conversational Baseline Continuation
Identifier: `atgb_03c_live_baseline_continuation`
Date: 2026-10-18
Generated: 2026-10-18T22:35:40.285633+00:00
Purpose: Capture the remaining approved live conversations using verified ATGB-03B accounting without changing gameplay.

# Executive Summary

24 new turns; 37/37 unique baseline turns available. S04 full trial 2 is separate from original partial trial 1. 23 admissions reconciled. S07/S09 opening delivery absent before first turn; inspect setup caveats before scoring. All judgments pending; no gameplay-performance result or improvement claim.

Objective status: `24/24 CONTINUATION TURNS CAPTURED; HUMAN REVIEW PENDING; OPENING DELIVERY LIMITED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No criteria or rubric changes. Provider-disabled readiness and dispatch-owner tests rerun.

## Tooling changes

- Campaign-only preparation/execution/packaging wrappers under artifacts/atgb/atgb_03c; reviewed harness unchanged.

## Documentation changes

- Execution report, coverage summary, current session orientation.

## Generated artifacts

- Seven scenario evidence packages, raw ledgers, isolation/preflight evidence, opening context analysis, approved scoring worksheets and review ZIP.

# What Was Tested

- **Focused tests:** 104 checks: 103 pass, 1 Windows reset failure; targeted reset reproducibility retry passes. All evidence retained.
- **Broader relevant tests:** No broad regression rerun; production source unchanged.
- **Full suite:** Not run.
- **Runtime validation:** 24 live API player turns; ten final provider-disabled preflights; per-live-scenario preflights.
- **Model/runtime boundary:** OpenAI gpt-4.1-mini; unchanged model routing; TestClient production API, no browser render check.
- **New regressions:** No production change. Opening setup limitations are exposed, not repaired.
- **Pre-existing failures:** Historical unrelated regression failures unchanged; Windows reset denial retained.
- **Self-contained bundle review:** Bundle verification checks required review sections, every packaged canonical hash, exact approved lines and order, 24 new and 37 unique worksheet rows with no human judgments, original partial S04 separation, lifecycle reconciliation, starting-state evidence and all seven transcripts.

# Behavioral Evidence

## Evidence Packet: atgb_03c_live_baseline_continuation

Runs / turns: `7` / `24`
Runtime/model boundary: Live-enabled OpenAI gpt-4.1-mini with existing host-owned replies and model roles; no browser UI validation

### Representative success

No example observed in this campaign.

### Representative failure

No example observed in this campaign.

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review exact exchanges and opening setup limitations; assign interpretation, response and authority separately with uncertain/not evaluated where unsupported.
- Do not treat this captured baseline as completed gameplay-performance measurement before human review. No repair campaign authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- S07/S09 authored opening context was not delivered before fixture turns; dependent outcomes unmeasured.
- Every human judgment remains pending.
- Dollar expenditure and SDK transport retry counts unavailable.

## Pre-existing baseline

- Original S04 partial telemetry remains unavailable and completion-only historical ledger cannot certify admissions.
- Extensive pre-existing dirty worktree and transient Windows reset write denials.

# Missing Concepts / Future Capabilities

- Delivered opening context is not part of the approved silent-reset chat worker. No new opening injection implemented.

# What This Campaign Does NOT Prove

- Conversational improvement, judged gameplay success, independent held-out generalization, multi-environment performance, full regression, browser rendering or absolute SDK transport request bounds.

# Recommended Next Step

Stop and await human review. Score only supported criteria; retain original/continuation version provenance and separate historical partial S04.

# Review Bundle Contents

Bundle file count: `202`
Bundle ZIP size: `000001046101` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_03c_live_baseline_continuation.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_03c_live_baseline_continuation.md`.
- `support/artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`.
- `support/artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`.
- `support/artifacts/atgb/atgb_03/S01/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S01/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S01/result.json`.
- `support/artifacts/atgb/atgb_03/S01/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S01/transcript.md`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S02/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S02/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S02/result.json`.
- `support/artifacts/atgb/atgb_03/S02/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S02/transcript.md`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S03/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S03/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S03/result.json`.
- `support/artifacts/atgb/atgb_03/S03/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S03/transcript.md`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S04/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S04/result.json`.
- `support/artifacts/atgb/atgb_03/S04/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/accounting_readiness.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/accounting_readiness.json`.
- `support/artifacts/atgb/atgb_03c/baseline_coverage.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/baseline_coverage.json`.
- `support/artifacts/atgb/atgb_03c/baseline_coverage.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/baseline_coverage.md`.
- `support/artifacts/atgb/atgb_03c/campaign_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/campaign_clock.json`.
- `support/artifacts/atgb/atgb_03c/campaign_usage.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/campaign_usage.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_review_source.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_review_source.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_worksheet.json`.
- `support/artifacts/atgb/atgb_03c/combined_baseline_worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/combined_baseline_worksheet.md`.
- `support/artifacts/atgb/atgb_03c/continuation_review_source.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/continuation_review_source.json`.
- `support/artifacts/atgb/atgb_03c/continuation_worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/continuation_worksheet.json`.
- `support/artifacts/atgb/atgb_03c/continuation_worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/continuation_worksheet.md`.
- `support/artifacts/atgb/atgb_03c/execute.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/execute.py`.
- `support/artifacts/atgb/atgb_03c/export_authorization.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/export_authorization.json`.
- `support/artifacts/atgb/atgb_03c/finalize.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/finalize.py`.
- `support/artifacts/atgb/atgb_03c/focused.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/focused.txt`.
- `support/artifacts/atgb/atgb_03c/focused_unsandboxed.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/focused_unsandboxed.txt`.
- `support/artifacts/atgb/atgb_03c/focused_unsandboxed.xml`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/focused_unsandboxed.xml`.
- `support/artifacts/atgb/atgb_03c/initial_git_status.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/initial_git_status.txt`.
- `support/artifacts/atgb/atgb_03c/live_console.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/live_console.txt`.
- `support/artifacts/atgb/atgb_03c/opening_context.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/opening_context.json`.
- `support/artifacts/atgb/atgb_03c/preflight/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight/report.md`.
- `support/artifacts/atgb/atgb_03c/preflight/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight/result.json`.
- `support/artifacts/atgb/atgb_03c/preflight/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/preflight/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/preflight_console.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight_console.txt`.
- `support/artifacts/atgb/atgb_03c/preflight_final/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight_final/report.md`.
- `support/artifacts/atgb/atgb_03c/preflight_final/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight_final/result.json`.
- `support/artifacts/atgb/atgb_03c/preflight_final_console.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight_final_console.txt`.
- `support/artifacts/atgb/atgb_03c/preflight_verified/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight_verified/report.md`.
- `support/artifacts/atgb/atgb_03c/preflight_verified/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preflight_verified/result.json`.
- `support/artifacts/atgb/atgb_03c/prepare.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/prepare.py`.
- `support/artifacts/atgb/atgb_03c/preservation_checks.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/preservation_checks.json`.
- `support/artifacts/atgb/atgb_03c/provenance_before.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/provenance_before.json`.
- `support/artifacts/atgb/atgb_03c/provider_accounting.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/provider_accounting.json`.
- `support/artifacts/atgb/atgb_03c/reset_retry.txt`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/reset_retry.txt`.
- `support/artifacts/atgb/atgb_03c/reset_retry.xml`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/reset_retry.xml`.
- `support/artifacts/atgb/atgb_03c/S04/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S04/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S04/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/report.md`.
- `support/artifacts/atgb/atgb_03c/S04/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/result.json`.
- `support/artifacts/atgb/atgb_03c/S04/review_status.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/review_status.md`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/combat.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/session.json`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/world.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/world.json`.
- `support/artifacts/atgb/atgb_03c/S04/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S04/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S04/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S04/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S04/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/S05/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S05/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S05/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/report.md`.
- `support/artifacts/atgb/atgb_03c/S05/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/result.json`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/combat.json`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/session.json`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/world.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/world.json`.
- `support/artifacts/atgb/atgb_03c/S05/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S05/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S05/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S05/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S05/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/S06/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S06/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S06/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/report.md`.
- `support/artifacts/atgb/atgb_03c/S06/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/result.json`.
- `support/artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/combat.json`.
- `support/artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/session.json`.
- `support/artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/world.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/world.json`.
- `support/artifacts/atgb/atgb_03c/S06/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S06/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S06/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S06/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S06/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/S07/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S07/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S07/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/report.md`.
- `support/artifacts/atgb/atgb_03c/S07/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/result.json`.
- `support/artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/combat.json`.
- `support/artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/session.json`.
- `support/artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/world.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/world.json`.
- `support/artifacts/atgb/atgb_03c/S07/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S07/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S07/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S07/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S07/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/S08/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S08/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/report.md`.
- `support/artifacts/atgb/atgb_03c/S08/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/result.json`.
- `support/artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/combat.json`.
- `support/artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/session.json`.
- `support/artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S08/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S08/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S08/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S08/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S08/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/S09/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S09/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S09/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/report.md`.
- `support/artifacts/atgb/atgb_03c/S09/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/result.json`.
- `support/artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/combat.json`.
- `support/artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/session.json`.
- `support/artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S09/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S09/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S09/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S09/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S09/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/S10/execution_status.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/execution_status.json`.
- `support/artifacts/atgb/atgb_03c/S10/provider_usage.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03c/S10/report.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/report.md`.
- `support/artifacts/atgb/atgb_03c/S10/result.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/result.json`.
- `support/artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/atgb-job.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/atgb-job.json`.
- `support/artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/atgb-worker.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/combat.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/combat.json`.
- `support/artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/session.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/session.json`.
- `support/artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/session_log.jsonl`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S10/transcript.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/transcript.md`.
- `support/artifacts/atgb/atgb_03c/S10/wall_clock.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/wall_clock.json`.
- `support/artifacts/atgb/atgb_03c/S10/worksheet.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/worksheet.json`.
- `support/artifacts/atgb/atgb_03c/S10/worksheet.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/S10/worksheet.md`.
- `support/artifacts/atgb/atgb_03c/scenario_readiness.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/scenario_readiness.json`.
- `support/artifacts/atgb/atgb_03c/turn_latency.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/turn_latency.json`.
- `support/artifacts/atgb/atgb_03c/validation_results.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/validation_results.json`.
- `support/artifacts/atgb/atgb_03c/verify_bundle.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `artifacts/atgb/atgb_03c/verify_bundle.py`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/manifest.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/world.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/world.json`.
- `support/data/validation/atgb/corpus.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/held_out/S07.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/data/validation/atgb/README.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/README.md`.
- `support/data/validation/atgb/visible/S01.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02_execution.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `development/reports/atgb_02_execution.md`.
- `support/development/reports/atgb_03_initial_live_baseline.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `development/reports/atgb_03_initial_live_baseline.md`.
- `support/development/reports/atgb_03b_provider_accounting_integrity.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `development/reports/atgb_03b_provider_accounting_integrity.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/validation_evidence_standard.md`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `docs/validation_evidence_standard.md`.
- `support/tools/atgb/__init__.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/__init__.py`.
- `support/tools/atgb/accounting.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/accounting.py`.
- `support/tools/atgb/baseline.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/baseline.py`.
- `support/tools/atgb/budget.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/budget.py`.
- `support/tools/atgb/chat_worker.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/chat_worker.py`.
- `support/tools/atgb/driver.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/driver.py`.
- `support/tools/atgb/fixtures.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/fixtures.py`.
- `support/tools/atgb/isolation.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/isolation.py`.
- `support/tools/atgb/preflight.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/preflight.py`.
- `support/tools/atgb/provider_accounting_integrity.json`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/provider_accounting_integrity.json`.
- `support/tools/atgb/results.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/results.py`.
- `support/tools/atgb/worksheet.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/atgb/worksheet.py`.
- `support/tools/run_atgb.py`: Review capture, provenance, safeguards, setup limitations and pending human judgments. Canonical source: `tools/run_atgb.py`.

## Explicit omissions

- `artifacts/atgb/atgb_03c/accounting_readiness_final.json`: duplicate content of artifacts/atgb/atgb_03c/accounting_readiness.json; canonical reference retained
- `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json`: duplicate content of artifacts/atgb/atgb_03c/behavioral_evidence/evidence_manifest.json; canonical reference retained
- `artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md`: duplicate content of artifacts/atgb/atgb_03c/behavioral_evidence/evidence_summary.md; canonical reference retained
- `artifacts/atgb/atgb_03c/preflight_final/worksheet.json`: duplicate content of artifacts/atgb/atgb_03c/preflight/worksheet.json; canonical reference retained
- `artifacts/atgb/atgb_03c/preflight_final/worksheet.md`: duplicate content of artifacts/atgb/atgb_03c/preflight/worksheet.md; canonical reference retained
- `artifacts/atgb/atgb_03c/preflight_verified/worksheet.json`: duplicate content of artifacts/atgb/atgb_03c/preflight/worksheet.json; canonical reference retained
- `artifacts/atgb/atgb_03c/preflight_verified/worksheet.md`: duplicate content of artifacts/atgb/atgb_03c/preflight/worksheet.md; canonical reference retained
- `artifacts/atgb/atgb_03c/preflight_verified_console.txt`: duplicate content of artifacts/atgb/atgb_03c/preflight_console.txt; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/review_status.md`: duplicate content of artifacts/atgb/atgb_03c/S04/review_status.md; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/review_status.md`: duplicate content of artifacts/atgb/atgb_03c/S04/review_status.md; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S06/stores/S06-7f62abef6b7b4945a1f627dae3e8fe27/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/review_status.md`: duplicate content of artifacts/atgb/atgb_03c/S04/review_status.md; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/review_status.md`: duplicate content of artifacts/atgb/atgb_03c/S04/review_status.md; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S08/stores/S08-e240c44229974598913550ba33beaef0/world.json`: duplicate content of artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/world.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/review_status.md`: duplicate content of artifacts/atgb/atgb_03c/S04/review_status.md; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S09/stores/S09-73332f0ff6384b34879d077261a74fbe/world.json`: duplicate content of artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/world.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/review_status.md`: duplicate content of artifacts/atgb/atgb_03c/S04/review_status.md; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03c/S10/stores/S10-732cbd6e6ad54ea7b6beda6a30e99916/world.json`: duplicate content of artifacts/atgb/atgb_03c/S07/stores/S07-e3a05606ef94461a9863a6bdc9923d25/world.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/campaign.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/campaign.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/character.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/character.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/conditions.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/conditions.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/frontier_gate.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/market_quarter.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03c/S04/stores/S04-316953d82e4b446683c7f6c06fac9b76/scenes/old_milestone.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
