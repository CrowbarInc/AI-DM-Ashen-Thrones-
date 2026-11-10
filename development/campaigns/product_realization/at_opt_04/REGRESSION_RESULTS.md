# Regression Results

Live provider calls: 0. No Gameplay Benchmark was run.

| Command | Result |
| --- | --- |
| Baseline, before the edit: PR-ED, PR-DE, and the compact-prompt test | 11 passed, 3 failed, 0 skipped |
| New matrix plus existing PR-ED | 24 passed, 0 failed, 0 skipped (17 new, 7 existing) |
| PR-DE and the compact-prompt test after the edit | 4 passed, 3 failed, 0 skipped. Same three identities |
| Classification, integration, one physical flag test, and the two publication checks | 118 passed, 0 failed, 0 skipped |
| Frozen 79D-F3 holdout, results under `artifacts/at_opt_04/` | 28 passed, 0 failed. Digest `917d67fd5b997699d850311dfe4b405933f8c4b84989c39f5dfbdfdf8c3f6945` |
| Protected file rehash against `artifacts/pr_play_79df3/protected_entry.json` | 150 unchanged, 0 changed, 0 missing |

The new tests were written with this change. They are not an independent holdout. The F3 assembly check is the same reconstruction AT-OPT-03 measured.

## Baseline failures

Confirmed on this tree before the edit, and again after it:

- `test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context` — `KeyError: provider_context_projection`. That key is written only when the harmless-social projection predicate selects. It did not.
- `test_full_context_classes_stay_unprojected_while_mirrors_drop` — `KeyError: gm_only`. `project_narration_payload` strips that private field.
- `test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload` — `KeyError: social_context`. `project_narration_payload` removes `social_context`.

They were not repaired. They do not fail because a duplicate policy key was removed.

## Isolated rerun

A first adjacent run set `ASHEN_DISABLE_PROVIDER_CALLS=1` and overlapped another process. Three classification tests then failed. Those tests clear provider blocking themselves. Rerun alone, without that override and without an API key: 118 passed. That first trio is not a new product failure.

The holdout runner refuses non-local sockets. Blocked connections: 0. It does not write `artifacts/pr_play_79df3/holdout_results.jsonl`.

No new failure identity in the slices above.
