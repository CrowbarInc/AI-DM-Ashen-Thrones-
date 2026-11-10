# Campaign

Campaign: PR-PLAY-61 — Controlled player-facing investigation
Identifier: `pr_play_61`
Date: 2026-11-03
Generated: 2026-11-04T01:48:24.575161+00:00
Purpose: Show a restricted investigation through the application, with validated narration or the engine fallback.

# Executive Summary

# 01 Executive summary

**A — PASS / CONTROLLED GAMEPLAY DEMONSTRATED.**

An isolated copy of the frontier-gate campaign loaded through the application chat route. The player examined the notice board, the rain barrel, the notice board again, and the gate. The engine resolved each action. Two live narrations passed the existing integrated validators and were published. Two candidates failed validation. Their rejected text was not published. After a same-cycle repair, those turns publish the engine sentence instead of the provider-disabled stub. Replaying the saved provider text confirmed that repair without another provider call.

The experimental flag is off by default and is bound to one campaign run id. A second session in the same process kept its ordinary sentence. Inventory, hit points, scene, clues, and NPC attitude matched the provider-disabled control. The only identity difference is the campaign run id.

Provider use: 4 requests, 1663 input tokens, 263 output tokens, 1926 total, 0 retries. Average action-to-response time 2.601 seconds. Maximum 3.331 seconds. Quality is provisional and separate from the validator result: the two published turns are usable; the engine fallback reads as a fact list.

No critical safety failure. No commit and no push.

| Check | Result |
|---|---|
| A Flag disabled | PASS |
| B Flag enabled for one session | PASS |
| C Supported investigation | PASS |
| D Follow-up | PARTIAL — resolved, narration rejected, engine fallback used |
| E Repeated investigation | PASS |
| F Four-action sequence | PASS |
| G Valid narration published | PASS — 2 responses |
| H Invalid narration rejected | PASS |
| I Deterministic fallback | PASS after the same-cycle stub repair |
| J Timeout recovery | PASS |
| K Provider-error recovery | PASS |
| L Validation-error recovery | PASS |
| M State comparison | PASS |
| N Session persistence | PASS |
| O Frontend rendering | PASS — log rendered; one later input accepted |
| P Regression | PASS focused, 3 known failures; 9 known broader failures |
| Q Provider accounting | PASS |
| R Latency | PASS — recorded, not optimized |
| S Quality | PROVISIONAL |


Objective status: `A — PASS / CONTROLLED GAMEPLAY DEMONSTRATED`.

# Changes Made

## Production changes

- Session-scoped publication of a passing investigation sentence, and engine fallback when the only ordinary sentence is the provider-disabled stub.

## Validation changes

- No validator change. PASS is still required before AI prose is published.

## Tooling changes

- One live four-action application run, saved-text replay, fault injection, and the prior focused regression.

## Documentation changes

- 21 numbered reports and the session orientation.

## Generated artifacts

- Provider ledger, per-action results, replay, regression summary, and the player-log screenshot.

# What Was Tested

- **Focused tests:** 741 passed / 3 known failures of 744. Zero new focused failures.
- **Broader relevant tests:** 9/9 authority-assurance failures, each KeyError hard_validation_attempt_1.
- **Full suite:** Not executed.
- **Runtime validation:** Four live application actions, two published narrations, two engine fallbacks on replay, fault injection, and browser rendering.
- **Model/runtime boundary:** OpenAI gpt-4.1-mini-2025-04-14. 4 requests, 1926 tokens, 0 retries.
- **New regressions:** None in the focused suite.
- **Pre-existing failures:** 3 focused failures and 9 broader hard_validation_attempt_1 failures.
- **Self-contained bundle review:** Reports, live results, replay, ledger, regression summary, and the player screenshot are included.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No enablement of the flag for ordinary play. Quality scores are provisional.

# Known Problems / Unresolved Findings

## Campaign-specific

- Rain-barrel and gate narration did not pass. The engine fallback lists every visible fact.

## Pre-existing baseline

- 3 focused failures, 9 broader metadata failures, H03 and H26 false rejections.

# Missing Concepts / Future Capabilities

- A spoken fallback, a faster turn, and any mechanic beyond disclosure and observation.

# What This Campaign Does NOT Prove

- General AI-DM play, inventory, NPC changes, travel, or an ATGB benchmark score.

# Recommended Next Step

Improve investigation responsiveness and replace the catalogue fallback with a short engine sentence. Do not expand the semantic validator.

# Review Bundle Contents

