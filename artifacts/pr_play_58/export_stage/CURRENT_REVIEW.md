# Campaign

Campaign: PR-PLAY-58 — Semantic Outcome Coverage
Identifier: `pr_play_58`
Date: 2026-11-03
Generated: 2026-11-04T00:55:47.709928+00:00
Purpose: Recognize authorized semantic paraphrases while preserving quarantine and combined authority gates.

# Executive Summary

# PR-PLAY-58 — C — FAIL / REMEDIATION REQUIRED

Bounded semantic coverage improves the eight original PR-PLAY-57 samples from 4/8 to 8/8 covered. Combined decisions improve from 4 PASS / 1 FAIL / 3 REVIEW_REQUIRED to 7 PASS / 1 FAIL. A1 remains rejected for the unsupported "new, urgent update" discovery. Exact UTF-8 provider text and authority are preserved; all archived previous combined decisions reproduce.

The single frozen holdout pass finds a critical false acceptance: H41 appends "The gate is now permanently open." to the authorized patrol fact and receives PASS. This is an unsupported persistent consequence. Implementation remains frozen after evaluation; no holdout tuning or rerun occurred. A safe player-facing experiment is not authorized.

Development: 43 cases; legitimate combined acceptance 14/15 (coverage 15/15); omissions blocked 6/6; contradictions blocked 11/11; expansions rejected 9/9; ambiguous review 2/2. Zero critical false acceptances; one legacy false rejection; 18 reviews.

Holdout: 50 cases; legitimate acceptance 14/15; omissions blocked 10/10; contradictions blocked 10/10; expansions rejected 9/10; ambiguous review 5/5. One critical false acceptance, one false rejection, 25 reviews, zero validation errors. Most contradictions are quarantined for review, not explicitly rejected; exact confusion matrices remain available. Same-session authored holdout is not independent blind validation.

Warmed coverage: 0.214 ms average / 0.713 ms maximum. Combined: 4.399 / 128.673 ms. 800 measurements per series during local regression activity. Zero provider requests / tokens.

Regression: 601 passed / 3 failed / 0 errors / 0 skipped of 604 focused cases. Final-source checks: 204 passed of 204. PR55 holdout wrapper and known broader results are recorded separately. No campaign state, deterministic response, quarantine gate, protected fixture, commit or push change.

Primary next step: repair the unsupported persistent-consequence detection gap exposed by H41 in a subsequent bounded validation cycle. Preserve this failed holdout and quarantine.


Objective status: `C — FAIL / REMEDIATION REQUIRED`.

# Changes Made

## Production changes

- No gameplay or publication change.

## Validation changes

- Bounded movement/uncertainty/status coverage leaf; narrow consequential assertion controls in existing PR55 owner.

## Tooling changes

- Frozen corpora, one-pass holdout runner, baseline replay, local measurements and integrity verification.

## Documentation changes

- 18 requested campaign reports.

## Generated artifacts

- Raw original samples, all layer audits and review export.

# What Was Tested

- **Focused tests:** 601 passed / 3 known failures of 604; final frozen-source lane 204/204 passed (overlaps focused lane).
- **Broader relevant tests:** PR55 holdout wrapper passed; nine known authority-assurance metadata failures reproduced.
- **Full suite:** Not executed.
- **Runtime validation:** Eight fixed local sample replays, 43 development controls and one frozen 50-case holdout pass.
- **Model/runtime boundary:** No provider requests; quarantine remains mandatory.
- **New regressions:** No unexplained new regression-test failure; H41 semantic false acceptance remains.
- **Pre-existing failures:** Three focused failures and nine hard_validation_attempt_1 failures.
- **Self-contained bundle review:** All 18 reports, fixed corpora/authority, result audits, incremental source diff and regression summaries present; ZIP CRC and included-file hashes verified.

# Behavioral Evidence

## Evidence Packet: pr_play_58

Runs / turns: `8` / `8`
Runtime/model boundary: Replay of preserved historical candidate text through local validation only.

### Representative success

Example: `D1`
Player classification: `runtime_discovered`
Player: I examine the footprints.
GM: You crouch by the weathered milestone, carefully studying the mud churned with faint, overlapping footprints. Though you discern their presence clearly, the exact number of prints, their origin, and the direction they lead remain frustratingly unclear, fading into the scrub beyond the track.
Automated result: `UNAVAILABLE`
Human review: `PENDING` - Same-agent provisional reading; external confirmation not claimed.
Source: `artifacts/pr_play_58/fixed_results.json`

### Representative failure

