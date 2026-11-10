# Campaign

Campaign: AT-OPT-06 Same-Scene Transition Correction and Compact Eligibility Safeguard
Identifier: `at_opt_06`
Date: 2026-11-08
Generated: 2026-11-08T15:31:08-05:00
Purpose: Stop treating an unchanged scene id as a required location change, and keep plan-backed manual_play_auto narration on the full instruction list.

# Executive Summary

Verdict A/PASS. Live provider calls: 0. A same-scene scene-id stamp no longer sets transition_required or location_change. Genuine signals still do: a different scene id, activate_scene_id, resolved_transition, arrival, and time_skip. Equality does not clear an independent signal. On the F3 examine-turn CTIR both scene ids remain frontier_gate and resolved_transition is false. Re-deriving that CTIR now yields transition_required false, type none, and must_advance_scene false. Narrative mode stays action_outcome. The rederived manual_play_auto instruction list stays at 78 lines and is identical to the pre-change list. The serialized request falls from 79859 bytes to 79235. The admission estimate falls from 26683 to 26475, minus 624 bytes and 208 estimate. That estimate is bytes divided by 3 plus 64, not a provider bill. The recorded input remains 22777. Explicit compact and the detached auto path are unchanged. Visibility, first-mention, speaker, scene-anchor, and policy-bridge lines remain. Focused tests 42 passed. The baseline slice is 15 passed and 3 failed before and after. Those failures are the preexisting provider_context_projection, gm_only, and social_context KeyErrors. Adjacent tests 118 passed. Frozen holdout 28/28. Protected files 150/150. No Gameplay Benchmark was run.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- Changed the scene-block predicate in game/narrative_planning.py so a scene_id stamp equal to the known current scene is not a transition signal. activate_scene_id, a different stamp, and a stamp with no known current id keep the prior signal.
- Changed game/prompt_context.py so manual_play_auto stays on the full instruction list when a stamp-matched narrative plan is present. A not-required transition node with null anchors is accepted. Required nodes still need mapping anchors. The file was already dirty; the preexisting project_narration_payload call was left in place.

## Validation changes

- Added tests/test_at_opt_06_same_scene_transition.py and tests/test_at_opt_06_instruction_eligibility.py. Twenty-four provider-free cases cover the transition matrix, instruction selection, compact preservation, and one operational-refusal publication check.

## Tooling changes

- Added artifacts/at_opt_06/measure_f3.py. It rebuilds the F3 request in a temp data directory, blocks OpenAI and call_gpt, and writes only under artifacts/at_opt_06/.

## Documentation changes

- Added the AT-OPT-06 reports under development/campaigns/product_realization/at_opt_06/.
- Prepended the AT-OPT-06 result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added the before/after F3 measurements, the comparison, regression counts, the protected-file rehash, and the redirected holdout result under artifacts/at_opt_06/.
- Generated this review handoff. The archive digest sidecar is written after the zip is sealed.

# What Was Tested

- **Focused tests:** 42 passed, 0 failed, 0 skipped. 24 new tests and 18 existing transition, consumption, and provider-efficiency tests. Baseline slice after the edit: 15 passed, 3 failed, 0 skipped.
- **Broader relevant tests:** Adjacent classification, integration, physical-flag, and publication tests: 118 passed, 0 failed, 0 skipped. No full historical 1065 suite.
- **Full suite:** Not run.
- **Runtime validation:** Provider-free rederivation and build_messages on snapshot 2026-11-08T16-50-45_8caf7aff. Same-scene node is no longer required. Instruction text is unchanged at 78 lines. Detached compact path is unchanged. Disk snapshot unchanged.
- **Model/runtime boundary:** Live provider calls: 0. The measurement replaced the OpenAI constructor and call_gpt. The holdout blocked non-local sockets and recorded 0 blocked connections. Byte counts are not provider tokenizer counts. No Gameplay Benchmark was run.
- **New regressions:** None in the focused, adjacent, holdout, or protected-file slices.
- **Pre-existing failures:** The worktree was already dirty. The three KeyError failures were reproduced before the edit and again after it. Causes: the harmless-social projection did not select, and project_narration_payload strips gm_only and social_context.
- **Self-contained bundle review:** The bundle contains the AT-OPT-06 reports, the before/after F3 measurements, the regression counts, the redirected holdout, and the protected-file rehash. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No product decision is required to accept this correction.
- Do not treat the 208-token admission delta as a measured provider saving or as improved playability.
- Do not start AT-OPT-07 from this handoff.

# Known Problems / Unresolved Findings

## Campaign-specific

- The captured 22777-token prompt is still absent. The rederived request is not that bill.
- A saved narration bundle built before this correction is reused until a new plan is derived. The snapshot file still contains the historical required node.
- A missing current scene id with a nonempty stamp still uses the previous defensive location-change signal. A current id is not invented.

## Pre-existing baseline

