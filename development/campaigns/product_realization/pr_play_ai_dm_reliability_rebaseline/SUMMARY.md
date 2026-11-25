# pr_play_ai_dm_reliability_rebaseline

Verdict: **A/PASS**. The current foundation was measured on the ordinary chat path with providers disabled. The highest-severity actionable defect was an admission hole: coverage already marked a negated or conditional player act as non-execution, but the gate did not stop it. "I do not persuade the guard captain." reached the captain as a request, advanced the turn, and created NPC runtime. "If he is listening, I try to persuade the guard captain." reached disabled narration and advanced the turn. Both now stop with no state change. A later real check still commits, and a following negation does not undo or repeat it.

The frozen forty and supplementary inputs were replayed. Visible text did not change, so the historical scores stay 12/40 successful, minimum quality 22/40, mean actionability 1.675, and supplementary executable 5/55. No broad-sample improvement is claimed. Combined regression: 455 passed / 17 failed, same identities. Focused regression: 470 passed / 1 failed, still `test_api_roll_initiative_returns_canonical_resolution`. Provider records in those runs: 0. No live provider call was made. The paused milestone `pr_play_social_check_repeat_and_legacy_stance` was not started.

No commit and no push. Last updated: 2026-11-15.
