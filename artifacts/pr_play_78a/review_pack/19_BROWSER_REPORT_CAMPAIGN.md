# Browser report campaign

Same host. New campaign, then typed chat only.

- Examine the notice board and ask the guard about the warning. -> northwest mud clue, then Gate Guard: "I do not know about that."
- I follow the missing patrol rumor. -> Old Milestone.
- I look at the weathered milestone and the tracks. -> overlapping prints, then a further part was not supported.
- I head back and tell the watch the trail is uncertain. -> authored report consequence.
- I return to Cinderwatch Gate. -> frontier gate.
- I give the watch the patrol report. -> authored warn consequence.
- What are my options? -> Cinderwatch Gate District, no further authored continuation.

Save status showed `frontier_gate` and 2 clues. Snapshot `2026-11-08T00-52-36_769b1fe4`. After reload and load, the scene was Cinderwatch Gate District and the same options answer was given. `browser_data/world.json` flags include `patrol_report` and `patrol_guards_warned`, and not `patrol_survey`.

Screenshots: `browser_shots/campaign_b_before_reload.png`, `campaign_b_after_resume.png`.

Network rows were `POST /api/chat`, `/api/state`, `/api/log`, `/api/start_campaign`, and `/api/snapshots`, all HTTP 200. No `/api/action` authored call was made by the typed sequence.
