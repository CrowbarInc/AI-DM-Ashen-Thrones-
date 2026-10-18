# PR-DY recommendation

Decision: A — LIVE GAMEPLAY READY

Ordinary sentences submitted in the existing browser reached live interpretation, the PR-DU bridge, the existing resolvers, the disposable session, and the on-screen log.

- Inspect of the notice board discovered `notice_patrol_route` and showed that clue.
- A follow-up question to the captain was classified as ASK `guard_captain` and answered with the same clue.
- An unmarked rules question was classified as out of character and did not change gameplay state.
- An explicit `OOC:` message did not call the provider and did not change gameplay state.
- Sent usage was 3 requests, 2173 input tokens, 583 output tokens, 2756 total, model `gpt-4.1-mini-2025-04-14`.
- Three narration attempts were refused before send because their estimates exceed 8,000 input tokens. Token counts for those refusals are unavailable.
- Production saves were unchanged.
- Focused tests: 99 passed, 0 failed.
- The human playtest guide is in `PR-DY_human_playtest_guide.md`.

HUMAN PLAYTEST: NOT YET PERFORMED

## Next step

Independent review of `handoff/CURRENT_REVIEW.zip`, then a real 10–15 minute session using the guide. The player should choose the messages.

After that, if live narration under the 8,000 input ceiling is required, shrink the narration prompt. Do not raise the ceiling inside a verification run to force those calls through. The 29 shared-pipeline and exploration failures stay outside this cycle.