Example: `A1`
Player classification: `runtime_discovered`
Player: I examine the notice board.
GM: You take a closer look at the notice board amid the bustling gate area. Among the posted taxes and curfew rules, you find a new, urgent update: the missing patrol was last seen heading northwest along the muddy track past the crates. This detail stands out against the usual announcements, offering a crucial lead in the ongoing search.
Automated result: `UNAVAILABLE`
Human review: `PENDING` - Same-agent provisional reading; external confirmation not claimed.
Source: `artifacts/pr_play_58/fixed_results.json`

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review C verdict and preserved H41 failure; no action or player-facing enablement requested.

# Known Problems / Unresolved Findings

## Campaign-specific

- H41 unsupported permanent gate opening passes; H12 legitimate repeat is reviewed; D15 legacy rejection remains.

## Pre-existing baseline

- Three focused and nine broader known regression failures.

# Missing Concepts / Future Capabilities

- General assertion entailment, grammatical scope and robust temporal/coreference reasoning.

# What This Campaign Does NOT Prove

- Semantic completeness, independent blind holdout validation, live gameplay quality, ATGB score or safe player-facing narration.

# Recommended Next Step

Repair unsupported persistent-consequence detection exposed by H41 in a subsequent bounded validation cycle; preserve quarantine.

# Review Bundle Contents

