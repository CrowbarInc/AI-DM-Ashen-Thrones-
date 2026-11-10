# Integrity

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- The worktree was already dirty at entry. The first short-status sample was 784 lines. Those modifications were left in place.
- No production file was edited. No test expectation, fixture, or frozen result was edited.
- No commit. No push. No reset. No clean. No stash. No `git checkout` of a source file.
- Scene and session hashes after the runs match the hashes taken before them: `data/scenes/frontier_gate.json`, `market_quarter.json`, `old_milestone.json`, `data/session.json`, `data/world.json`, `data/combat.json`, and `data/session_log.jsonl`. `data/scenes/mill_loft.json` was absent before and after.
- Historical source was a copy outside the repository. Continuity, the intent parser, and referenced-surface classification in that copy are `git show HEAD`. Orchestration in that copy is the current file with the handoff insertions removed. `authored_travel_admission` remains there. The repository copies of those files were not replaced.
- The overlay's `static` path is a junction to the repository `static` directory. That junction is outside the repository.
- Live provider calls: 0. OpenAI construction was blocked. `ASHEN_DISABLE_PROVIDER_CALLS` was set for the captures. The handoff tests restore the production `call_gpt` wrapper, which returns before the network while that flag is set.
- No campaign opening route was called. The handoff replay uses `seed_gate` on an isolated directory.
- Pytest for the 176-test selection and the 7 handoff tests ran one process at a time.
- Known unrelated failures not in this selection, and not rerun: `provider_context_projection`, `gm_only`, and `social_context` KeyErrors.
- Files created for this audit are the reports under `development/campaigns/product_realization/pr_play_adjacent_regression/`, the evidence under `artifacts/pr_play_adjacent_regression/`, the prepended `docs/NEXT_SESSION.md` entry, and the review export.
- `handoff/CURRENT_REVIEW.md` and `handoff/REVIEW_MANIFEST.json` are the new review. `handoff/history/pr_play_adjacent_regression/` has the same summary, manifest, and zip.
- `handoff/CURRENT_REVIEW.zip` could not be replaced. The file is memory-mapped, and both overwrite and rename returned an error. It is still the previous campaign zip. The verified archive for this audit is `artifacts/pr_play_adjacent_regression/CURRENT_REVIEW(20261108-174500).zip`, also copied to `handoff/CURRENT_REVIEW(20261108-174500).zip`. Its SHA-256 is in `artifacts/pr_play_adjacent_regression/archive_sha256.txt`, which is not inside the zip.
