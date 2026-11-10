# Campaign

Campaign: PR-PLAY-57 — Integrated Authoritative Outcome Narration
Identifier: `pr_play_57`
Date: 2026-11-03
Generated: 2026-11-04T00:36:15.332359+00:00
Purpose: Evaluate completed-outcome narration inside quarantine.

# Executive Summary

# PR-PLAY-57 — B — PARTIAL / FURTHER INVESTIGATION REQUIRED

Eight real integrated candidates were generated across four existing investigation scenarios. Default gameplay remains deterministic. Provisional reading shows better action responsiveness and more coherent outcomes than the captured prelude-plus-anchor responses. The gates still reject legitimate paraphrases, so this is not ready for promotion.

- Provider: OpenAI; model(s): gpt-4.1-mini-2025-04-14. Successful calls: 8/8. Tokens: 3228 input + 478 output = 3706. Retries: 0.
- Provider latency: 1.892s average, 4.223s maximum. Exact per-call measurements are in performance_and_usage.json and raw_provider_responses.json.
- Combined gates: {'FAIL': 1, 'PASS': 4, 'REVIEW_REQUIRED': 3}. PR55 alone: {'FAIL': 1, 'PASS': 7}. Mandatory coverage: {'REVIEW_REQUIRED': 4, 'PASS': 4}.
- Provisional review: no identified new positive consequential fabrication or hidden disclosure. Omission/uncertainty concerns: []. Human/external review remains pending.
- State, quarantine and deterministic response checks pass on all eight. All raw state stops are preserved and explained; no gameplay assertions were relaxed.
- Regression: 557 passed / 3 known focused failures, no errors/skips; holdout wrapper passed; all nine known broader metadata failures reproduced. New module: 28/28.
- No commit or push. No ordinary player narration enabled. No ATGB benchmark score claimed.

Primary next cycle: improve integrated outcome coverage with a bounded, reviewed paraphrase mechanism. Preserve quarantine and demonstrate the same gameplay value; do not expand into general validator hardening.

## Changes made

New game/integrated_investigation_narration.py; small changes to game/quarantined_investigation_narration.py; new tests/test_pr_play_57_integrated_narration.py; extended architecture allowlist and persistence-import checks in tests/test_pr_play_49_anchored_narration.py. All other output is scoped evidence under artifacts/pr_play_57 and generated handoff exports.

## Human review and known limits

Review exact prose, especially “urgent update,” qualified negative search wording, and footprint uncertainty. Automated scores and this separate raw-text reading are provisional, not independent ground truth. Scenario B is a mundane no-clue examination, not a failed skill check. This four-scenario experiment does not establish general gameplay or validator completeness. Existing gold-gain wording is missed by PR55 but rejected by the preserved legacy mechanical check.

## Bundle contents

Seventeen reports, raw SDK captures, contracts, fact IDs, validation/coverage reasons, worksheets, individual quality scores, complete state comparisons, three durably accounted budget shards, regression logs, and incremental source diffs. No secrets or environment file is included.


Objective status: `B — PARTIAL / FURTHER INVESTIGATION REQUIRED`.

# Changes Made

## Production changes

- Opt-in integrated narration adapter and small quarantine transport extension. Default deterministic behavior preserved.

## Validation changes

- Narrow conservative mandatory-outcome check; PR55 unchanged. 28 integrated tests and updated quarantine architecture assertion.

## Tooling changes

- Three decreasing-budget durable accounting shards; state-stop diagnostics preserved.

## Documentation changes

- Seventeen requested campaign reports and provisional review worksheets.

## Generated artifacts

- Explicit evidence export with raw provider captures and source diffs.

# What Was Tested

