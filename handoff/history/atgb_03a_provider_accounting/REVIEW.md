# Campaign

Campaign: ATGB-03A Provider Accounting Safety and Continuation Readiness
Identifier: `atgb_03a_provider_accounting`
Date: 2026-10-18
Generated: 2026-10-18T21:13:39.329078+00:00
Purpose: Investigate accounting and continue only if request usage can be bounded safely.

# Executive Summary

45 provider-disabled tests passed. Three production ledger coverage gaps prevent a safe upper bound. Benchmark entry points now refuse before live dispatch. No new live trials or requests; original 15/37 captured turns preserved. Human scoring pending. User's explicit stop condition applied; full accounting repair and live baseline remain incomplete.

Objective status: `SAFETY CORRECTION VALIDATED; UPPER BOUND UNRESOLVED; LIVE CONTINUATION STOPPED`.

# Changes Made

## Production changes

- None; source hashes match original execution.

## Validation changes

- 21 new accounting checks plus 24 existing infrastructure/readiness checks passed.

## Tooling changes

- ATGB-03A-1 ledger observation/reconciliation and fail-closed readiness gate in runner and direct worker.

## Documentation changes

- Root-cause report, current session orientation, distinct-trial continuation plan.

## Generated artifacts

- Coverage audit, preservation hashes, original raw metadata, usage/latency summaries, unchanged human worksheets and transcripts.

# What Was Tested

- **Focused tests:** 45 passed, 0 failed/errors/skipped; provider-disabled.
- **Broader relevant tests:** Existing provider-disabled chat and all-scenario reset checks included in 45.
- **Full suite:** Not run.
- **Runtime validation:** No additional live execution; original baseline remains partial.
- **Model/runtime boundary:** Original OpenAI gpt-4.1-mini configuration preserved; zero new live calls.
- **New regressions:** None observed in focused scope; live execution intentionally unavailable until accounting is reliable.
- **Pre-existing failures:** Host telemetry missing/incomplete scope; completion-ledger coverage gaps. Interrupted sandbox TestClient attempt retained as environmental limitation.
- **Self-contained bundle review:** Bundle includes original captured transcripts/raw evidence/worksheets, original changed harness source snapshots, new accounting code/tests/JUnit, coverage audit, continuation plan and preservation checks. No human scores created. ZIP contents/hash verification recorded separately.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the fail-closed safety correction and established accounting coverage limitations. No gameplay change proposed.
- Human-score original captured conversations only; retain pending/not-evaluated until authorized judgments are supplied.

# Known Problems / Unresolved Findings

## Campaign-specific

- Reliable universal request upper bound remains unresolved; live continuation refused.
- No supported S04.3 resume continuity; future S04 requires a separate full trial.
- S07/S09 opening context unmeasured.

## Pre-existing baseline

- Original host counters omit expression usage; S04.2 performance absent.
- Ledger does not cover all dispatch owners and unfinished attempts.
- Dirty worktree, previously exposed held-out corpus, unavailable dollar costs/SDK retry counts.

# Missing Concepts / Future Capabilities

- Reliable dispatch lifecycle accounting across provider owners within an approved scope.
- Validated resume/checkpoint continuity; complete live baseline and human scoring.

# What This Campaign Does NOT Prove

- Complete accounting repair or full live baseline completion.
- Zero provider use from absent host telemetry, or exact turn attribution from an untagged ledger.
- Gameplay improvement, semantic success, S07/S09 opening delivery, independent generalization, dollar cost, or SDK-internal retry totals.

# Recommended Next Step

Await review. Do not bypass guard or start gameplay/Product Realization repairs. If separately resolved, rerun S04 as trial 2 and execute S05–S10 with proven request allowance and fresh explicit deadlines, preserving S01–S03 and original partial S04.

# Review Bundle Contents

