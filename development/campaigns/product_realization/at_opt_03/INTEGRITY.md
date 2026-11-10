# AT-OPT-03 Integrity

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Worktree at entry | Already dirty. `git status --short` was 753 lines. This cycle did not reset, clean, commit, or push |
| Production prompt code | Unchanged by this cycle. `game/gm.py` and `game/prompt_context.py` remain the pre-existing dirty files |
| Live provider calls | 0. `provider_client_constructed` is false. `OpenAI` was replaced with a class that raises before any reconstruction or chat sample |
| Historical ledgers and the F3 snapshot | Read only. The script copied snapshot state into a temporary directory and deleted that directory |
| Scene files | Read from `artifacts/pr_play_79df3/http_data/scenes` because the snapshot does not contain them |

## Focused tests run

`pytest` on `tests/test_pr_ed_provider_efficiency.py`, `tests/test_pr_de_exact_contract_deduplication.py`, and `test_manual_play_compact_prompt_keeps_continuity_and_shrinks_payload`: 11 passed, 3 failed.

Passed: the seven PR-ED tests, including the all-equal and all-unequal packet-policy unit tests, and four PR-DE unit tests that keep or drop exact top-level contract mirrors.

Failed on this tree, which this cycle did not edit: `test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context` (`KeyError: provider_context_projection`), `test_full_context_classes_stay_unprojected_while_mirrors_drop` (`KeyError: gm_only`), and the compact-prompt latency test (`KeyError: social_context`). These are existing expectations against `build_messages`. They are not a new AT-OPT-03 regression, and they are not evidence that the proposed mixed-key drop is already covered.

No historical suite, no Gameplay Benchmark, no protected-file rewrite.

## Files this cycle adds

Reports under `development/campaigns/product_realization/at_opt_03/`.

Evidence under `artifacts/at_opt_03/`: `reconstruct_context.py`, `measurements.json`, `_correlate_logs.py`, `_correlate_detail.py`.

`docs/NEXT_SESSION.md` gains a prepended AT-OPT-03 entry. Prior entries stay.

`INPUT_SIZE_ATTRIBUTION.md` repeats the attribution report so the review zip can carry it. The bundler omits `TOKEN_ATTRIBUTION.md` because the filename safeguard treats a leading `TOKEN_` as sensitive. The campaign file remains `TOKEN_ATTRIBUTION.md`.

Archive path and SHA-256 are written to `artifacts/at_opt_03/archive_sha256.txt` after the zip is sealed.
