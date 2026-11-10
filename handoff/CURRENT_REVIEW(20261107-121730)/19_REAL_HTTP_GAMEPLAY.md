# Real HTTP Gameplay

Both campaigns used `POST /api/new_campaign`, `POST /api/start_campaign`, typed `/api/chat`, and the authored survey or report actions. They were not seeded through a developer-only state API. Provider calls were disabled. The opening used the existing offline fixture.

## Campaign A — survey

- Asked whether a small loose stone could be shifted. The engine established an ordinary light stone beside the stonework.
- "I push the loose stone aside." Position became aside from the stonework.
- "Is the loose stone still beside the stonework?" Answered from the new position.
- "I push it farther." Position became farther aside from the stonework. World flags did not change.
- Snapshot, new campaign, load snapshot.
- "Where is the loose stone?" still answered farther aside.
- A sit question then "I sit on the stone seat." Posture became sitting.

Result: PASS. Snapshot `2026-11-07T17-09-47_5ef9adf6`.

## Campaign B — report

- "I approach the notice board." Position became beside the Notice board.
- The climb line did not establish stonework and did not change scene state.
- "Am I beside the notice board?" answered from the ledger.
- Snapshot, new campaign, load snapshot. The beside position remained.
- "I step back from the notice board." Position became back.

Result: PASS. Snapshot `2026-11-07T17-09-53_b1e2a90e`.

No response contained a hidden sentinel. Full turn records are in `artifacts/pr_play_76/http/http_campaigns.json`.
