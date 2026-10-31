# Campaign

Campaign: PR-PLAY-04 Opening Failure Acceptance and Commit Integrity
Identifier: `pr_play_04_opening_failure_acceptance`
Date: 2026-10-26
Generated: 2026-10-26T21:15:00-04:00
Purpose: A campaign opening either completes from an accepted scene_opening or fails explicitly without gameplay progression.

# Executive Summary

Failure class: implementation. A rejected scene_opening was sealed as safe_nonresolution and committed as a successful opening, and opening progression was saved before acceptance. The repair keeps that generic fallback from completing scene_opening and restores turn, time pressure, and faction state unless a valid opening is accepted. Pre-change stubs reproduced both defects. Post-change stubs and 18 integration tests pass. Structured validation, prompts, schemas, models, token limits, and PR-PLAY-02 admission controls were not weakened. Two legacy HTTP tests that treated '[Narration]' as a completed opening now receive HTTP 422. Three rich-opening length assertions still fail at gate length 781 and were not bisected. The accounting fingerprint test remains red on the preexisting dirty tree. No live provider call. Verdict B. Live playtesting may not resume.

Objective status: `B — CONDITIONAL ACCEPTANCE; HOST REPAIR DEMONSTRATED; LIVE GENERATION UNPROVEN`.

# Changes Made

## Production changes

- game/api.py only: opening completion rejects generic and unstructured openings; opening progression is staged and restored unless completion succeeds.

## Validation changes

- tests/test_pr_play_04_opening_integrity.py. Contract-valid stubs in tests/test_start_campaign_api.py and tests/test_opening_start_seam_regressions.py. '[Narration]' was not accepted to preserve old HTTP 200 expectations.

## Tooling changes

- Offline reproduction script artifacts/pr_play_04/pre_change_reproduce.py. No production tool or provider client change.

## Documentation changes

- Eight reports under development/campaigns/product_realization/pr_play_04/. docs/NEXT_SESSION.md oriented to this conditional verdict.

## Generated artifacts

- Pre-change and post-change stub captures, scoped source diff, HTTP regression output, repository status, and this review bundle.

# What Was Tested

- **Focused tests:** 18 passed, 0 failed, exit 0: tests/test_pr_play_04_opening_integrity.py.
- **Broader relevant tests:** Non-HTTP slice 95 passed / 1 failed (preexisting accounting fingerprint). HTTP start/seam/scene slice finished inside 50s: 18 passed / 5 failed.
- **Full suite:** Not run. No full-suite-green claim.
- **Runtime validation:** Deterministic SDK stubs only. Standalone pre-change and post-change captures in artifacts/pr_play_04/. One successful stubbed opening measured 1.60s wall clock including process start. No token or provider-latency claim.
- **Model/runtime boundary:** No live provider calls and no connectivity diagnostics. Pytest live-model guard remained installed; tests restored production call_gpt and stubbed OpenAI.
- **New regressions:** Two journal-seed HTTP tests now return 422 because '[Narration]' is not a valid scene_opening. Three rich-text HTTP length assertions remain 200 with gate length 781; classified indeterminate and not bisected.
- **Pre-existing failures:** test_readiness_acceptance_is_not_live_execution fails on reviewed source fingerprints for provider_budget.py and six already-guarded dispatch owners. Manifest not updated.
- **Self-contained bundle review:** Bundle includes the eight reports, scoped diff, modified source, new and updated tests, pre-change and post-change captures, HTTP regression output, and repository status. No secrets.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept or redirect the conditional host repair before any live playtest.
- Do not authorize a manual Start Campaign from this package alone.

# Known Problems / Unresolved Findings

## Campaign-specific

- Live missing_structured_envelope cause remains unknown because the raw provider body was not retained.
- World save is not crash-atomic. Caught failures restore the baseline; a kill during the success write can still tear world.json.
- The opening attempt holds the existing persistence lock across the provider call.

## Pre-existing baseline

- Dirty worktree and ATGB accounting fingerprint drift predate a clean attestation of current sources.
- Rich opening emission length 781 versus the >800 assertion was not introduced by the completion guard and was not bisected.
- PR-EG experimental integration remains out of scope.

# Missing Concepts / Future Capabilities

- No new transaction framework, narrative contract, or provider retry. Crash-atomic multi-file persistence was not added.

# What This Campaign Does NOT Prove

- That the live model will emit a valid scene_opening.
- Full-suite green, gameplay-benchmark improvement, token savings, or provider-latency improvement.
- Crash atomicity of world.json.

# Recommended Next Step

