# PR-DK Investigation Report

Mode: ESCALATION ROUTING INVESTIGATION.

Live provider calls: 0 in the PR-DK harness. `ASHEN_DISABLE_LIVE_INTERPRETATION=1` is set before contract construction.

Git HEAD at start: d31beb7d73dd4fda0f22184a6a69b947b5f470ff.

Initial worktree: dirty before PR-DK. Existing modified areas included prior artifacts, `data/*.json`, many `game/*.py` modules, tests, and `handoff/CURRENT_REVIEW.*`. PR-DK preserves that worktree and only adds experiment/report artifacts plus the requested handoff refresh.

Three-way result over 21 deterministic rows:

- A: TP=3 FP=0 FN=6 precision=1.0 recall=0.3333333333333333
- B: TP=8 FP=2 FN=1 precision=0.8 recall=0.8888888888888888
- C: TP=9 FP=12 FN=0 precision=0.42857142857142855 recall=1.0

Decision: C - BOTH REQUIRE LIVE COMPARISON.

Rationale: independent deterministic checks materially improve fixture recall versus existing signals, but they add false-positive exposure in ordinary hypotheticals, negations, quotes, and single-focus pronoun follow-ups. Universal interpretation has predictable coverage and large call volume, but PR-DH already showed that interpretation quality and authority validity are not automatic. Deterministic fixture performance alone is therefore insufficient to pick a production strategy.
