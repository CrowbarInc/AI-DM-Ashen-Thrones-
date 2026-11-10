# Campaign

Campaign: AT-OPT-04 Mixed-Key Response Policy Deduplication
Identifier: `at_opt_04`
Date: 2026-11-08
Generated: 2026-11-08T19:26:18Z
Purpose: Remove individually identical nested turn-packet policy keys from the serialized primary narration request, and measure that reduction without a provider call.

# Executive Summary

Verdict A/PASS. Live provider calls: 0. omit_duplicate_turn_packet_policy now drops each nested policy key whose complete JSON value equals the root, and keeps differing and root-absent keys. The root policy hash is unchanged. On the F3 build_messages reconstruction the blob falls from 83,040 bytes to 80,403, a reduction of 2,637 bytes (3.18%). The admission estimate falls from 27,744 to 26,865, minus 879. That estimate is bytes divided by 3 plus 64. It matches the AT-OPT-03 hypothesis and is not a provider bill. The recorded F3 input remains 22,777. Twelve equal keys are removed. response_delta, answer_completeness, and planner_seam_trace stay, and their value hashes are unchanged. No other request section hash changes. must_advance_scene stays true. New matrix 17/17 and existing provider-efficiency tests 7/7. Adjacent authority and publication tests 118/118. Frozen developer holdout 28/28, redirected so the historical results file was not rewritten. Protected files 150/150. The same three KeyError failures were present before the edit. Provider-free checks do not prove that a model reads the shorter request as the same narration.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- Changed omit_duplicate_turn_packet_policy in game/gm.py so identical nested policy keys are removed one at a time. Differing keys, root-absent keys, the root policy, and malformed structures stay. The file was already dirty; the function diff is artifacts/at_opt_04/implementation.diff.

## Validation changes

- Added tests/test_at_opt_04_mixed_key_policy.py. Seventeen provider-free cases cover the mixed-key matrix, immutability, idempotence, and one F3 build_messages reconstruction.

## Tooling changes

- Added artifacts/at_opt_04/measure_primary_narration.py. It rebuilds the F3 request, blocks OpenAI, and refuses call_gpt.

## Documentation changes

- Added the AT-OPT-04 reports under development/campaigns/product_realization/at_opt_04/.
- Prepended the AT-OPT-04 result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added baseline and optimized measurements, the semantic comparison, regression counts, the protected-file rehash, and the redirected holdout result under artifacts/at_opt_04/.
- Generated this review handoff. The archive digest sidecar is written after the zip is sealed.

# What Was Tested

- **Focused tests:** Before the edit: 11 passed, 3 failed, 0 skipped. After the edit: new matrix and PR-ED 24 passed, 0 failed. The same three KeyError tests failed again: provider_context_projection, gm_only, and social_context.
- **Broader relevant tests:** Adjacent classification, integration, physical-flag, and publication tests: 118 passed, 0 failed, 0 skipped. No full historical 1065 suite.
- **Full suite:** Not run.
- **Runtime validation:** Provider-free build_messages reconstruction of snapshot 2026-11-08T16-50-45_8caf7aff. Root policy unchanged. Twelve equal nested keys removed. Three unequal keys preserved. No other section hash changed. Disk state unchanged.
- **Model/runtime boundary:** Live provider calls: 0. The measurement replaced the OpenAI constructor and call_gpt. The holdout blocked non-local sockets and recorded 0 blocked connections. Byte counts are not provider tokenizer counts. No Gameplay Benchmark was run.
- **New regressions:** None in the focused, adjacent, holdout, or protected-file slices. An earlier adjacent run with ASHEN_DISABLE_PROVIDER_CALLS=1 failed three classification tests; the isolated rerun without that override passed 118/118.
- **Pre-existing failures:** The worktree was already dirty. The three KeyError failures were reproduced before the helper edit and again after it. Causes: the harmless-social projection did not select, and project_narration_payload strips gm_only and social_context.
- **Self-contained bundle review:** The bundle contains the five AT-OPT-04 reports, the before/after measurements, the semantic comparison, the helper diff, and the redirected holdout and protected-file results. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- No product decision is required to accept this serialization change.
- Do not treat the 879-token admission delta as a measured provider saving.
- Do not start AT-OPT-05 from this handoff.

