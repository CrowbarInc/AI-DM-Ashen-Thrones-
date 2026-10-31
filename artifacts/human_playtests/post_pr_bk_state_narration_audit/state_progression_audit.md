# State Progression Audit

Session `735ebd1cfb4567c4f97df6dc`. Compared with player-facing prose. Overlay mutations are listed separately from authored scene content because they were adopted from model `scene_update`, not from the transition owner.

| Turn | Scene | Date / time | Turn counter (session) | Clocks | NPC runtime / interlocutor | Relationships | Topics | Clues / leads | Interactables / search | Transition | Conditions / combat | What prose told the player had changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | `frontier_gate` | Day 1. World clocks empty | 1 at end of campaign start; final counter is 10 | `time_pressure` increments per chat. Final value 10. Suspicion, unrest, danger, occult stay 0 | No interlocutor | None recorded | None | None | None searched | Stay. Activate `frontier_gate` | Not in combat | Arrival at the gate as the opening. Matches seeds |
| 01 | unchanged | Day 1 | +1 | `time_pressure` +1 | No target | none | none | none | board not searched | none | none | Player has read curfew hours and the patrol route. State discovered nothing |
| 02 | unchanged | Day 1 | +1 | +1 | none | none | none | `notice_patrol_route` discovered. Lead registry row, `related_scene_ids` = `frontier_gate` only, `next_step` empty | `notice_board` searched and resolved | none | none | Curfew examination produced the patrol route. The discovery is real. The hours are not |
| 03 | unchanged | Day 1 | +1 | +1 | `tavern_runner` bound | disposition not shown changing | `topic_revealed` null. Runner topic not marked revealed | no new clue | none | none | none | Runner stated the route as city guidance |
| 04 | unchanged | Day 1 | 5 | +1 | runner kept (`active_interlocutor_followup`) | none | `topic:approach_around_away` stores an unshown generative count paragraph, provenance `generative_reply` | none | none | none | none | Runner cannot answer the count. Matches content |
| 05 | unchanged | Day 1 | 6 | +1 | switches to `gate_guard`. Salience of the runner ignored | none | `topic:find_information_perhap` stores an unshown banner paragraph with provenance `clue_knowledge` and authoritative text = the patrol clue | contextual-lead fragments of an unshown "no reward" line | none | none | none | Guard shrugs. No reward invented in the heard line. Speaker change is real state |
| 06 | id unchanged | Day 1 | 7 | +1 | interlocutor fields on the emission are empty. Topic-pressure speaker stays `gate_guard` from turn 05 | none | no new social topic | no registry discovery. Overlay `discoverable_clues_add` and `hidden_facts_add` gain banner and watcher sentences | none | `resolved_transition` null. `visited_scene_ids` still only `frontier_gate` | none | Player has traveled northwest onto the mud track, past crates, sheds, lanterns, and broken banners |
| 07 | unchanged | Day 1 | 8 | +1 | unchanged | none | last-answer payload (the real clue) is emitted. Banner paragraph is not | none | crates not created or searched | none | none | Repeats the route. Does not establish opened crates |
| 08 | unchanged | Day 1 | 9 | +1 | no speaker id. `last_exploration_action_key` becomes the banner custom id | none | none | overlay banner clue written again | no banner interactable | none | none | A guard speaks. No destruction fact |
| 09 | unchanged | Day 1 | 10 | `time_pressure` 10 | `current_interlocutor` null. `interaction_context.active_interaction_kind` `observe` | none | `topic_pressure_current` still the turn 05 guard exchange | overlay visible facts repeat arrival and add banner sigils. `mode` `exploration` | none | none | combat `in_combat` false | A guard speaks again. No further movement is narrated |

World event log at the end contains off-screen faction pressure and completed operations for House Verevin, the Ash Cowl, and Ordo Pyric. None of that was in the player-facing transcript.

## How much apparent gameplay progression existed only in narration?

Geographic progression the player was given:

- left the gate crowd
- turned northwest
- passed crates
- entered a mud track with sheds and lanterns
- found broken patrol banners
- reached the patrol's last known stretch
- was still on that path two turns later

Authoritative scene graph:

- zero scene transitions
- destination `old_milestone` never activated
- its milestone and mud prints were never reached

Authored information progression that did happen:

- one real discovery, `notice_patrol_route`, on turn 02
- `notice_board` marked searched
- interlocutor moved from nobody, to `tavern_runner`, to `gate_guard`
- turn counter and `time_pressure` advanced. Diegetic date stayed Day 1. There is still no world-clock owner

Model overlay progression, not authored and not a transition:

- visible fact: the player has reached the northwest mud track
- discoverable clue: broken patrol banners and matching sigils
- hidden fact: an unseen watcher
- scene mode forced to `exploration`
- those writes happened on turns 06, 08, and 09, including turns whose player-facing text was only `The guard says`

The actionable divergence is the false journey. Atmospheric gate detail on the opening is not progression. The unshown half-dozen paragraph and the unshown banner paragraph are stored memory, not heard progression. PR-BK kept the heard quantity answer as a refusal and, on turn 07, emitted the clue payload rather than the banner paragraph.