Bundle file count: `38`
Bundle ZIP size: `000000301469` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_61/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_61/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_play_61/broader_hard_validation_final.xml`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/broader_hard_validation_final.xml`.
- `support/artifacts/pr_play_61/experiment_results.json`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/experiment_results.json`.
- `support/artifacts/pr_play_61/focused_final.xml`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/focused_final.xml`.
- `support/artifacts/pr_play_61/frontend/player_log.png`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/frontend/player_log.png`.
- `support/artifacts/pr_play_61/holdout_final.xml`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/holdout_final.xml`.
- `support/artifacts/pr_play_61/provider_usage.jsonl`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/provider_usage.jsonl`.
- `support/artifacts/pr_play_61/regression_summary_final.json`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/regression_summary_final.json`.
- `support/artifacts/pr_play_61/replay_results.json`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/replay_results.json`.
- `support/artifacts/pr_play_61/replay_saved_narration.py`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/replay_saved_narration.py`.
- `support/artifacts/pr_play_61/run_experiment.py`: PR-PLAY-61 implementation, result, or report. Canonical source: `artifacts/pr_play_61/run_experiment.py`.
- `support/development/campaigns/product_realization/pr_play_61/02_BASELINE_AND_SCOPE.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/02_BASELINE_AND_SCOPE.md`.
- `support/development/campaigns/product_realization/pr_play_61/03_APPLICATION_PATHWAY.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/03_APPLICATION_PATHWAY.md`.
- `support/development/campaigns/product_realization/pr_play_61/04_EXPERIMENTAL_FLAG.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/04_EXPERIMENTAL_FLAG.md`.
- `support/development/campaigns/product_realization/pr_play_61/05_CAMPAIGN_AND_SCENE.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/05_CAMPAIGN_AND_SCENE.md`.
- `support/development/campaigns/product_realization/pr_play_61/06_INITIALIZATION_RESULTS.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/06_INITIALIZATION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_61/07_FIRST_INVESTIGATION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/07_FIRST_INVESTIGATION.md`.
- `support/development/campaigns/product_realization/pr_play_61/08_FOLLOW_UP_INVESTIGATION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/08_FOLLOW_UP_INVESTIGATION.md`.
- `support/development/campaigns/product_realization/pr_play_61/09_REPEATED_INVESTIGATION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/09_REPEATED_INVESTIGATION.md`.
- `support/development/campaigns/product_realization/pr_play_61/10_CONTINUATION_ACTION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/10_CONTINUATION_ACTION.md`.
- `support/development/campaigns/product_realization/pr_play_61/11_LIVE_PROVIDER_RESULTS.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/11_LIVE_PROVIDER_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_61/12_PLAYER_FACING_PUBLICATION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/12_PLAYER_FACING_PUBLICATION.md`.
- `support/development/campaigns/product_realization/pr_play_61/13_VALIDATION_AND_FALLBACK.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/13_VALIDATION_AND_FALLBACK.md`.
- `support/development/campaigns/product_realization/pr_play_61/14_STATE_CONTINUITY.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/14_STATE_CONTINUITY.md`.
- `support/development/campaigns/product_realization/pr_play_61/15_FRONTEND_VERIFICATION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/15_FRONTEND_VERIFICATION.md`.
- `support/development/campaigns/product_realization/pr_play_61/16_GAMEPLAY_QUALITY.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/16_GAMEPLAY_QUALITY.md`.
- `support/development/campaigns/product_realization/pr_play_61/17_LATENCY_AND_USAGE.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/17_LATENCY_AND_USAGE.md`.
- `support/development/campaigns/product_realization/pr_play_61/18_FAILURE_INJECTION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/18_FAILURE_INJECTION.md`.
- `support/development/campaigns/product_realization/pr_play_61/19_REGRESSION_RESULTS.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/19_REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_61/20_LIMITATIONS_AND_OPEN_RISKS.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/20_LIMITATIONS_AND_OPEN_RISKS.md`.
- `support/development/campaigns/product_realization/pr_play_61/21_NEXT_SESSION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `development/campaigns/product_realization/pr_play_61/21_NEXT_SESSION.md`.
- `support/docs/NEXT_SESSION.md`: PR-PLAY-61 implementation, result, or report. Canonical source: `docs/NEXT_SESSION.md`.
- `support/game/api.py`: PR-PLAY-61 implementation, result, or report. Canonical source: `game/api.py`.
- `support/game/integrated_investigation_narration.py`: PR-PLAY-61 implementation, result, or report. Canonical source: `game/integrated_investigation_narration.py`.
- `support/game/quarantined_investigation_narration.py`: PR-PLAY-61 implementation, result, or report. Canonical source: `game/quarantined_investigation_narration.py`.
- `support/tests/test_pr_play_61_player_facing.py`: PR-PLAY-61 implementation, result, or report. Canonical source: `tests/test_pr_play_61_player_facing.py`.

## Explicit omissions

- `artifacts/pr_play_61/evidence_summary.md`: source file missing
- `artifacts/pr_play_61/evidence_manifest.json`: source file missing
- `development/campaigns/product_realization/pr_play_61/01_EXECUTIVE_SUMMARY.md`: duplicate content of development/campaigns/product_realization/pr_play_61/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
