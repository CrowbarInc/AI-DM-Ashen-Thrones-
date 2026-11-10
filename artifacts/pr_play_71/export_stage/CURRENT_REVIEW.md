# Campaign

Campaign: Normal Campaign Lifecycle and Branch Continuity
Identifier: `PR-PLAY-71`
Date: 2026-11-05
Generated: 2026-11-06T01:15:48.802347+00:00
Purpose: Review normal UI creation, start, branch choice, save/resume and continuity, including preserved failures.

# Executive Summary

Both normal browser lifecycles demonstrated; one frozen holdout 46/50 precedes targeted persistence/import repairs. Final-source holdout/browser coverage incomplete. No commit/push.

Objective status: `B — PARTIAL / BOTH NORMAL PLAYER LIFECYCLES DEMONSTRATED; FINAL HOLDOUT COVERAGE INCOMPLETE`.

# Changes Made

## Production changes

- Explicit default-off new-campaign enrollment; trusted prerequisite disclosure; full transcript resume; bounded start deadline/busy guards.
- Bounded same-file Windows rename retry and failed-New-Campaign rollback; existing adapter dependency retained.

## Validation changes

- 50-case frozen developer holdout once: 46 passed, four failures retained.
- Final focused recovery/publication/branch and boundary checks; separate baseline comparison for newly measured startup failures.

## Tooling changes

- Isolated normal browser/TCP host, full transport/authority capture and selected sanitized review export.

## Documentation changes

- 23 cycle reports and NEXT_SESSION orientation.

## Generated artifacts

- Original failure traces, screenshots, frozen manifest/source and final repair results.

# What Was Tested

- **Focused tests:** {'passed': 102, 'failed': [], 'total': 102}
- **Broader relevant tests:** Nine historical authority failures; exact XML/log included.
- **Full suite:** Not run; no official ATGB or external independence.
- **Runtime validation:** Both normal UI branches plus separate TCP replay; final persistence repair has final TCP but no live-browser rerun.
- **Model/runtime boundary:** 15 live requests, 189036 tokens including preflight/required gameplay; no shadow study.
- **New regressions:** PR49 direct-import regression fixed and retested; temporary test directory collisions retained then rerun with isolated basetemp.
- **Pre-existing failures:** Three historical focused, nine broader, plus six newly measured startup failures verified against exact entry API.
- **Self-contained bundle review:** 23 requested reports, exact player-facing responses, original failure traces, final repair checks, explicit baseline and scope limits.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No approval requested; no commit/push.

# Known Problems / Unresolved Findings

## Campaign-specific

- Frozen holdout precedes final recovery changes; raw score 46/50.
- Cached frontend initially kept the previous transcript; reopened context verified current frontend.
- Complete per-operation browser startup/substage timings unavailable.

## Pre-existing baseline

- Six startup failures reproduced on entry API.
- Permanent filesystem outages can still prevent rollback.

# Missing Concepts / Future Capabilities

- Final-source fresh holdout and live-browser coverage for final persistence repair.

# What This Campaign Does NOT Prove

- Full suite, official ATGB, external independent validation, process-crash durability, multiplayer authorization or broad open-world initiative.

# Recommended Next Step

PR-PLAY-71 verification closure: use a fresh, correctly specified holdout against the final persistence repair, including transient and permanent Windows rename failures. Preserve this frozen run without rerunning or tuning it.

# Review Bundle Contents

