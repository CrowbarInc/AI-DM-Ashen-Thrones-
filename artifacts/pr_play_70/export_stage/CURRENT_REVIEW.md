# Campaign

Campaign: Meaningful Player Choice and Branching Consequences
Identifier: `PR-PLAY-70`
Date: 2026-11-05
Generated: 2026-11-06T00:06:18.333367+00:00
Purpose: Review deterministic exclusive branch gameplay with persistent and observable follow-ups.

# Executive Summary

Both branches demonstrated through real HTTP and actual existing browser UI. Qualified evidence: seeded browser sessions, clipped viewport captures, shadow-only provider experiment, incomplete latency attribution. No commit/push.

Objective status: `B — PARTIAL / CORE BRANCHING DEMONSTRATED; QUALIFIED EVIDENCE`.

# Changes Made

## Production changes

- Finite authored consequence schema over existing world flags, action conditions, persistence and trusted HTTP publication.
- Default-off/session-bound Old Milestone scenario with survey/report branches and distinct follow-ups.

## Validation changes

- 42 development tests; frozen once-only 50-case holdout.

## Tooling changes

- Isolated HTTP/browser and bounded provider harnesses.

## Documentation changes

- 23 campaign reports and current session orientation.

## Generated artifacts

- Full sanitized requests/responses, before/after authority, frozen holdout, original provider candidates, browser traces, exact regression failures.

# What Was Tested

- **Focused tests:** 42 development passed; see regression_summary for established lanes.
- **Broader relevant tests:** See exact broader failed node IDs and comparison.
- **Full suite:** Not run; no official ATGB or independent external validation claim.
- **Runtime validation:** 19 TCP gameplay actions; 13 browser actions.
- **Model/runtime boundary:** Four configured provider shadow calls, 1287 tokens, zero AI publications.
- **New regressions:** See regression summary.
- **Pre-existing failures:** Three focused and nine broader in historical baseline.
- **Self-contained bundle review:** 23 requested reports and explicit source/evidence selection with complete player-facing branch text and machine traces.

# Behavioral Evidence

## Evidence Packet: PR-PLAY-70

Runs / turns: `2` / `19`
Runtime/model boundary: Deterministic consequence publication; optional provider candidates shadow-only.

### Representative success

Example: `survey_01`
Player classification: `representative_player_behavior, synthetic_positive_control`
Player: I examine the notice board.
GM: You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.
Automated result: `PASS`
Human review: `UNREVIEWED` - No external human review recorded.
Source: `artifacts/pr_play_70/http_survey.json`

### Representative failure

No example observed in this campaign.

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

Example: `survey_05`
Player classification: `stress_probe, synthetic_negative_control`
Player: Survey the uncertain trail yourself
GM: That choice is not available here. No consequence was applied.
Automated result: `PASS`
Human review: `UNREVIEWED` - No external human review recorded.
Source: `artifacts/pr_play_70/http_survey.json`

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- No approval requested. No commit/push.

# Known Problems / Unresolved Findings

## Campaign-specific

- Browser starts from clean prestarted isolated campaigns.
- Clipped viewport captures; browser-visible latency unmeasured.
- Provider study shadow-only; deterministic branch text published.
- Modest scripted stakes; no broad free-text initiative or concurrent-choice guarantee.

## Pre-existing baseline

- Historical regression failures retained.

# Missing Concepts / Future Capabilities

- Normal browser campaign startup/save-slot resume evidence.

# What This Campaign Does NOT Prove

- Independent external holdout, official ATGB, full suite, open-world agency, concurrent persistence atomicity, live AI publication.

# Recommended Next Step

Complete the existing two-branch experiment through normal New Campaign/Start Campaign and browser save-slot resume, with readable viewport captures and measured browser-visible latency.

# Review Bundle Contents

