# State integrity

The comparison that matters is the finished baseline run against the finished live run, after removing save timestamps and the session integrity hash that covers them. `state_comparison.json` records that comparison.

| Pair | Character, world, conditions | Session and combat, after dropping save stamps |
| --- | --- | --- |
| Notice-board baseline vs live | identical | identical except `saved_at` and `integrity.payload_sha256` |
| Rain-barrel baseline vs live | identical | identical except `saved_at` and `integrity.payload_sha256` |
| Notice-board baseline vs timeout fault | identical | identical except `saved_at` and `integrity.payload_sha256` |

Clue knowledge matches inside each pair. The notice-board pair both record `notice_patrol_route`. The rain-barrel pair both record no new clue. Inventory and conditions are inside the character and conditions files, which matched.

Player-facing text matched in each pair. Mechanical kind, success, clue id, and clue text matched. Resolver behavior was the existing exploration path: one discovery on the board, no discovery on the barrel.

`scenario_results.json` also lists within-turn differences from the empty seeded session to the saved session. Those are the resolver committing the turn: the log line, the clue, turn counter, and the ordinary scene bookkeeping. They are not a difference between the baseline and the live run. The same shape appears when the live flag is off.

Canonical `data/` hashes were unchanged. `.env` was unchanged. Campaign writers were guarded in the automated tests; the hook did not call them. The provider text is stored under `artifacts/pr_play_53`, which is outside the campaign data directory.

No mismatch required a stop. The narration integration did not move authoritative state.