Bundle file count: `162`
Bundle ZIP size: `000008164643` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_71/01_EXECUTIVE_SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_71/01_EXECUTIVE_SUMMARY.md`.
- `support/artifacts/pr_play_71/A_choices.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_choices.png`.
- `support/artifacts/pr_play_71/A_choices.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_choices.txt`.
- `support/artifacts/pr_play_71/A_consequence.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_consequence.png`.
- `support/artifacts/pr_play_71/A_final.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_final.png`.
- `support/artifacts/pr_play_71/A_final.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_final.txt`.
- `support/artifacts/pr_play_71/A_followup.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_followup.png`.
- `support/artifacts/pr_play_71/A_opening.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_opening.png`.
- `support/artifacts/pr_play_71/A_post_resume.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_post_resume.png`.
- `support/artifacts/pr_play_71/A_post_resume.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_post_resume.txt`.
- `support/artifacts/pr_play_71/A_post_resume_submission.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_post_resume_submission.txt`.
- `support/artifacts/pr_play_71/A_reload.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_reload.png`.
- `support/artifacts/pr_play_71/A_reopened.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_reopened.png`.
- `support/artifacts/pr_play_71/A_reopened.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_reopened.txt`.
- `support/artifacts/pr_play_71/A_repaired_choices.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_repaired_choices.png`.
- `support/artifacts/pr_play_71/A_resume_wide.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_resume_wide.png`.
- `support/artifacts/pr_play_71/A_resumed.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_resumed.txt`.
- `support/artifacts/pr_play_71/A_save.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_save.png`.
- `support/artifacts/pr_play_71/A_saved.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/A_saved.txt`.
- `support/artifacts/pr_play_71/analyze.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/analyze.py`.
- `support/artifacts/pr_play_71/B_choices.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_choices.png`.
- `support/artifacts/pr_play_71/B_consequence.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_consequence.png`.
- `support/artifacts/pr_play_71/B_final.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_final.png`.
- `support/artifacts/pr_play_71/B_final.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_final.txt`.
- `support/artifacts/pr_play_71/B_followup.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_followup.png`.
- `support/artifacts/pr_play_71/B_opening.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_opening.png`.
- `support/artifacts/pr_play_71/B_post_resume.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_post_resume.txt`.
- `support/artifacts/pr_play_71/B_post_resume_wide.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_post_resume_wide.png`.
- `support/artifacts/pr_play_71/B_reload.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_reload.png`.
- `support/artifacts/pr_play_71/B_reload.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_reload.txt`.
- `support/artifacts/pr_play_71/B_resume.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_resume.png`.
- `support/artifacts/pr_play_71/B_resumed.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_resumed.txt`.
- `support/artifacts/pr_play_71/B_save.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_save.png`.
- `support/artifacts/pr_play_71/B_saved.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/B_saved.txt`.
- `support/artifacts/pr_play_71/baseline.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/baseline.py`.
- `support/artifacts/pr_play_71/baseline_opening.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/baseline_opening.png`.
- `support/artifacts/pr_play_71/baseline_route.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/baseline_route.txt`.
- `support/artifacts/pr_play_71/baseline_start_regression.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/baseline_start_regression.py`.
- `support/artifacts/pr_play_71/baseline_start_regression.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/baseline_start_regression.txt`.
- `support/artifacts/pr_play_71/baseline_start_regression.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/baseline_start_regression.xml`.
- `support/artifacts/pr_play_71/boundary_final.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/boundary_final.txt`.
- `support/artifacts/pr_play_71/boundary_final.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/boundary_final.xml`.
- `support/artifacts/pr_play_71/broader_final.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/broader_final.txt`.
- `support/artifacts/pr_play_71/broader_final.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/broader_final.xml`.
- `support/artifacts/pr_play_71/cached_frontend_resume_mismatch.png`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/cached_frontend_resume_mismatch.png`.
- `support/artifacts/pr_play_71/cached_frontend_resume_mismatch.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/cached_frontend_resume_mismatch.txt`.
- `support/artifacts/pr_play_71/cases.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/cases.py`.
- `support/artifacts/pr_play_71/development_disclosure.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/development_disclosure.txt`.
- `support/artifacts/pr_play_71/development_initial.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/development_initial.txt`.
- `support/artifacts/pr_play_71/development_second.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/development_second.txt`.
- `support/artifacts/pr_play_71/diagnose_openings.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/diagnose_openings.py`.
- `support/artifacts/pr_play_71/entry_api.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/entry_api.py`.
- `support/artifacts/pr_play_71/entry_sources.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/entry_sources.py`.
- `support/artifacts/pr_play_71/final_boundary.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/final_boundary.txt`.
- `support/artifacts/pr_play_71/final_boundary.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/final_boundary.xml`.
- `support/artifacts/pr_play_71/final_boundary_collided.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/final_boundary_collided.txt`.
- `support/artifacts/pr_play_71/final_boundary_collided.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/final_boundary_collided.xml`.
- `support/artifacts/pr_play_71/final_optional_gate.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/final_optional_gate.txt`.
- `support/artifacts/pr_play_71/final_optional_gate.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/final_optional_gate.xml`.
- `support/artifacts/pr_play_71/finalize.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/finalize.py`.
- `support/artifacts/pr_play_71/focused_final.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/focused_final.txt`.
- `support/artifacts/pr_play_71/focused_final.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/focused_final.xml`.
- `support/artifacts/pr_play_71/freeze_holdout.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/freeze_holdout.py`.
- `support/artifacts/pr_play_71/frozen_source/artifacts/pr_play_71/holdout.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/frozen_source/artifacts/pr_play_71/holdout.py`.
- `support/artifacts/pr_play_71/frozen_source/game/api.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/frozen_source/game/api.py`.
- `support/artifacts/pr_play_71/frozen_source/game/authored_consequences.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/frozen_source/game/authored_consequences.py`.
- `support/artifacts/pr_play_71/frozen_source/game/campaign_reset.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/frozen_source/game/campaign_reset.py`.
- `support/artifacts/pr_play_71/frozen_source/static/app.js`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/frozen_source/static/app.js`.
- `support/artifacts/pr_play_71/frozen_source/tests/test_pr_play_71_lifecycle.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/frozen_source/tests/test_pr_play_71_lifecycle.py`.
- `support/artifacts/pr_play_71/holdout_run.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/holdout_run.txt`.
- `support/artifacts/pr_play_71/host.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/host.py`.
- `support/artifacts/pr_play_71/host_after_log.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/host_after_log.txt`.
- `support/artifacts/pr_play_71/host_enabled_log.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/host_enabled_log.txt`.
- `support/artifacts/pr_play_71/host_log.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/host_log.txt`.
- `support/artifacts/pr_play_71/host_repaired_log.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/host_repaired_log.txt`.
- `support/artifacts/pr_play_71/http_final_run.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/http_final_run.txt`.
- `support/artifacts/pr_play_71/http_lifecycle.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/http_lifecycle.py`.
- `support/artifacts/pr_play_71/http_run.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/http_run.txt`.
- `support/artifacts/pr_play_71/implementation.diff`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/implementation.diff`.
- `support/artifacts/pr_play_71/opening_diagnostics_run.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/opening_diagnostics_run.txt`.
- `support/artifacts/pr_play_71/optional_preservation.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/optional_preservation.txt`.
- `support/artifacts/pr_play_71/optional_preservation.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/optional_preservation.xml`.
- `support/artifacts/pr_play_71/package_review.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/package_review.py`.
- `support/artifacts/pr_play_71/package_run.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/package_run.txt`.
- `support/artifacts/pr_play_71/persistence_recovery_final.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/persistence_recovery_final.xml`.
- `support/artifacts/pr_play_71/post_holdout_repair.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/post_holdout_repair.txt`.
- `support/artifacts/pr_play_71/post_holdout_repair.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/post_holdout_repair.xml`.
- `support/artifacts/pr_play_71/post_holdout_repair_collided.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/post_holdout_repair_collided.txt`.
- `support/artifacts/pr_play_71/post_holdout_repair_collided.xml`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/post_holdout_repair_collided.xml`.
- `support/artifacts/pr_play_71/publication_reproduction.txt`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/publication_reproduction.txt`.
- `support/artifacts/pr_play_71/regression.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/regression.py`.
- `support/artifacts/pr_play_71/report.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/report.py`.
- `support/artifacts/pr_play_71/review_data/baseline.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/baseline.json`.
- `support/artifacts/pr_play_71/review_data/browser_console.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/browser_console.json`.
- `support/artifacts/pr_play_71/review_data/browser_measurements.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/browser_measurements.json`.
- `support/artifacts/pr_play_71/review_data/browser_network.jsonl`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/browser_network.jsonl`.
- `support/artifacts/pr_play_71/review_data/browser_observations.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/browser_observations.json`.
- `support/artifacts/pr_play_71/review_data/browser_results.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/browser_results.json`.
- `support/artifacts/pr_play_71/review_data/complete_payload_scan.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/complete_payload_scan.json`.
- `support/artifacts/pr_play_71/review_data/entry_source_provenance.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/entry_source_provenance.json`.
- `support/artifacts/pr_play_71/review_data/final_implementation_freeze.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/final_implementation_freeze.json`.
- `support/artifacts/pr_play_71/review_data/final_repository_status.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/final_repository_status.json`.
- `support/artifacts/pr_play_71/review_data/final_validation.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/final_validation.json`.
- `support/artifacts/pr_play_71/review_data/freeze_integrity.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/freeze_integrity.json`.
- `support/artifacts/pr_play_71/review_data/frozen_holdout.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/frozen_holdout.json`.
- `support/artifacts/pr_play_71/review_data/frozen_holdout_manifest.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/frozen_holdout_manifest.json`.
- `support/artifacts/pr_play_71/review_data/holdout_results.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/holdout_results.json`.
- `support/artifacts/pr_play_71/review_data/holdout_started.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/holdout_started.json`.
- `support/artifacts/pr_play_71/review_data/holdout_summary.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/holdout_summary.json`.
- `support/artifacts/pr_play_71/review_data/http_summary.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/http_summary.json`.
- `support/artifacts/pr_play_71/review_data/http_summary_pre_recovery.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/http_summary_pre_recovery.json`.
- `support/artifacts/pr_play_71/review_data/http_traces.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/http_traces.json`.
- `support/artifacts/pr_play_71/review_data/http_traces_pre_recovery.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/http_traces_pre_recovery.json`.
- `support/artifacts/pr_play_71/review_data/implementation_freeze.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/implementation_freeze.json`.
- `support/artifacts/pr_play_71/review_data/inherited_protected_integrity.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/inherited_protected_integrity.json`.
- `support/artifacts/pr_play_71/review_data/latency.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/latency.json`.
- `support/artifacts/pr_play_71/review_data/metrics.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/metrics.json`.
- `support/artifacts/pr_play_71/review_data/opening_diagnostics.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/opening_diagnostics.json`.
- `support/artifacts/pr_play_71/review_data/protected_integrity.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/protected_integrity.json`.
- `support/artifacts/pr_play_71/review_data/provenance.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/provenance.json`.
- `support/artifacts/pr_play_71/review_data/provider_usage.jsonl`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/provider_usage.jsonl`.
- `support/artifacts/pr_play_71/review_data/provider_usage_22944.jsonl`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/provider_usage_22944.jsonl`.
- `support/artifacts/pr_play_71/review_data/provider_usage_28560.jsonl`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/provider_usage_28560.jsonl`.
- `support/artifacts/pr_play_71/review_data/provider_usage_32308.jsonl`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/provider_usage_32308.jsonl`.
- `support/artifacts/pr_play_71/review_data/provider_usage_summary.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/provider_usage_summary.json`.
- `support/artifacts/pr_play_71/review_data/publication_500_diagnostics.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/publication_500_diagnostics.json`.
- `support/artifacts/pr_play_71/review_data/regression_comparison.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/regression_comparison.json`.
- `support/artifacts/pr_play_71/review_data/regression_summary.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/regression_summary.json`.
- `support/artifacts/pr_play_71/review_data/state_integrity.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/state_integrity.json`.
- `support/artifacts/pr_play_71/review_data/verdict.json`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/review_data/verdict.json`.
- `support/artifacts/pr_play_71/working_tree.diff`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `artifacts/pr_play_71/working_tree.diff`.
- `support/development/campaigns/product_realization/pr_play_71/02_BASELINE_AND_SCOPE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/02_BASELINE_AND_SCOPE.md`.
- `support/development/campaigns/product_realization/pr_play_71/03_LIFECYCLE_ARCHITECTURE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/03_LIFECYCLE_ARCHITECTURE.md`.
- `support/development/campaigns/product_realization/pr_play_71/04_NEW_CAMPAIGN_BASELINE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/04_NEW_CAMPAIGN_BASELINE.md`.
- `support/development/campaigns/product_realization/pr_play_71/05_START_CAMPAIGN_RELIABILITY.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/05_START_CAMPAIGN_RELIABILITY.md`.
- `support/development/campaigns/product_realization/pr_play_71/06_INITIALIZATION_CONTRACT.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/06_INITIALIZATION_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_71/07_BRANCH_A_LIFECYCLE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/07_BRANCH_A_LIFECYCLE.md`.
- `support/development/campaigns/product_realization/pr_play_71/08_BRANCH_B_LIFECYCLE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/08_BRANCH_B_LIFECYCLE.md`.
- `support/development/campaigns/product_realization/pr_play_71/09_SAVE_RESUME.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/09_SAVE_RESUME.md`.
- `support/development/campaigns/product_realization/pr_play_71/10_CROSS_CAMPAIGN_ISOLATION.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/10_CROSS_CAMPAIGN_ISOLATION.md`.
- `support/development/campaigns/product_realization/pr_play_71/11_PUBLICATION_HTTP_500.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/11_PUBLICATION_HTTP_500.md`.
- `support/development/campaigns/product_realization/pr_play_71/12_FAILURE_RECOVERY.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/12_FAILURE_RECOVERY.md`.
- `support/development/campaigns/product_realization/pr_play_71/13_DEVELOPMENT_TESTS.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/13_DEVELOPMENT_TESTS.md`.
- `support/development/campaigns/product_realization/pr_play_71/14_FROZEN_HOLDOUT.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/14_FROZEN_HOLDOUT.md`.
- `support/development/campaigns/product_realization/pr_play_71/15_REAL_HTTP_LIFECYCLE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/15_REAL_HTTP_LIFECYCLE.md`.
- `support/development/campaigns/product_realization/pr_play_71/16_BROWSER_LIFECYCLE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/16_BROWSER_LIFECYCLE.md`.
- `support/development/campaigns/product_realization/pr_play_71/17_PLAYER_SAFE_PROJECTION.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/17_PLAYER_SAFE_PROJECTION.md`.
- `support/development/campaigns/product_realization/pr_play_71/18_STATE_AND_DISCLOSURE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/18_STATE_AND_DISCLOSURE.md`.
- `support/development/campaigns/product_realization/pr_play_71/19_LATENCY.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/19_LATENCY.md`.
- `support/development/campaigns/product_realization/pr_play_71/20_PLAYER_EXPERIENCE.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/20_PLAYER_EXPERIENCE.md`.
- `support/development/campaigns/product_realization/pr_play_71/21_REGRESSION_RESULTS.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/21_REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_71/22_LIMITATIONS_AND_OPEN_RISKS.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/22_LIMITATIONS_AND_OPEN_RISKS.md`.
- `support/development/campaigns/product_realization/pr_play_71/23_NEXT_SESSION.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `development/campaigns/product_realization/pr_play_71/23_NEXT_SESSION.md`.
- `support/docs/NEXT_SESSION.md`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `docs/NEXT_SESSION.md`.
- `support/game/api.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `game/api.py`.
- `support/game/campaign_reset.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `game/campaign_reset.py`.
- `support/game/quarantined_investigation_narration.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `game/quarantined_investigation_narration.py`.
- `support/game/storage.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `game/storage.py`.
- `support/tests/test_pr_play_71_lifecycle.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `tests/test_pr_play_71_lifecycle.py`.
- `support/tests/test_pr_play_71_persistence_recovery.py`: Selected PR71 implementation, original evidence, or final repair verification. Canonical source: `tests/test_pr_play_71_persistence_recovery.py`.