- Three prompt tests still fail with KeyError for provider_context_projection, gm_only, and social_context.
- target_scene_id and time_skip can require a transition node while narrative mode stays continuation.
- The worktree was already dirty at entry. HEAD does not uniquely identify the executable source.

# Missing Concepts / Future Capabilities

- A stored copy of the original F3 provider payload.
- A live tokenizer count for the corrected request.
- A Gameplay Benchmark or authorized live-play check. None was run.

# What This Campaign Does NOT Prove

- It does not prove a provider-billed token saving or a latency improvement.
- It does not prove improved playability. No Gameplay Benchmark was run.
- The 24 new tests were authored with the implementation. They are not an independent holdout. The frozen 28-case holdout is a developer holdout, not external validation.
- It does not authorize AT-OPT-07, a compact-instruction swap for plan-backed turns, or a 3000-token production opening cap.

# Recommended Next Step

Stop the runtime-optimization sequence. Do not start AT-OPT-07. Return to PR-PLAY / ATGB gameplay only under a separate authorization. Do not open PR-PLAY-80 from this handoff. Do not cap production openings at 3000. Do not treat the 624-byte change as a measured provider saving. A playability claim still needs an authorized live-play check or the Gameplay Benchmark.

# Review Bundle Contents

Bundle file count: `22`
Bundle ZIP size: `000000101712` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/at_opt_06/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/at_opt_06/SUMMARY.md`.
- `support/development/campaigns/product_realization/at_opt_06/TRANSITION_CORRECTION.md`: Root cause, predicate, genuine-transition controls, and the unknown-identity boundary. Canonical source: `development/campaigns/product_realization/at_opt_06/TRANSITION_CORRECTION.md`.
- `support/development/campaigns/product_realization/at_opt_06/INSTRUCTION_ELIGIBILITY.md`: Plan-backed full-instruction hold and the preserved compact paths. Canonical source: `development/campaigns/product_realization/at_opt_06/INSTRUCTION_ELIGIBILITY.md`.
- `support/development/campaigns/product_realization/at_opt_06/F3_RECONSTRUCTION.md`: Before and after transition state, instruction count, and request size. Canonical source: `development/campaigns/product_realization/at_opt_06/F3_RECONSTRUCTION.md`.
- `support/development/campaigns/product_realization/at_opt_06/REGRESSION_RESULTS.md`: Commands, counts, baseline failures, and the protected rerun. Canonical source: `development/campaigns/product_realization/at_opt_06/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/at_opt_06/INTEGRITY.md`: Branch, dirty-tree preservation, and the zero-provider confirmation. Canonical source: `development/campaigns/product_realization/at_opt_06/INTEGRITY.md`.
- `support/artifacts/at_opt_06/f3_comparison.json`: Machine-readable before/after transition and instruction comparison. Canonical source: `artifacts/at_opt_06/f3_comparison.json`.
- `support/artifacts/at_opt_06/f3_before.json`: Provider-free F3 reconstruction before the predicate edit. Canonical source: `artifacts/at_opt_06/f3_before.json`.
- `support/artifacts/at_opt_06/f3_after.json`: Provider-free F3 reconstruction after the predicate edit. Canonical source: `artifacts/at_opt_06/f3_after.json`.
- `support/artifacts/at_opt_06/regression_results.json`: Machine-readable test counts and the empty new-failure list. Canonical source: `artifacts/at_opt_06/regression_results.json`.
- `support/artifacts/at_opt_06/implementation.diff`: Production diff against HEAD. The preexisting narration projection hunk is included because that file was already dirty. Canonical source: `artifacts/at_opt_06/implementation.diff`.
- `support/artifacts/at_opt_06/protected_rehash.json`: 150 protected files unchanged. Canonical source: `artifacts/at_opt_06/protected_rehash.json`.
- `support/artifacts/at_opt_06/holdout_rerun.json`: Redirected frozen holdout, 28 passed, historical results file not rewritten. Canonical source: `artifacts/at_opt_06/holdout_rerun.json`.
- `support/artifacts/at_opt_06/focused_junit.xml`: 42 passed, including the new matrices. Canonical source: `artifacts/at_opt_06/focused_junit.xml`.
- `support/artifacts/at_opt_06/baseline_junit.xml`: 15 passed and the three preexisting KeyError failures before the edit. Canonical source: `artifacts/at_opt_06/baseline_junit.xml`.
- `support/artifacts/at_opt_06/baseline_after_junit.xml`: The same three KeyError failures after the edit. Canonical source: `artifacts/at_opt_06/baseline_after_junit.xml`.
- `support/tests/test_at_opt_06_same_scene_transition.py`: Production transition matrix. Canonical source: `tests/test_at_opt_06_same_scene_transition.py`.
- `support/tests/test_at_opt_06_instruction_eligibility.py`: Instruction-selection and compact-path matrix. Canonical source: `tests/test_at_opt_06_instruction_eligibility.py`.
- `support/artifacts/at_opt_06/measure_f3.py`: Reproducible provider-free measurement. Canonical source: `artifacts/at_opt_06/measure_f3.py`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