Bundle file count: `80`
Bundle ZIP size: `000005476548` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_70/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_70/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/validation_evidence/pr_play_70/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/pr_play_70/evidence_summary.md`.
- `support/artifacts/validation_evidence/pr_play_70/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/pr_play_70/evidence_manifest.json`.
- `support/artifacts/pr_play_70/boundary_final.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/boundary_final.txt`.
- `support/artifacts/pr_play_70/broader_final.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/broader_final.txt`.
- `support/artifacts/pr_play_70/browser_report_choices.png`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_report_choices.png`.
- `support/artifacts/pr_play_70/browser_report_continuation.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_report_continuation.txt`.
- `support/artifacts/pr_play_70/browser_report_full.png`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_report_full.png`.
- `support/artifacts/pr_play_70/browser_report_reload.png`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_report_reload.png`.
- `support/artifacts/pr_play_70/browser_report_reload.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_report_reload.txt`.
- `support/artifacts/pr_play_70/browser_survey_continuation.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_survey_continuation.txt`.
- `support/artifacts/pr_play_70/browser_survey_reload.png`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_survey_reload.png`.
- `support/artifacts/pr_play_70/browser_survey_reload.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/browser_survey_reload.txt`.
- `support/artifacts/pr_play_70/development.xml`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/development.xml`.
- `support/artifacts/pr_play_70/development_final.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/development_final.txt`.
- `support/artifacts/pr_play_70/focused_final.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/focused_final.txt`.
- `support/artifacts/pr_play_70/gameplay.py`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/gameplay.py`.
- `support/artifacts/pr_play_70/holdout.py`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/holdout.py`.
- `support/artifacts/pr_play_70/implementation.diff`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/implementation.diff`.
- `support/artifacts/pr_play_70/live_provider.py`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/live_provider.py`.
- `support/artifacts/pr_play_70/package_review.py`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/package_review.py`.
- `support/artifacts/pr_play_70/regression.py`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/regression.py`.
- `support/artifacts/pr_play_70/regression_diagnose.txt`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/regression_diagnose.txt`.
- `support/artifacts/pr_play_70/report.py`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/report.py`.
- `support/artifacts/pr_play_70/review_data/baseline.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/baseline.json`.
- `support/artifacts/pr_play_70/review_data/browser_report_network.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/browser_report_network.json`.
- `support/artifacts/pr_play_70/review_data/browser_results.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/browser_results.json`.
- `support/artifacts/pr_play_70/review_data/browser_survey_network.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/browser_survey_network.json`.
- `support/artifacts/pr_play_70/review_data/complete_payload_scan.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/complete_payload_scan.json`.
- `support/artifacts/pr_play_70/review_data/failure_injection.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/failure_injection.json`.
- `support/artifacts/pr_play_70/review_data/freeze_integrity.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/freeze_integrity.json`.
- `support/artifacts/pr_play_70/review_data/frozen_holdout.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/frozen_holdout.json`.
- `support/artifacts/pr_play_70/review_data/frozen_holdout_manifest.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/frozen_holdout_manifest.json`.
- `support/artifacts/pr_play_70/review_data/holdout_results.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/holdout_results.json`.
- `support/artifacts/pr_play_70/review_data/holdout_summary.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/holdout_summary.json`.
- `support/artifacts/pr_play_70/review_data/http_report.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/http_report.json`.
- `support/artifacts/pr_play_70/review_data/http_summary.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/http_summary.json`.
- `support/artifacts/pr_play_70/review_data/http_survey.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/http_survey.json`.
- `support/artifacts/pr_play_70/review_data/implementation_freeze.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/implementation_freeze.json`.
- `support/artifacts/pr_play_70/review_data/live_provider_results.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/live_provider_results.json`.
- `support/artifacts/pr_play_70/review_data/metrics.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/metrics.json`.
- `support/artifacts/pr_play_70/review_data/protected_integrity.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/protected_integrity.json`.
- `support/artifacts/pr_play_70/review_data/provenance.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/provenance.json`.
- `support/artifacts/pr_play_70/review_data/regression_comparison.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/regression_comparison.json`.
- `support/artifacts/pr_play_70/review_data/regression_summary.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/regression_summary.json`.
- `support/artifacts/pr_play_70/review_data/snapshot_relocation.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/snapshot_relocation.json`.
- `support/artifacts/pr_play_70/review_data/state_integrity.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/state_integrity.json`.
- `support/artifacts/pr_play_70/review_data/verdict.json`: PR70 selected implementation or retained review evidence. Canonical source: `artifacts/pr_play_70/review_data/verdict.json`.
- `support/development/campaigns/product_realization/pr_play_70/02_BASELINE_AND_SCOPE.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/02_BASELINE_AND_SCOPE.md`.
- `support/development/campaigns/product_realization/pr_play_70/03_EXISTING_CONSEQUENCE_ARCHITECTURE.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/03_EXISTING_CONSEQUENCE_ARCHITECTURE.md`.
- `support/development/campaigns/product_realization/pr_play_70/04_SCENARIO_SELECTION.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/04_SCENARIO_SELECTION.md`.
- `support/development/campaigns/product_realization/pr_play_70/05_CHOICE_AND_CONSEQUENCE_CONTRACT.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/05_CHOICE_AND_CONSEQUENCE_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_70/06_IMPLEMENTATION.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/06_IMPLEMENTATION.md`.
- `support/development/campaigns/product_realization/pr_play_70/07_BRANCH_A_GAMEPLAY.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/07_BRANCH_A_GAMEPLAY.md`.
- `support/development/campaigns/product_realization/pr_play_70/08_BRANCH_B_GAMEPLAY.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/08_BRANCH_B_GAMEPLAY.md`.
- `support/development/campaigns/product_realization/pr_play_70/09_BRANCH_COMPARISON.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/09_BRANCH_COMPARISON.md`.
- `support/development/campaigns/product_realization/pr_play_70/10_PERSISTENCE_AND_EXCLUSIVITY.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/10_PERSISTENCE_AND_EXCLUSIVITY.md`.
- `support/development/campaigns/product_realization/pr_play_70/11_FOLLOW_UP_RECOGNITION.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/11_FOLLOW_UP_RECOGNITION.md`.
- `support/development/campaigns/product_realization/pr_play_70/12_DEVELOPMENT_TESTS.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/12_DEVELOPMENT_TESTS.md`.
- `support/development/campaigns/product_realization/pr_play_70/13_FROZEN_HOLDOUT.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/13_FROZEN_HOLDOUT.md`.
- `support/development/campaigns/product_realization/pr_play_70/14_LIVE_HTTP_GAMEPLAY.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/14_LIVE_HTTP_GAMEPLAY.md`.
- `support/development/campaigns/product_realization/pr_play_70/15_LIVE_PROVIDER_RESULTS.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/15_LIVE_PROVIDER_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_70/16_BROWSER_GAMEPLAY.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/16_BROWSER_GAMEPLAY.md`.
- `support/development/campaigns/product_realization/pr_play_70/17_FAILURE_INJECTION.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/17_FAILURE_INJECTION.md`.
- `support/development/campaigns/product_realization/pr_play_70/18_STATE_AND_DISCLOSURE.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/18_STATE_AND_DISCLOSURE.md`.
- `support/development/campaigns/product_realization/pr_play_70/19_PLAYER_SAFE_PROJECTION.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/19_PLAYER_SAFE_PROJECTION.md`.
- `support/development/campaigns/product_realization/pr_play_70/20_PERFORMANCE_AND_QUALITY.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/20_PERFORMANCE_AND_QUALITY.md`.
- `support/development/campaigns/product_realization/pr_play_70/21_REGRESSION_RESULTS.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/21_REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_70/22_LIMITATIONS_AND_OPEN_RISKS.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/22_LIMITATIONS_AND_OPEN_RISKS.md`.
- `support/development/campaigns/product_realization/pr_play_70/23_NEXT_SESSION.md`: PR70 selected implementation or retained review evidence. Canonical source: `development/campaigns/product_realization/pr_play_70/23_NEXT_SESSION.md`.
- `support/docs/NEXT_SESSION.md`: PR70 selected implementation or retained review evidence. Canonical source: `docs/NEXT_SESSION.md`.
- `support/experiments/pr_play_70/scene_actions.json`: PR70 selected implementation or retained review evidence. Canonical source: `experiments/pr_play_70/scene_actions.json`.
- `support/game/api.py`: PR70 selected implementation or retained review evidence. Canonical source: `game/api.py`.
- `support/game/authored_consequences.py`: PR70 selected implementation or retained review evidence. Canonical source: `game/authored_consequences.py`.
- `support/game/exploration.py`: PR70 selected implementation or retained review evidence. Canonical source: `game/exploration.py`.
- `support/game/player_http_projection.py`: PR70 selected implementation or retained review evidence. Canonical source: `game/player_http_projection.py`.
- `support/game/storage.py`: PR70 selected implementation or retained review evidence. Canonical source: `game/storage.py`.
- `support/tests/test_pr_play_70_branching.py`: PR70 selected implementation or retained review evidence. Canonical source: `tests/test_pr_play_70_branching.py`.

## Explicit omissions

- `development/campaigns/product_realization/pr_play_70/01_EXECUTIVE_SUMMARY.md`: duplicate content of development/campaigns/product_realization/pr_play_70/01_EXECUTIVE_SUMMARY.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