- **Focused tests:** 557 passed, 3 known failures; final 28-case module counted once.
- **Broader relevant tests:** Nine known hard_validation_attempt_1 failures reproduced; holdout wrapper passed.
- **Full suite:** Not executed.
- **Runtime validation:** 8/8 successful real requests; all state/quarantine/fallback checks pass.
- **Model/runtime boundary:** Engine resolves first; prose never reaches ordinary player response or authoritative storage.
- **New regressions:** None after updating architecture assertion for the new quarantined module.
- **Pre-existing failures:** Same three focused and nine broader metadata failures.
- **Self-contained bundle review:** ZIP CRC, included-file SHA-256 and secret scan verified by package_review.py.

# Behavioral Evidence

## Evidence Packet: pr_play_57

Runs / turns: `8` / `10`
Runtime/model boundary: Real provider after authoritative resolution; prose quarantined.

### Representative success

Example: `A2`
Player classification: `representative_player_behavior`
Player: I examine the notice board.
GM: You study the notice board carefully and discover a new detail: the missing patrol was last seen taking the northwest mud track past the crates. This piece of information stands out amid the usual listings of taxes, curfew rules, and warnings, offering a fresh lead in the midst of the bustling gate area.
Automated result: `PASS`
Human review: `PENDING` - Provisional automated assessment only.
Source: `artifacts/pr_play_57/final_results.json`

### Representative failure

Example: `A1`
Player classification: `representative_player_behavior`
Player: I examine the notice board.
GM: You take a closer look at the notice board amid the bustling gate area. Among the posted taxes and curfew rules, you find a new, urgent update: the missing patrol was last seen heading northwest along the muddy track past the crates. This detail stands out against the usual announcements, offering a crucial lead in the ongoing search.
Automated result: `FAIL`
Human review: `PENDING` - Provisional automated assessment only.
Source: `artifacts/pr_play_57/final_results.json`

### Evaluator disagreement

Example: `D1`
Player classification: `representative_player_behavior`
Player: I examine the footprints.
GM: You crouch by the weathered milestone, carefully studying the mud churned with faint, overlapping footprints. Though you discern their presence clearly, the exact number of prints, their origin, and the direction they lead remain frustratingly unclear, fading into the scrub beyond the track.
Automated result: `REVIEW_REQUIRED`
Human review: `PENDING` - Provisional automated assessment only.
Source: `artifacts/pr_play_57/final_results.json`

### Ambiguous/unexpected

Example: `B2`
Player classification: `representative_player_behavior`
Player: I examine the rain barrel.
GM: You take a closer look at the rain barrel, noting its worn surface and the faint scent of damp wood mingling with the stew nearby. Despite your careful inspection, nothing new stands out—no hidden compartments or unusual markings catch your eye this time. The barrel remains just what it seems, an ordinary container amidst the bustling gate line.
Automated result: `PASS`
Human review: `PENDING` - Provisional automated assessment only.
Source: `artifacts/pr_play_57/final_results.json`

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

- `A1`: automated `FAIL`; human `PENDING`; player: I examine the notice board.; GM: You take a closer look at the notice board amid the bustling gate area. Among the posted taxes and curfew rules, you find a new, urgent update: the missing patrol was last seen heading northwest along the muddy track past the crates. This detail stands out against the usual announcements, offering a crucial lead in the ongoing search.
- `C2`: automated `REVIEW_REQUIRED`; human `PENDING`; player: I examine the notice board.; GM: You take a careful look at the notice board once more, but nothing new catches your eye beyond what you already know: the missing patrol was last spotted heading along the northwest mud track past the crates. The familiar postings about taxes, curfew, and the warning remain unchanged, offering no fresh clues.
- `D1`: automated `REVIEW_REQUIRED`; human `PENDING`; player: I examine the footprints.; GM: You crouch by the weathered milestone, carefully studying the mud churned with faint, overlapping footprints. Though you discern their presence clearly, the exact number of prints, their origin, and the direction they lead remain frustratingly unclear, fading into the scrub beyond the track.
- `D2`: automated `REVIEW_REQUIRED`; human `PENDING`; player: I examine the footprints.; GM: You carefully study the mud around the weathered milestone, noting faint overlapping footprints pressed into the earth. Though the prints are clear enough to see, their exact number, origin, and direction remain frustratingly indistinct, blending into the scrub and fading before you can trace them further along the track.

