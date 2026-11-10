# PR-PLAY-55 — Semantic generalization and discovery-claim hardening

Verdict: **A — PASS / READY FOR NEXT CONTROLLED EXPERIMENT**.

The quarantined narration check now treats `find` and `discover` as the same kind of claim. "You find a ribbon beneath the board." is rejected. "You discover a ribbon beneath the board." is rejected. "You notice a crack in the board." and "You notice a crack running through the weathered board." still pass. A ribbon the player comes to hold is rejected even when the sentence never says "find" or "discover". An unfamiliar marking is `REVIEW_REQUIRED`, not a pass and not an automatic discovery.

The two legacy false rejects are repaired in the rules that caused them. "At sundown, the guard makes his rounds along the west road." passes the combined prelude gate. "A little dust lies in your pack." passes it. A silver key in a pack still fails. An east-road patrol, against a west-road fact, still fails.

The previous 49 consequential fabrications still fail. Development fixtures: 40/40 match their labels, with 0 critical false negatives. The frozen holdout: 70/70 match their labels, with 0 critical false negatives. No provider was called. Player-facing narration stays off.

This pass does not authorize player-facing narration.

Measurement: `artifacts/pr_play_55/evaluation.json`, `performance.json`, `regression_summary.json`.