Bundle file count: `74`
Bundle ZIP size: `000000271538` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_play_58/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_play_58/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_play_58/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/pr_play_58/evidence_summary.md`.
- `support/artifacts/pr_play_58/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/pr_play_58/evidence_manifest.json`.
- `support/artifacts/pr_play_58/02_BASELINE_AND_SCOPE.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/02_BASELINE_AND_SCOPE.md`.
- `support/artifacts/pr_play_58/03_PR_PLAY_57_FAILURE_ANALYSIS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/03_PR_PLAY_57_FAILURE_ANALYSIS.md`.
- `support/artifacts/pr_play_58/04_SEMANTIC_COVERAGE_CONTRACT.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/04_SEMANTIC_COVERAGE_CONTRACT.md`.
- `support/artifacts/pr_play_58/05_IMPLEMENTATION_CHANGES.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/05_IMPLEMENTATION_CHANGES.md`.
- `support/artifacts/pr_play_58/06_PARAPHRASE_RECOGNITION_RESULTS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/06_PARAPHRASE_RECOGNITION_RESULTS.md`.
- `support/artifacts/pr_play_58/07_UNCERTAINTY_PRESERVATION.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/07_UNCERTAINTY_PRESERVATION.md`.
- `support/artifacts/pr_play_58/08_REPEATED_INVESTIGATION.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/08_REPEATED_INVESTIGATION.md`.
- `support/artifacts/pr_play_58/09_NEGATIVE_CONTROL_RESULTS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/09_NEGATIVE_CONTROL_RESULTS.md`.
- `support/artifacts/pr_play_58/10_POSITIVE_CONTROL_RESULTS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/10_POSITIVE_CONTROL_RESULTS.md`.
- `support/artifacts/pr_play_58/11_FIXED_SAMPLE_REEVALUATION.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/11_FIXED_SAMPLE_REEVALUATION.md`.
- `support/artifacts/pr_play_58/12_HOLDOUT_RESULTS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/12_HOLDOUT_RESULTS.md`.
- `support/artifacts/pr_play_58/13_COMBINED_VALIDATION_INTEGRITY.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/13_COMBINED_VALIDATION_INTEGRITY.md`.
- `support/artifacts/pr_play_58/14_PERFORMANCE_AND_USAGE.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/14_PERFORMANCE_AND_USAGE.md`.
- `support/artifacts/pr_play_58/15_STATE_AND_QUARANTINE_INTEGRITY.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/15_STATE_AND_QUARANTINE_INTEGRITY.md`.
- `support/artifacts/pr_play_58/16_REGRESSION_RESULTS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/16_REGRESSION_RESULTS.md`.
- `support/artifacts/pr_play_58/17_LIMITATIONS_AND_OPEN_RISKS.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/17_LIMITATIONS_AND_OPEN_RISKS.md`.
- `support/artifacts/pr_play_58/18_NEXT_SESSION.md`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/18_NEXT_SESSION.md`.
- `support/artifacts/pr_play_58/broader_hard_validation_final.txt`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/broader_hard_validation_final.txt`.
- `support/artifacts/pr_play_58/broader_hard_validation_final.xml`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/broader_hard_validation_final.xml`.
- `support/artifacts/pr_play_58/consequential_before.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/consequential_before.py`.
- `support/artifacts/pr_play_58/development_corpus.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/development_corpus.json`.
- `support/artifacts/pr_play_58/development_error_examples.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/development_error_examples.json`.
- `support/artifacts/pr_play_58/development_initial.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/development_initial.json`.
- `support/artifacts/pr_play_58/development_results.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/development_results.json`.
- `support/artifacts/pr_play_58/development_tests.xml`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/development_tests.xml`.
- `support/artifacts/pr_play_58/entry_hashes.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/entry_hashes.json`.
- `support/artifacts/pr_play_58/entry_status.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/entry_status.json`.
- `support/artifacts/pr_play_58/evaluate.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/evaluate.py`.
- `support/artifacts/pr_play_58/export_scan.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/export_scan.json`.
- `support/artifacts/pr_play_58/final_frozen_source_final.txt`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/final_frozen_source_final.txt`.
- `support/artifacts/pr_play_58/final_frozen_source_final.xml`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/final_frozen_source_final.xml`.
- `support/artifacts/pr_play_58/final_source_tests.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/final_source_tests.json`.
- `support/artifacts/pr_play_58/fixed_results.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/fixed_results.json`.
- `support/artifacts/pr_play_58/fixed_results_invalid_windows_decoding.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/fixed_results_invalid_windows_decoding.json`.
- `support/artifacts/pr_play_58/fixed_samples.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/fixed_samples.json`.
- `support/artifacts/pr_play_58/focused_final.txt`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/focused_final.txt`.
- `support/artifacts/pr_play_58/focused_final.xml`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/focused_final.xml`.
- `support/artifacts/pr_play_58/holdout.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout.json`.
- `support/artifacts/pr_play_58/holdout_error_examples.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout_error_examples.json`.
- `support/artifacts/pr_play_58/holdout_final.txt`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout_final.txt`.
- `support/artifacts/pr_play_58/holdout_final.xml`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout_final.xml`.
- `support/artifacts/pr_play_58/holdout_manifest.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout_manifest.json`.
- `support/artifacts/pr_play_58/holdout_results.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout_results.json`.
- `support/artifacts/pr_play_58/holdout_started.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/holdout_started.json`.
- `support/artifacts/pr_play_58/implementation.diff`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/implementation.diff`.
- `support/artifacts/pr_play_58/implementation_frozen.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/implementation_frozen.json`.
- `support/artifacts/pr_play_58/integrated_before.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/integrated_before.py`.
- `support/artifacts/pr_play_58/integrity.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/integrity.json`.
- `support/artifacts/pr_play_58/measure.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/measure.py`.
- `support/artifacts/pr_play_58/metrics.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/metrics.json`.
- `support/artifacts/pr_play_58/package_review.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/package_review.py`.
- `support/artifacts/pr_play_58/performance.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/performance.json`.
- `support/artifacts/pr_play_58/prepare.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/prepare.py`.
- `support/artifacts/pr_play_58/previous_coverage.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/previous_coverage.py`.
- `support/artifacts/pr_play_58/previous_decisions_original.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/previous_decisions_original.json`.
- `support/artifacts/pr_play_58/raw_provider_responses_original.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/raw_provider_responses_original.json`.
- `support/artifacts/pr_play_58/raw_text_integrity.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/raw_text_integrity.json`.
- `support/artifacts/pr_play_58/regression_summary_final.json`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/regression_summary_final.json`.
- `support/artifacts/pr_play_58/report.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/report.py`.
- `support/artifacts/pr_play_58/run_regression.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `artifacts/pr_play_58/run_regression.py`.
- `support/game/anchored_investigation_narration.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `game/anchored_investigation_narration.py`.
- `support/game/consequential_narration_validation.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `game/consequential_narration_validation.py`.
- `support/game/integrated_investigation_narration.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `game/integrated_investigation_narration.py`.
- `support/game/mandatory_outcome_coverage.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `game/mandatory_outcome_coverage.py`.
- `support/game/offline_investigation_projection.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `game/offline_investigation_projection.py`.
- `support/game/quarantined_investigation_narration.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `game/quarantined_investigation_narration.py`.
- `support/tests/pr_play_58_development.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `tests/pr_play_58_development.py`.
- `support/tests/test_pr_play_57_integrated_narration.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `tests/test_pr_play_57_integrated_narration.py`.
- `support/tests/test_pr_play_58_semantic_coverage.py`: Explicit PR58 change, original evidence or validation result. Canonical source: `tests/test_pr_play_58_semantic_coverage.py`.

## Explicit omissions

- `artifacts/pr_play_58/01_EXECUTIVE_SUMMARY.md`: duplicate content of artifacts/pr_play_58/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `artifacts/pr_play_58/evidence_manifest.json`: duplicate content of artifacts/pr_play_58/evidence_manifest.json; canonical reference retained
- `artifacts/pr_play_58/evidence_summary.md`: duplicate content of artifacts/pr_play_58/evidence_summary.md; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