# Decisions Requiring Human Review

- Review the eight provisional semantic worksheets; no human confirmation claimed. No player-facing promotion authorized.

# Known Problems / Unresolved Findings

## Campaign-specific

- Four candidates conservatively flagged for coverage, including faithful cross-sentence/wording paraphrases. A1 also rejected by PR55.

## Pre-existing baseline

- Known gold-gain phrase missed by PR55 and rejected by the preserved legacy gate; three focused and nine broader test failures.

# Missing Concepts / Future Capabilities

- Deterministic failed skill-check fixture; consequences outside disclosure-only investigations.

# What This Campaign Does NOT Prove

- Human-confirmed quality, semantic completeness, broad gameplay, or safe player-facing narration.

# Recommended Next Step

Improve integrated outcome coverage using a bounded reviewed paraphrase set while preserving quarantine.

# Review Bundle Contents

Bundle file count: `101`
Bundle ZIP size: `000001613160` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_play_57/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_play_57/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_play_57/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/pr_play_57/evidence_summary.md`.
- `support/artifacts/pr_play_57/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/pr_play_57/evidence_manifest.json`.
- `support/artifacts/pr_play_57/02_BASELINE_AND_SCOPE.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/02_BASELINE_AND_SCOPE.md`.
- `support/artifacts/pr_play_57/03_INTEGRATED_NARRATION_ARCHITECTURE.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/03_INTEGRATED_NARRATION_ARCHITECTURE.md`.
- `support/artifacts/pr_play_57/04_STRUCTURED_OUTCOME_CONTRACT.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/04_STRUCTURED_OUTCOME_CONTRACT.md`.
- `support/artifacts/pr_play_57/05_SCENARIO_RESULTS.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/05_SCENARIO_RESULTS.md`.
- `support/artifacts/pr_play_57/06_RAW_INTEGRATED_NARRATION.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/06_RAW_INTEGRATED_NARRATION.md`.
- `support/artifacts/pr_play_57/07_BASELINE_COMPARISON.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/07_BASELINE_COMPARISON.md`.
- `support/artifacts/pr_play_57/08_VALIDATION_RESULTS.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/08_VALIDATION_RESULTS.md`.
- `support/artifacts/pr_play_57/09_MANDATORY_OUTCOME_COVERAGE.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/09_MANDATORY_OUTCOME_COVERAGE.md`.
- `support/artifacts/pr_play_57/10_INDEPENDENT_SEMANTIC_REVIEW.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/10_INDEPENDENT_SEMANTIC_REVIEW.md`.
- `support/artifacts/pr_play_57/11_NARRATION_QUALITY.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/11_NARRATION_QUALITY.md`.
- `support/artifacts/pr_play_57/12_STATE_AND_QUARANTINE_INTEGRITY.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/12_STATE_AND_QUARANTINE_INTEGRITY.md`.
- `support/artifacts/pr_play_57/13_FAILURE_HANDLING.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/13_FAILURE_HANDLING.md`.
- `support/artifacts/pr_play_57/14_PERFORMANCE_AND_USAGE.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/14_PERFORMANCE_AND_USAGE.md`.
- `support/artifacts/pr_play_57/15_REGRESSION_RESULTS.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/15_REGRESSION_RESULTS.md`.
- `support/artifacts/pr_play_57/16_LIMITATIONS_AND_OPEN_RISKS.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/16_LIMITATIONS_AND_OPEN_RISKS.md`.
- `support/artifacts/pr_play_57/17_NEXT_SESSION.md`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/17_NEXT_SESSION.md`.
- `support/artifacts/pr_play_57/authorized_outcome_contracts.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/authorized_outcome_contracts.json`.
- `support/artifacts/pr_play_57/baseline_comparison.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/baseline_comparison.json`.
- `support/artifacts/pr_play_57/broader_hard_validation.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/broader_hard_validation.txt`.
- `support/artifacts/pr_play_57/broader_hard_validation.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/broader_hard_validation.xml`.
- `support/artifacts/pr_play_57/broader_hard_validation_final.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/broader_hard_validation_final.txt`.
- `support/artifacts/pr_play_57/broader_hard_validation_final.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/broader_hard_validation_final.xml`.
- `support/artifacts/pr_play_57/campaign_hashes_before.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/campaign_hashes_before.json`.
- `support/artifacts/pr_play_57/closeout_metrics.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/closeout_metrics.json`.
- `support/artifacts/pr_play_57/closeout_metrics.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/closeout_metrics.txt`.
- `support/artifacts/pr_play_57/combined_results.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/combined_results.json`.
- `support/artifacts/pr_play_57/continuation_integrity.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/continuation_integrity.json`.
- `support/artifacts/pr_play_57/continue_experiment.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/continue_experiment.py`.
- `support/artifacts/pr_play_57/coverage_decisions.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/coverage_decisions.json`.
- `support/artifacts/pr_play_57/deterministic_baselines.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/deterministic_baselines.json`.
- `support/artifacts/pr_play_57/entry/commit.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/entry/commit.txt`.
- `support/artifacts/pr_play_57/entry/quarantined_investigation_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/entry/quarantined_investigation_narration.py`.
- `support/artifacts/pr_play_57/entry/status.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/entry/status.txt`.
- `support/artifacts/pr_play_57/entry/test_pr_play_49_anchored_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/entry/test_pr_play_49_anchored_narration.py`.
- `support/artifacts/pr_play_57/export_scan.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/export_scan.json`.
- `support/artifacts/pr_play_57/failure_handling.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/failure_handling.json`.
- `support/artifacts/pr_play_57/final_integrity.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/final_integrity.json`.
- `support/artifacts/pr_play_57/final_results.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/final_results.json`.
- `support/artifacts/pr_play_57/finish_experiment.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/finish_experiment.py`.
- `support/artifacts/pr_play_57/focused.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/focused.txt`.
- `support/artifacts/pr_play_57/focused.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/focused.xml`.
- `support/artifacts/pr_play_57/focused_final.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/focused_final.txt`.
- `support/artifacts/pr_play_57/focused_final.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/focused_final.xml`.
- `support/artifacts/pr_play_57/generation_parameters.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/generation_parameters.json`.
- `support/artifacts/pr_play_57/holdout.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/holdout.txt`.
- `support/artifacts/pr_play_57/holdout.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/holdout.xml`.
- `support/artifacts/pr_play_57/holdout_final.txt`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/holdout_final.txt`.
- `support/artifacts/pr_play_57/holdout_final.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/holdout_final.xml`.
- `support/artifacts/pr_play_57/hook_evidence/A1_t1-001.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/A1_t1-001.json`.
- `support/artifacts/pr_play_57/hook_evidence/A2_t1-001.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/A2_t1-001.json`.
- `support/artifacts/pr_play_57/hook_evidence/B1_t1-001.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/B1_t1-001.json`.
- `support/artifacts/pr_play_57/hook_evidence/B2_t1-002.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/B2_t1-002.json`.
- `support/artifacts/pr_play_57/hook_evidence/C1_t2-003.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/C1_t2-003.json`.
- `support/artifacts/pr_play_57/hook_evidence/C2_t2-004.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/C2_t2-004.json`.
- `support/artifacts/pr_play_57/hook_evidence/D1_t1-005.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/D1_t1-005.json`.
- `support/artifacts/pr_play_57/hook_evidence/D2_t1-006.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/hook_evidence/D2_t1-006.json`.
- `support/artifacts/pr_play_57/implementation.diff`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/implementation.diff`.
- `support/artifacts/pr_play_57/independent_review_worksheets.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/independent_review_worksheets.json`.
- `support/artifacts/pr_play_57/initial_stop_analysis.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/initial_stop_analysis.json`.
- `support/artifacts/pr_play_57/integrated_candidates.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/integrated_candidates.json`.
- `support/artifacts/pr_play_57/mandatory_fact_identifiers.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/mandatory_fact_identifiers.json`.
- `support/artifacts/pr_play_57/new_tests.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/new_tests.xml`.
- `support/artifacts/pr_play_57/new_tests_final.xml`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/new_tests_final.xml`.
- `support/artifacts/pr_play_57/package_review.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/package_review.py`.
- `support/artifacts/pr_play_57/performance_and_usage.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/performance_and_usage.json`.
- `support/artifacts/pr_play_57/preflight.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/preflight.json`.
- `support/artifacts/pr_play_57/prepare_review.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/prepare_review.py`.
- `support/artifacts/pr_play_57/provider_usage.jsonl`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/provider_usage.jsonl`.
- `support/artifacts/pr_play_57/provider_usage_final.jsonl`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/provider_usage_final.jsonl`.
- `support/artifacts/pr_play_57/provider_usage_remaining.jsonl`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/provider_usage_remaining.jsonl`.
- `support/artifacts/pr_play_57/provisional_assessments.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/provisional_assessments.json`.
- `support/artifacts/pr_play_57/quality_scores.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/quality_scores.json`.
- `support/artifacts/pr_play_57/raw_provider_responses.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/raw_provider_responses.json`.
- `support/artifacts/pr_play_57/regression_summary.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/regression_summary.json`.
- `support/artifacts/pr_play_57/regression_summary_final.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/regression_summary_final.json`.
- `support/artifacts/pr_play_57/run_experiment.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/run_experiment.py`.
- `support/artifacts/pr_play_57/run_regression.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/run_regression.py`.
- `support/artifacts/pr_play_57/run_regression_final.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/run_regression_final.py`.
- `support/artifacts/pr_play_57/scenario_manifest.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/scenario_manifest.json`.
- `support/artifacts/pr_play_57/scenario_results.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/scenario_results.json`.
- `support/artifacts/pr_play_57/second_stop_analysis.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/second_stop_analysis.json`.
- `support/artifacts/pr_play_57/state_and_quarantine_audit.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/state_and_quarantine_audit.json`.
- `support/artifacts/pr_play_57/state_integrity.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/state_integrity.json`.
- `support/artifacts/pr_play_57/test_summary.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/test_summary.json`.
- `support/artifacts/pr_play_57/validation_decisions.json`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `artifacts/pr_play_57/validation_decisions.json`.
- `support/game/anchored_investigation_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/anchored_investigation_narration.py`.
- `support/game/consequential_narration_validation.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/consequential_narration_validation.py`.
- `support/game/expressive_dialogue.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/expressive_dialogue.py`.
- `support/game/immutable_valid_response.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/immutable_valid_response.py`.
- `support/game/integrated_investigation_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/integrated_investigation_narration.py`.
- `support/game/offline_investigation_projection.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/offline_investigation_projection.py`.
- `support/game/provider_budget.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/provider_budget.py`.
- `support/game/quarantined_investigation_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `game/quarantined_investigation_narration.py`.
- `support/tests/test_pr_play_49_anchored_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `tests/test_pr_play_49_anchored_narration.py`.
- `support/tests/test_pr_play_57_integrated_narration.py`: Explicit PR-PLAY-57 implementation or execution evidence. Canonical source: `tests/test_pr_play_57_integrated_narration.py`.
- `support/artifacts/pr_play_57/review_config.json`: Reproduce the exact repository handoff selection. Canonical source: `artifacts/pr_play_57/review_config.json`.

## Explicit omissions

- `artifacts/pr_play_57/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_play_57/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_play_57/evidence_manifest.json`: duplicate content of artifacts/pr_play_57/evidence_manifest.json; canonical reference retained
- `artifacts/pr_play_57/evidence_summary.md`: duplicate content of artifacts/pr_play_57/evidence_summary.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
