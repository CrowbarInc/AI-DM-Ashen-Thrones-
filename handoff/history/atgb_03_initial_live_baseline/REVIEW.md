# Campaign

Campaign: ATGB-03 Initial Live Conversational Baseline
Identifier: `atgb_03_initial_live_baseline`
Date: 2026-10-18
Generated: 2026-10-18T21:04:41.616498+00:00
Purpose: Observe existing player–AI-DM behavior through the approved benchmark and preserve a partial run after its accounting guard stopped execution.

# Executive Summary

S01–S03 completed; S04 stopped after two turns because its provider-call counter became unavailable. Captured 15/37 turns, 12 provider requests. S05–S10 not attempted. All human judgments pending; no gameplay score or production change. Explicit OpenAI approval was supplied after the initial rejected command.

Objective status: `PARTIAL LIVE BASELINE; INFRASTRUCTURE STOP AT S04; HUMAN REVIEW PENDING`.

# Changes Made

## Production changes

- None; canonical campaign and all recorded execution sources unchanged.

## Validation changes

- Existing 24 focused provider-disabled tests passed; four live starting preflights passed.

## Tooling changes

- Campaign wrapper only; approved harness unchanged.

## Documentation changes

- Partial execution report and current NEXT_SESSION orientation.

## Generated artifacts

- 15 raw captured exchanges, independent provider ledger, state/log evidence, existing human worksheets and explicit pending/not-evaluated reporting.

# What Was Tested

- **Focused tests:** 24 passed in preparation.
- **Broader relevant tests:** Separate existing provider-disabled production chat test passed.
- **Full suite:** Not run.
- **Runtime validation:** S01 passed live infrastructure acceptance; S02/S03 complete; S04 stopped before third turn.
- **Model/runtime boundary:** OpenAI gpt-4.1-mini; 12 recorded requests, no narration requests; host-owned replies preserved.
- **New regressions:** No code change; missing runtime accounting is an observed infrastructure limitation.
- **Pre-existing failures:** Sandbox startup limitations and initial pytest-directory setup attempt preserved separately.
- **Self-contained bundle review:** ZIP includes exact captured conversations, per-turn context/rubric worksheets, isolated state/logs, provider ledger, missing-counter evidence, status roster, hashes and the pending-human-review boundary.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review partial transcripts using separate interpretation, response adequacy and authority judgments; no scores supplied.
- Review missing performance accounting and expression-call underreporting before a separately reviewed readiness correction/new live baseline. Do not repair gameplay during evaluation.

# Known Problems / Unresolved Findings

## Campaign-specific

- S04.2 lacks performance metadata; approved harness stopped before S04.3.
- Provider ledger includes S03.2 expression request missing from host turn counter.
- 22 turns unsubmitted; S07/S09 opening delivery not evaluated.

## Pre-existing baseline

- Previously exposed held-out corpus.
- Dirty worktree means HEAD alone is insufficient provenance.
- No browser-rendered UI validation.

# Missing Concepts / Future Capabilities

- Complete live execution and authorized human scoring.
- Reliable benchmark accounting across all existing response paths.

# What This Campaign Does NOT Prove

- Full baseline completion, gameplay improvement or any aggregate gameplay score.
- Unscored semantic adequacy or authority compliance.
- S07/S09 opening delivery or held-out/independent generalization.
- Complete cost telemetry or SDK-internal retry counts.

# Recommended Next Step

Review the partial evidence and accounting blocker. Require separately reviewed infrastructure readiness before another live attempt. Human-score only captured turns with sufficient evidence; leave others not evaluated. No gameplay repair.

# Review Bundle Contents