# Known Problems / Unresolved Findings

## Campaign-specific

- The captured 22,777-token prompt is still absent. The 83,040-byte baseline is a reconstruction, and it remains well above the recorded input after this 2,637-byte cut.
- Provider-free preservation does not prove that a model treats a root-only copy as equivalent to the duplicated nested copy.

## Pre-existing baseline

- Three prompt tests still fail with KeyError for provider_context_projection, gm_only, and social_context.
- must_advance_scene is still true on this reconstruction, so the long instruction list stays.
- The worktree was already dirty at entry. HEAD does not uniquely identify the executable source.

# Missing Concepts / Future Capabilities

- A live tokenizer count for this shorter request.
- A stored copy of the original F3 provider payload.

# What This Campaign Does NOT Prove

- It does not prove a provider-billed token saving or a latency improvement.
- It does not prove that narration quality is unchanged. No live narration was generated.
- It does not prove a Gameplay Benchmark result. No benchmark was run.
- The 17 new tests were authored with the implementation. They are not an independent holdout.
- It does not authorize bypassing the compact-instruction gate or capping production openings at 3,000.

# Recommended Next Step

Stop. Do not start AT-OPT-05. Do not bypass the compact-instruction gate. Do not cap production openings at 3,000. Do not open PR-PLAY-80. Do not treat the 879 admission delta as a measured provider saving.

# Review Bundle Contents

Bundle file count: `17`
Bundle ZIP size: `000000084674` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/at_opt_04/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/at_opt_04/SUMMARY.md`.
- `support/development/campaigns/product_realization/at_opt_04/DEDUPLICATION_CONTRACT.md`: Equality rules, preserved data, immutability, and idempotence. Canonical source: `development/campaigns/product_realization/at_opt_04/DEDUPLICATION_CONTRACT.md`.
- `support/development/campaigns/product_realization/at_opt_04/CONTEXT_MEASUREMENT.md`: Snapshot, byte counts, estimate, and structural comparison. Canonical source: `development/campaigns/product_realization/at_opt_04/CONTEXT_MEASUREMENT.md`.
- `support/development/campaigns/product_realization/at_opt_04/REGRESSION_RESULTS.md`: Commands, counts, baseline failures, and the protected rerun. Canonical source: `development/campaigns/product_realization/at_opt_04/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/at_opt_04/INTEGRITY.md`: Branch, dirty-tree preservation, hashes, and the zero-provider confirmation. Canonical source: `development/campaigns/product_realization/at_opt_04/INTEGRITY.md`.
- `support/artifacts/at_opt_04/semantic_comparison.json`: Machine-readable root, removed, and preserved policy comparison. Canonical source: `artifacts/at_opt_04/semantic_comparison.json`.
- `support/artifacts/at_opt_04/baseline_measurement.json`: Provider-free F3 reconstruction before the helper edit. Canonical source: `artifacts/at_opt_04/baseline_measurement.json`.
- `support/artifacts/at_opt_04/optimized_measurement.json`: Provider-free F3 reconstruction after the helper edit. Canonical source: `artifacts/at_opt_04/optimized_measurement.json`.
- `support/artifacts/at_opt_04/implementation.diff`: The only production change, isolated from the preexisting dirty file. Canonical source: `artifacts/at_opt_04/implementation.diff`.
- `support/artifacts/at_opt_04/regression_results.json`: Machine-readable test counts and failure causes. Canonical source: `artifacts/at_opt_04/regression_results.json`.
- `support/artifacts/at_opt_04/protected_rehash.json`: 150 protected files unchanged. Canonical source: `artifacts/at_opt_04/protected_rehash.json`.
- `support/artifacts/at_opt_04/holdout_rerun.json`: Redirected frozen holdout, 28 passed, historical results file not rewritten. Canonical source: `artifacts/at_opt_04/holdout_rerun.json`.
- `support/tests/test_at_opt_04_mixed_key_policy.py`: Focused matrix and the assembly-path check. Canonical source: `tests/test_at_opt_04_mixed_key_policy.py`.
- `support/artifacts/at_opt_04/measure_primary_narration.py`: Reproducible provider-free measurement. Canonical source: `artifacts/at_opt_04/measure_primary_narration.py`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
