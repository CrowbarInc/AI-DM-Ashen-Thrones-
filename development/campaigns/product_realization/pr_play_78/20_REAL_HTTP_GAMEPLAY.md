# Real HTTP gameplay

`tests/test_pr_play_78_http.py` passed inside the 259-test closure run. The test uses `TestClient` against `game.api.app` with physical adjudication, dynamic NPCs, and the lifecycle helpers. It does not write a trace file, because artifact writes from pytest are refused. The assertions below are what the passing test checked. HTTP 200 is not the claim. The claim is those assertions.

Campaign A (chat turns, provider off):

- Look around.
- "I examine the notice board and ask the guard about the warning." The reply mentions the notice, the patrol, or the guard. It must not contain "northwest mud". This mixed turn does not publish the authored clue.
- Approach and greet. The reply mentions the guard.
- Ask whether anyone passed. No northwest route.
- Wait and watch.
- Climb the gate wall. The reply contains "not".
- Snapshot `integrated-a`, new campaign, load, then "Ask the guard what concerns him."

Campaign B:

- Create, start, `reach` (dedicated notice examine, follow the rumor, examine the milestone, prints clue, scene `old_milestone`, both branch affordances present).
- `choose("report")` through the authored action API, then return and the watch follow-up.
- Look around the milestone.
- Look for a struggle. Uncertainty, nothing invented.
- Offer to help search. No invented search party.
- "Am I standing?"
- Snapshot, new campaign, load. Scene id matches the pre-load id.
- Wait and watch.

No `SENTINEL` in the campaign JSON the test built. Player-facing sentences for these HTTP turns were not persisted to disk.
