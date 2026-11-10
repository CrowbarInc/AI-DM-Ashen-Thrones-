# Regression results

Live provider calls: 0. No Gameplay Benchmark was run. The new tests were written with this change. They are not an independent holdout. The frozen holdout was not edited.

| Command | Result |
| --- | --- |
| Baseline, before the edit: transition node, transition consumption, PR-DE, compact prompt | 15 passed, 3 failed, 0 skipped |
| Focused, after the edit: new matrices, existing transition tests, transition consumption, PR-ED | 42 passed, 0 failed, 0 skipped (24 new, 18 existing) |
| Same baseline command after the edit | 15 passed, 3 failed, 0 skipped. Same three identities |
| Classification, integration, one physical-flag test, and the two publication checks | 118 passed, 0 failed, 0 skipped |
| Frozen 79D-F3 holdout, results under `artifacts/at_opt_06/` | 28 passed, 0 failed. Digest `917d67fd5b997699d850311dfe4b405933f8c4b84989c39f5dfbdfdf8c3f6945`. Non-local connections blocked: 0 |
| Protected file rehash against `artifacts/pr_play_79df3/protected_entry.json` | 150 unchanged, 0 changed, 0 missing |

## Baseline failures

Confirmed before the edit and again after it. They were not repaired.

- `test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context` — `KeyError: provider_context_projection`
- `test_full_context_classes_stay_unprojected_while_mirrors_drop` — `KeyError: gm_only`
- `test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload` — `KeyError: social_context`

## New failures

None. The focused, adjacent, holdout, and protected slices introduced no new failure identity.

## Protected verification

The holdout runner wrote `artifacts/at_opt_06/holdout_rerun.json` only. It did not write `artifacts/pr_play_79df3/holdout_results.jsonl`. Intermediate per-case working files were removed after the result file was written. The historical snapshot was not modified.

Junit files: `artifacts/at_opt_06/baseline_junit.xml`, `baseline_after_junit.xml`, `focused_junit.xml`, `adjacent_junit.xml`.
