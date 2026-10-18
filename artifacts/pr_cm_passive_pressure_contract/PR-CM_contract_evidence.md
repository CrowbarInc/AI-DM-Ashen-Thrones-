# PR-CM contract evidence

Live provider calls: 0.

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.

The worktree was already dirty. Nothing was reset. No product file was edited.

PR-CL decision inherited: B — TEST EXPECTATION DRIFT CONFIRMED.

The old test names are not descriptions of the current contract. They required deleted interruption templates.

## Authoritative expectations

| Concern | Authority | What a passive wait must do |
| --- | --- | --- |
| Session pressure | `game.clocks.advance_clock`, called from `game.api.chat` on every chat | `session.clocks.time_pressure` increases by 1. This is not a wait-owned duration. |
| Diegetic date | `session.current_date` | Stays `Day 1`. `world.world_state.clocks` stays empty. PR-BE. |
| World tick | `game.world.advance_world_tick` | Runs before narration. Faction threshold crossings and seeded mobile NPC moves are written to `world.event_log` and `resolution.world_tick_events`. |
| Faction threshold | `PRESSURE_THRESHOLD_EVENT = 3` | A faction whose pressure crosses 3 records `{name}'s pressure mounts.` Other factions still increment. |
| Mobile NPC | Same tick, only when `availability` is `mobile` and `agenda_move_to_scene_id` is set | The NPC location changes. The event text says the move is off-screen. Default `available` NPCs do not move. |
| Scene momentum | `docs/ai_gm_contract.md` and `game.gm._scene_momentum_due` | Default `momentum_next_due_in` is 2. The due threshold is `next_due_in - 1` (1 on the first window). After one completed exchange, the next exchange is due. A single momentum tag resets `momentum_exchanges_since` to 0 and toggles `momentum_next_due_in` between 2 and 3. The rule does not name an interruption phrase and does not authorize an unestablished actor. |
| Hard-valid seal | `run_preserve_if_valid` in `game.immutable_valid_response` | An unresolved hard-valid line is sealed when no question or stall retry is owed. The pressure rewriter does not replace it. |
| Scene-stall fallback | `scene_stall_check` in `game.gm_retry` | When momentum is due and the reply has no momentum tag, retry can replace weak atmosphere with a grounded visible fact. |
| Pressure metadata | `escalate_passive_scene` in `game.response_policy_enforcement` | When that rewriter runs, it stamps tag `passive_scene_pressure` and debug `passive_scene_pressure:{source}:streak={n}`. The beat is `render_grounded_perception_line`. The source subject is not spoken. |
| Grounded observation | `tests/test_grounded_observation_non_invention.py` and the passive-pressure prompt in `game.gm` | Visible tension does not authorize a new person, quoted speech, a clue, a route, or a confrontation. |
| Provider prose | `game.narration_state_consistency` | Narration is not provenance for a consequential state change. Tick mutations stay on `advance_world_tick`. |

## What the deleted tests required

`_assert_concrete_pressure` required the player line to contain a quotation mark or one of: `cuts through the crowd`, `stops at your shoulder`, `comes straight to you`, `squares up to you`, `breaks the silence first`, `if you're moving on this, move now`, `question the runner`, `work the notice`, `east-road trail`, `east road`, `ask me now`.

Those phrases belonged to `_render_passive_pressure_beat` before the PR-AR checkpoint removed them. The current renderer ignores the pressure source and returns a grounded perception line.

## What this cycle asserts instead

A single tense wait:

- HTTP 200, and the turn is not a social dialogue.
- `time_pressure` becomes 1.
- The world tick records the seeded House Verevin and Ash Cowl threshold events.
- The hard-valid provider line is kept.
- No interruption phrase is invented.
- No `passive_scene_pressure` tag is required, because the rewriter does not run.

A repeated passive wait:

- Both requests succeed.
- `time_pressure` becomes 2, and both turns record tick events.
- After the first exchange, `_scene_momentum_due` is true under the existing window.
- The second line drops the repeated atmosphere and restates a visible fact.
- `passive_scene_pressure` metadata and `streak=2` are present because that path ran.
- The final line passes `validate_generated_response`.
- No invented confrontation is required.