Stop for external review of this ZIP. Do not start a live playtest and do not implement a follow-on repair until that review accepts or redirects the conditional items.

# Review Bundle Contents

Bundle file count: `25`
Bundle ZIP size: `000000139024` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_04/08_final_verdict_and_handoff.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_04/08_final_verdict_and_handoff.md`.
- `support/development/campaigns/product_realization/pr_play_04/01_baseline_and_failure_reproduction.md`: Baseline and pre-change reproduction. Canonical source: `development/campaigns/product_realization/pr_play_04/01_baseline_and_failure_reproduction.md`.
- `support/development/campaigns/product_realization/pr_play_04/02_opening_acceptance_repair.md`: Acceptance repair. Canonical source: `development/campaigns/product_realization/pr_play_04/02_opening_acceptance_repair.md`.
- `support/development/campaigns/product_realization/pr_play_04/03_commit_integrity_repair.md`: Commit integrity repair. Canonical source: `development/campaigns/product_realization/pr_play_04/03_commit_integrity_repair.md`.
- `support/development/campaigns/product_realization/pr_play_04/04_deterministic_integration_matrix.md`: Deterministic integration matrix. Canonical source: `development/campaigns/product_realization/pr_play_04/04_deterministic_integration_matrix.md`.
- `support/development/campaigns/product_realization/pr_play_04/05_authority_and_provider_budget.md`: Authority and provider budget. Canonical source: `development/campaigns/product_realization/pr_play_04/05_authority_and_provider_budget.md`.
- `support/development/campaigns/product_realization/pr_play_04/06_regression_and_performance.md`: Regression and performance. Canonical source: `development/campaigns/product_realization/pr_play_04/06_regression_and_performance.md`.
- `support/development/campaigns/product_realization/pr_play_04/07_live_play_readiness.md`: Live-play readiness. Canonical source: `development/campaigns/product_realization/pr_play_04/07_live_play_readiness.md`.
- `support/game/api.py`: Opening acceptance and commit boundary. Canonical source: `game/api.py`.
- `support/tests/test_pr_play_04_opening_integrity.py`: Deterministic opening matrix. Canonical source: `tests/test_pr_play_04_opening_integrity.py`.
- `support/tests/test_start_campaign_api.py`: Contract-valid opening stub for success paths. Canonical source: `tests/test_start_campaign_api.py`.
- `support/tests/test_opening_start_seam_regressions.py`: Contract-valid opening stub for seam paths. Canonical source: `tests/test_opening_start_seam_regressions.py`.
- `support/artifacts/pr_play_04/source.diff`: Scoped diff of tracked edits. Canonical source: `artifacts/pr_play_04/source.diff`.
- `support/artifacts/pr_play_04/pre_change/summary.json`: Pre-change reproduction summary. Canonical source: `artifacts/pr_play_04/pre_change/summary.json`.
- `support/artifacts/pr_play_04/post_change/summary.json`: Post-change reproduction summary. Canonical source: `artifacts/pr_play_04/post_change/summary.json`.
- `support/artifacts/pr_play_04/pre_change/missing_envelope.json`: Pre-change missing-envelope state. Canonical source: `artifacts/pr_play_04/pre_change/missing_envelope.json`.
- `support/artifacts/pr_play_04/post_change/missing_envelope.json`: Post-change missing-envelope state. Canonical source: `artifacts/pr_play_04/post_change/missing_envelope.json`.
- `support/artifacts/pr_play_04/pre_change/pipeline_exception.json`: Pre-change partial progression. Canonical source: `artifacts/pr_play_04/pre_change/pipeline_exception.json`.
- `support/artifacts/pr_play_04/post_change/pipeline_exception.json`: Post-change restored progression. Canonical source: `artifacts/pr_play_04/post_change/pipeline_exception.json`.
- `support/artifacts/pr_play_04/pre_change/valid_structured.json`: Pre-change valid opening. Canonical source: `artifacts/pr_play_04/pre_change/valid_structured.json`.
- `support/artifacts/pr_play_04/regression_http_out.txt`: HTTP start and seam results. Canonical source: `artifacts/pr_play_04/regression_http_out.txt`.
- `support/artifacts/pr_play_04/repository_status.txt`: HEAD and scope note. Canonical source: `artifacts/pr_play_04/repository_status.txt`.
- `support/docs/NEXT_SESSION.md`: Next session must not resume live play. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

- `artifacts/pr_play_04/post_change/valid_structured.json`: duplicate content of artifacts/pr_play_04/pre_change/valid_structured.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