## Explicit omissions

- `artifacts/pr_play_71/development_third.txt`: duplicate content of artifacts/pr_play_71/development_disclosure.txt; canonical reference retained
- `artifacts/pr_play_71/frozen_source/artifacts/pr_play_71/cases.py`: duplicate content of artifacts/pr_play_71/cases.py; canonical reference retained
- `artifacts/pr_play_71/holdout.py`: duplicate content of artifacts/pr_play_71/frozen_source/artifacts/pr_play_71/holdout.py; canonical reference retained
- `artifacts/pr_play_71/persistence_recovery_final.txt`: duplicate content of artifacts/pr_play_71/optional_preservation.txt; canonical reference retained
- `artifacts/pr_play_71/regression_run.txt`: duplicate content of artifacts/pr_play_71/package_run.txt; canonical reference retained
- `development/campaigns/product_realization/pr_play_71/01_EXECUTIVE_SUMMARY.md`: duplicate content of development/campaigns/product_realization/pr_play_71/01_EXECUTIVE_SUMMARY.md; canonical reference retained
- `game/authored_consequences.py`: duplicate content of artifacts/pr_play_71/frozen_source/game/authored_consequences.py; canonical reference retained
- `static/app.js`: duplicate content of artifacts/pr_play_71/frozen_source/static/app.js; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