Bundle file count: `148`
Bundle ZIP size: `000000673690` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_03a_provider_accounting.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_03a_provider_accounting.md`.
- `support/artifacts/atgb/atgb_02a/validation_results.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_02a/validation_results.json`.
- `support/artifacts/atgb/atgb_03/S01/provider_usage.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/report.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/report.md`.
- `support/artifacts/atgb/atgb_03/S01/result.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/result.json`.
- `support/artifacts/atgb/atgb_03/S01/review_status.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/review_status.md`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-job.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-worker.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/combat.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/combat.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session.json`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session_log.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/world.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/world.json`.
- `support/artifacts/atgb/atgb_03/S01/transcript.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/transcript.md`.
- `support/artifacts/atgb/atgb_03/S01/wall_clock.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S01/worksheet.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S01/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S02/execution_status.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/execution_status.json`.
- `support/artifacts/atgb/atgb_03/S02/provider_usage.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/report.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/report.md`.
- `support/artifacts/atgb/atgb_03/S02/result.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/result.json`.
- `support/artifacts/atgb/atgb_03/S02/review_status.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/review_status.md`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-job.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-worker.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/combat.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/combat.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session.json`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S02/transcript.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/transcript.md`.
- `support/artifacts/atgb/atgb_03/S02/wall_clock.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S02/worksheet.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S02/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S03/execution_status.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/execution_status.json`.
- `support/artifacts/atgb/atgb_03/S03/provider_usage.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/report.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/report.md`.
- `support/artifacts/atgb/atgb_03/S03/result.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/result.json`.
- `support/artifacts/atgb/atgb_03/S03/review_status.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/review_status.md`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-job.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-worker.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/combat.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/combat.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session.json`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session_log.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/world.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/stores/S03-c362fa85652f4ba0bc78f824299b0857/world.json`.
- `support/artifacts/atgb/atgb_03/S03/transcript.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/transcript.md`.
- `support/artifacts/atgb/atgb_03/S03/wall_clock.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S03/worksheet.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S03/worksheet.md`.
- `support/artifacts/atgb/atgb_03/S04/execution_status.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/execution_status.json`.
- `support/artifacts/atgb/atgb_03/S04/provider_usage.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/provider_usage.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/report.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/report.md`.
- `support/artifacts/atgb/atgb_03/S04/result.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/result.json`.
- `support/artifacts/atgb/atgb_03/S04/review_status.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/review_status.md`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-job.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-job.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-worker.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/atgb-worker.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/combat.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/combat.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session.json`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session_log.jsonl`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/world.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/stores/S04-e95de1cdbcfa4c4d8812b9a801af39d7/world.json`.
- `support/artifacts/atgb/atgb_03/S04/transcript.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/transcript.md`.
- `support/artifacts/atgb/atgb_03/S04/wall_clock.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/wall_clock.json`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.json`.
- `support/artifacts/atgb/atgb_03/S04/worksheet.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/S04/worksheet.md`.
- `support/artifacts/atgb/atgb_03/campaign_clock.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/campaign_clock.json`.
- `support/artifacts/atgb/atgb_03/campaign_stop.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/campaign_stop.json`.
- `support/artifacts/atgb/atgb_03/configuration_and_provenance.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/configuration_and_provenance.json`.
- `support/artifacts/atgb/atgb_03/evaluation_status.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/evaluation_status.json`.
- `support/artifacts/atgb/atgb_03/execute.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/execute.py`.
- `support/artifacts/atgb/atgb_03/execution_blocker.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/execution_blocker.json`.
- `support/artifacts/atgb/atgb_03/execution_summary.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/execution_summary.json`.
- `support/artifacts/atgb/atgb_03/finalize_live.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/finalize_live.py`.
- `support/artifacts/atgb/atgb_03/focused.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/focused.txt`.
- `support/artifacts/atgb/atgb_03/focused.xml`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/focused.xml`.
- `support/artifacts/atgb/atgb_03/focused_host.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/focused_host.txt`.
- `support/artifacts/atgb/atgb_03/focused_host.xml`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/focused_host.xml`.
- `support/artifacts/atgb/atgb_03/focused_retry.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/focused_retry.txt`.
- `support/artifacts/atgb/atgb_03/host_check.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/host_check.txt`.
- `support/artifacts/atgb/atgb_03/host_check.xml`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/host_check.xml`.
- `support/artifacts/atgb/atgb_03/initial_git_status.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/initial_git_status.txt`.
- `support/artifacts/atgb/atgb_03/preflight/report.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/preflight/report.md`.
- `support/artifacts/atgb/atgb_03/preflight/result.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/preflight/result.json`.
- `support/artifacts/atgb/atgb_03/preflight/worksheet.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/preflight/worksheet.json`.
- `support/artifacts/atgb/atgb_03/preflight/worksheet.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/preflight/worksheet.md`.
- `support/artifacts/atgb/atgb_03/prepare.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/prepare.py`.
- `support/artifacts/atgb/atgb_03/preservation_checks.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/preservation_checks.json`.
- `support/artifacts/atgb/atgb_03/provider_telemetry.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/provider_telemetry.json`.
- `support/artifacts/atgb/atgb_03/resume_checks.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/resume_checks.json`.
- `support/artifacts/atgb/atgb_03/scenario_status.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/scenario_status.json`.
- `support/artifacts/atgb/atgb_03/stage_a_acceptance.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/stage_a_acceptance.json`.
- `support/artifacts/atgb/atgb_03/stage_a_console.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/stage_a_console.txt`.
- `support/artifacts/atgb/atgb_03/stage_b_console.txt`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/stage_b_console.txt`.
- `support/artifacts/atgb/atgb_03/turn_telemetry.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/turn_telemetry.json`.
- `support/artifacts/atgb/atgb_03/validation_results.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/validation_results.json`.
- `support/artifacts/atgb/atgb_03/verify_bundle.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/verify_bundle.py`.
- `support/artifacts/atgb/atgb_03/worksheet.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/worksheet.json`.
- `support/artifacts/atgb/atgb_03/worksheet.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03/worksheet.md`.
- `support/artifacts/atgb/atgb_03a/accounting_readiness.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/accounting_readiness.json`.
- `support/artifacts/atgb/atgb_03a/continuation_plan.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/continuation_plan.json`.
- `support/artifacts/atgb/atgb_03a/deterministic_host.xml`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/deterministic_host.xml`.
- `support/artifacts/atgb/atgb_03a/execution_status.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/execution_status.json`.
- `support/artifacts/atgb/atgb_03a/inspect_evidence.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/inspect_evidence.py`.
- `support/artifacts/atgb/atgb_03a/original_accounting_analysis.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/original_accounting_analysis.json`.
- `support/artifacts/atgb/atgb_03a/original_harness/chat_worker.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/original_harness/chat_worker.py`.
- `support/artifacts/atgb/atgb_03a/original_harness/driver.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/original_harness/driver.py`.
- `support/artifacts/atgb/atgb_03a/package_review.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/package_review.py`.
- `support/artifacts/atgb/atgb_03a/preservation_before.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/preservation_before.json`.
- `support/artifacts/atgb/atgb_03a/preservation_checks.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/preservation_checks.json`.
- `support/artifacts/atgb/atgb_03a/validation_results.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `artifacts/atgb/atgb_03a/validation_results.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/manifest.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/world.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/world.json`.
- `support/data/validation/atgb/corpus.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/held_out/S07.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/data/validation/atgb/visible/S01.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02_execution.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `development/reports/atgb_02_execution.md`.
- `support/development/reports/atgb_02a_readiness.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `development/reports/atgb_02a_readiness.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/review_handoff_standard.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `docs/review_handoff_standard.md`.
- `support/docs/validation_evidence_standard.md`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `docs/validation_evidence_standard.md`.
- `support/tests/test_atgb_accounting.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tests/test_atgb_accounting.py`.
- `support/tools/atgb/__init__.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/__init__.py`.
- `support/tools/atgb/accounting.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/accounting.py`.
- `support/tools/atgb/baseline.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/baseline.py`.
- `support/tools/atgb/budget.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/budget.py`.
- `support/tools/atgb/chat_worker.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/chat_worker.py`.
- `support/tools/atgb/driver.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/driver.py`.
- `support/tools/atgb/fixtures.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/fixtures.py`.
- `support/tools/atgb/isolation.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/isolation.py`.
- `support/tools/atgb/preflight.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/preflight.py`.
- `support/tools/atgb/results.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/results.py`.
- `support/tools/atgb/worksheet.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/atgb/worksheet.py`.
- `support/tools/run_atgb.py`: Review safety correction and distinguish preserved original observations from blocked/unmeasured continuation. Canonical source: `tools/run_atgb.py`.

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
- `artifacts/atgb/atgb_03a/original_provider_telemetry.json`: duplicate content of artifacts/atgb/atgb_03/provider_telemetry.json; canonical reference retained
- `artifacts/atgb/atgb_03a/original_turn_telemetry.json`: duplicate content of artifacts/atgb/atgb_03/turn_telemetry.json; canonical reference retained
- `artifacts/atgb/atgb_03a/original_worksheet.json`: duplicate content of artifacts/atgb/atgb_03/worksheet.json; canonical reference retained
- `artifacts/atgb/atgb_03a/original_worksheet.md`: duplicate content of artifacts/atgb/atgb_03/worksheet.md; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/campaign.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/campaign.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/character.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/character.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/conditions.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/conditions.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/frontier_gate.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/market_quarter.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/market_quarter.json; canonical reference retained
- `data/validation/atgb/baselines/frontier-gate-v1/scenes/old_milestone.json`: duplicate content of artifacts/atgb/atgb_03/S01/stores/S01-a0517ef32bc3401ba41fcbcf915d82c0/scenes/old_milestone.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
