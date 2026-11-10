# State transition evidence

## Before the first provider request

`GET /api/state` created a bootstrap session. Provider dispatches were 0. `campaign_started` was false, `turn_counter` was 0, and `active_scene_id` was `frontier_gate`. Character Galinor had 8/8 HP and one inventory entry. No discovered clues. No active-quest field exists on the campaign or session; that absence is an observability gap, not a discovered quest.

## After new campaign

`POST /api/new_campaign` succeeded. Provider dispatches remained 0. New session id `5cf4a79fbe05b34b0e3cc748`. Scene `frontier_gate`, Day 1, clocks all 0, turn 0, campaign not started, transcript empty.

## After rejected opening

| Field | Before start | After HTTP 422 |
| --- | --- | --- |
| campaign_started | false | false |
| active_scene_id | frontier_gate | frontier_gate |
| current_date | Day 1 | Day 1 |
| turn_counter | 0 | 0 |
| clocks | all 0 | all 0 |
| chat history | 0 | 0 |
| session log | 0 | 0 |
| discovered clues | none | none |
| HP | 8/8 | 8/8 |
| inventory count | 1 | 1 |

Documents whose bytes changed: `session.json` and `combat.json`.

Session payload changes were bookkeeping only:

- `last_saved_at` advanced from `2026-11-02T01:15:51.391164Z` to `2026-11-02T01:16:04.439796Z`.
- The persistence envelope `saved_at` and `integrity` changed with that save.
- `__turn_start_active_interaction_target_id` changed from null to an empty string.
- `debug_traces` gained a second identical `rebuild_active_scene_entities` entry.

`combat.json` changed only its envelope `saved_at`. The combat payload was unchanged.

No location change, time advance, clue discovery, HP change, inventory change, or quest change occurred. The rejected narration was not committed.

Expected mutation for a successful opening was `campaign_started: true` and one opening commit. That mutation is missing. No unexpected gameplay mutation was committed.

Narrative claims in the player-facing message do not contradict the state. The message says no turn was completed, and the state agrees. The unshown provider narration describes the gate scene that is already the active scene, but it was not accepted as world state.
