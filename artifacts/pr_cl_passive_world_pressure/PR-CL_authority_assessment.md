# PR-CL authority assessment

No new scheduler, probability, validator weakening, or authority owner was added. No product code changed.

## Who owns what

| Concern | Owner | PR-CL result |
| --- | --- | --- |
| Session `time_pressure` | `game.clocks.advance_clock`, called from `game.api.chat` for every chat | Advances on wait. Not wait-specific. |
| Diegetic date | `session.current_date` | Stays `Day 1`, matching PR-BE. |
| Scheduled faction and project ticks | `game.world.advance_world_tick` | Evaluated. Threshold events land in `event_log`. |
| Mobile NPC movement | Same tick, only when `availability` is `mobile` and a destination is set | Does not fire for the default available NPCs. Fires in control C when that agenda is seeded. |
| Passive streak | `game.api._record_scene_pressure_input` | Streak 1, then 2. |
| Pressure narration | `escalate_passive_scene` in `game.response_policy_enforcement` | Blocked on a sealed hard-valid line. On the stall path it appends a grounded perception line and stamps `passive_scene_pressure`. |
| Hard-valid seal | `run_preserve_if_valid` in `game.immutable_valid_response`, invoked from `game.api` before policy enforcement when the operation is unresolved and no retry is owed | Keeps the provider atmosphere on the first wait. |
| Final narration | Provider, then seal, stall fallback, or grounded pressure beat | Provider text is not allowed to create the consequential event. The engine does not splice tick-event sentences into a valid line. |

## Authorization check

Waiting does not create an NPC, a clue, a route, or a confrontation.

The faction sentences "House Verevin's pressure mounts." and "The Ash Cowl's pressure mounts." are authorized off-screen tick results. The contract lets the provider describe them. It does not require the engine to overwrite a hard-valid line with them. Doing that on every chat would be a new narration policy, and those sentences still would not satisfy `_assert_concrete_pressure`.

The mobile-NPC event is explicitly off-screen: "Tavern Runner moves off-screen to scene_investigate." Control C updates `location` and leaves the valid lamp sentence in place. A later system can read the new location. The player line is not required to announce an off-screen move.

Scene tension authorizes the pressure due-check. It does not authorize quoted speech. The historical templates did that without an agenda, and the grounded-observation contract now forbids it.

## Integrity

No unauthorized event was added to the player-facing response. The one dirty state note is pre-existing lead parsing: the stall sentence "As you watch the scene..." can be stored with subject `as you`. PR-CL did not change that parser. Repairing it would be a lead-extraction change, not a passive-world pressure projection, and it would not satisfy the phrase tests.