Bundle file count: `134`
Bundle ZIP size: `000000601864` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_03_initial_live_baseline.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_03_initial_live_baseline.md`.
- `support/artifacts/atgb/atgb_02a/validation_results.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_02a/validation_results.json`.
- `support/artifacts/atgb/atgb_03/campaign_clock.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/campaign_clock.json`.
- `support/artifacts/atgb/atgb_03/campaign_stop.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/campaign_stop.json`.
- `support/artifacts/atgb/atgb_03/configuration_and_provenance.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/configuration_and_provenance.json`.
- `support/artifacts/atgb/atgb_03/evaluation_status.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/evaluation_status.json`.
- `support/artifacts/atgb/atgb_03/execute.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/execute.py`.
- `support/artifacts/atgb/atgb_03/execution_blocker.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/execution_blocker.json`.
- `support/artifacts/atgb/atgb_03/execution_summary.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/execution_summary.json`.
- `support/artifacts/atgb/atgb_03/finalize_live.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/finalize_live.py`.
- `support/artifacts/atgb/atgb_03/focused.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/focused.txt`.
- `support/artifacts/atgb/atgb_03/focused.xml`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/focused.xml`.
- `support/artifacts/atgb/atgb_03/focused_host.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/focused_host.txt`.
- `support/artifacts/atgb/atgb_03/focused_host.xml`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/focused_host.xml`.
- `support/artifacts/atgb/atgb_03/focused_retry.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/focused_retry.txt`.
- `support/artifacts/atgb/atgb_03/host_check.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/host_check.txt`.
- `support/artifacts/atgb/atgb_03/host_check.xml`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/host_check.xml`.
- `support/artifacts/atgb/atgb_03/initial_git_status.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/initial_git_status.txt`.
- `support/artifacts/atgb/atgb_03/preflight/report.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/preflight/report.md`.
- `support/artifacts/atgb/atgb_03/preflight/result.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/preflight/result.json`.
- `support/artifacts/atgb/atgb_03/preflight/worksheet.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/preflight/worksheet.json`.
- `support/artifacts/atgb/atgb_03/preflight/worksheet.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/preflight/worksheet.md`.
- `support/artifacts/atgb/atgb_03/prepare.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/prepare.py`.
- `support/artifacts/atgb/atgb_03/preservation_checks.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/preservation_checks.json`.
- `support/artifacts/atgb/atgb_03/provider_telemetry.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/provider_telemetry.json`.
- `support/artifacts/atgb/atgb_03/resume_checks.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/resume_checks.json`.
- `support/artifacts/atgb/atgb_03/S01/provider_usage.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/report.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/report.md`.
- `support/artifacts/atgb/atgb_03/S01/result.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/result.json`.
- `support/artifacts/atgb/atgb_03/S01/review_status.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/review_status.md`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-job.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-worker.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/combat.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/combat.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session_log.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/world.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/world.json`.
- `support/artifacts/atgb/atgb_03/S01/transcript.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/transcript.md`.
- `support/artifacts/atgb/atgb_03/S01/wall_clock.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S02/execution_status.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/execution_status.json`.
- `support/artifacts/atgb/atgb_03/S02/provider_usage.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/report.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/report.md`.
- `support/artifacts/atgb/atgb_03/S02/result.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/result.json`.
- `support/artifacts/atgb/atgb_03/S02/review_status.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/review_status.md`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-job.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-worker.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/combat.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/combat.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/transcript.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/transcript.md`.
- `support/artifacts/atgb/atgb_03/S02/wall_clock.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S03/execution_status.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/execution_status.json`.
- `support/artifacts/atgb/atgb_03/S03/provider_usage.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/report.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/report.md`.
- `support/artifacts/atgb/atgb_03/S03/result.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/result.json`.
- `support/artifacts/atgb/atgb_03/S03/review_status.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/review_status.md`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-job.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-worker.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/combat.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/combat.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session_log.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/world.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/world.json`.
- `support/artifacts/atgb/atgb_03/S03/transcript.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/transcript.md`.
- `support/artifacts/atgb/atgb_03/S03/wall_clock.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S04/execution_status.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/execution_status.json`.
- `support/artifacts/atgb/atgb_03/S04/provider_usage.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/report.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/report.md`.
- `support/artifacts/atgb/atgb_03/S04/result.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/result.json`.
- `support/artifacts/atgb/atgb_03/S04/review_status.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/review_status.md`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-job.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-worker.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/combat.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/combat.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session_log.jsonl`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/world.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/world.json`.
- `support/artifacts/atgb/atgb_03/S04/transcript.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03/S04/wall_clock.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.md`.
- `support/artifacts/atgb/atgb_03/scenario_status.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/scenario_status.json`.
- `support/artifacts/atgb/atgb_03/stage_a_acceptance.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/stage_a_acceptance.json`.
- `support/artifacts/atgb/atgb_03/stage_a_console.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/stage_a_console.txt`.
- `support/artifacts/atgb/atgb_03/stage_b_console.txt`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/stage_b_console.txt`.
- `support/artifacts/atgb/atgb_03/turn_telemetry.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/turn_telemetry.json`.
- `support/artifacts/atgb/atgb_03/validation_results.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/validation_results.json`.
- `support/artifacts/atgb/atgb_03/verify_bundle.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/verify_bundle.py`.
- `support/artifacts/atgb/atgb_03/worksheet.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/worksheet.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `artifacts/atgb/atgb_03/worksheet.md`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/manifest.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/world.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/world.json`.
- `support/data/validation/atgb/corpus.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/held_out/S07.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/data/validation/atgb/visible/S01.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02_execution.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `development/reports/atgb_02_execution.md`.
- `support/development/reports/atgb_02a_readiness.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `development/reports/atgb_02a_readiness.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/review_handoff_standard.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `docs/review_handoff_standard.md`.
- `support/docs/validation_evidence_standard.md`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `docs/validation_evidence_standard.md`.
- `support/tools/atgb/__init__.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/__init__.py`.
- `support/tools/atgb/baseline.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/baseline.py`.
- `support/tools/atgb/budget.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/budget.py`.
- `support/tools/atgb/chat_worker.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/chat_worker.py`.
- `support/tools/atgb/driver.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/driver.py`.
- `support/tools/atgb/fixtures.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/fixtures.py`.
- `support/tools/atgb/isolation.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/isolation.py`.
- `support/tools/atgb/preflight.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/preflight.py`.
- `support/tools/atgb/results.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/results.py`.
- `support/tools/atgb/worksheet.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/atgb/worksheet.py`.
- `support/tools/run_atgb.py`: Review actual exchanges, state and telemetry independently; distinguish execution from pending judgments. Canonical source: `tools/run_atgb.py`.

## Explicit omissions

- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/campaign.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/character.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json; canonical reference retained
- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/conditions.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/world.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/world.json; canonical reference retained
- `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/campaign.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/character.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json; canonical reference retained
- `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/conditions.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json; canonical reference retained
- `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/campaign.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json; canonical reference retained
- `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/character.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json; canonical reference retained
- `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/conditions.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json; canonical reference retained
- `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json; canonical reference retained
- `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json; canonical reference retained
- `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/campaign.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/character.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/conditions.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
