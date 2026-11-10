# Change manifest

No existing gameplay, campaign-generation, narrative-generation, or provider-routing file was modified. `tools/playtest/runner.py` matches the PR-PLAY-33 repaired snapshot byte for byte. Every other `game/` and `tools/playtest/` file matches the PR-PLAY-33 pre-repair hash baseline. Git still shows those paths dirty against HEAD; that dirtiness predates this task and is listed in `preexisting_worktree_status.txt`.

New files:

- `artifacts/pr_play_34/PR_PLAY_34_INSPECTION.md` — phase-1 inspection of the preserved PR-PLAY-33 failure.
- `artifacts/pr_play_34/evaluate.py` — identified assertions. Bootstrap session existence is not a failure; campaign start, turns, gameplay, and provider dispatch are.
- `artifacts/pr_play_34/readiness.py` — offline controls A–G. Writes the process snapshot before controller cleanup. Does not change the shared launcher.
- `artifacts/pr_play_34/package_review.py` — this archive builder. It does not launch a worker.
- `tests/test_pr_play_34_readiness_diagnostics.py` — regression coverage for those assertion rules.
- `artifacts/pr_play_34/controls/` and `artifacts/atgb/pr_play_34/readiness/` — captured control evidence.
- Review reports, `regression.xml`, and `readiness_summary.json`.

The PR-PLAY-33 diagnostic and its failed run were left in place.
