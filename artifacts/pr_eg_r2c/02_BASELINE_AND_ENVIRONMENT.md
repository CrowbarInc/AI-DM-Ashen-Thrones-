# 02 — Baseline and Environment

Revision `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Existing dirty tree is recorded in working_tree_before.txt; the baseline is the entire starting worktree, not HEAD. before_hashes.json records source/data hashes. Runtime: 3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]. Client date October 17, 2026, America/New_York.

The 22-file historical regression selection was extracted from PR-EG-R1 junit and rerun: 393 passing / 19 failing. Exact identities are in regression_comparison.json and report 12. An initial sandbox TestClient run stalled; it was interrupted, then the same baseline ran successfully with local socket access. The failed sandbox attempt is not a regression result.

Observed fresh route: configured gpt-4.1-mini, returned gpt-4.1-mini-2025-04-14; production interpretation Responses path. No model substitution, recorded reply, or provider double was used in live qualification. The production routing code selected its configured model; no narration was required by these contained interactions. Usage/request identifiers and timing are in live_usage.jsonl. Credentials are excluded; active saves were not exported or sent. Disposable fictional fixtures only.
