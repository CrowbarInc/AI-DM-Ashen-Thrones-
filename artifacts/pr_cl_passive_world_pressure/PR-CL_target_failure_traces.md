# PR-CL target failure traces

Both tests were reproduced with the project virtualenv, stubbed `call_gpt`, and no live provider call.

```
tests/test_turn_pipeline_shared.py::test_chat_single_wait_in_tense_scene_forces_interaction_pressure
tests/test_turn_pipeline_shared.py::test_chat_repeated_passive_actions_do_not_stall_into_atmosphere
```

Both fail at `_assert_concrete_pressure` (`tests/test_turn_pipeline_shared.py` lines 72–90). The helper requires the player-facing text to contain one of: a quotation mark, "cuts through the crowd", "stops at your shoulder", "comes straight to you", "squares up to you", "breaks the silence first", "if you're moving on this, move now", "question the runner", "work the notice", "east-road trail", "east road", "ask me now".

## Test 1 — single tense wait

Input: `"I wait."`

Seeded visible facts:

- Guards keep glancing at a missing patrol notice beside the checkpoint.
- A tavern runner lingers under an awning, selling rumors for coin.

Stubbed provider line: `Rain beads on the checkpoint while nobody moves first.`

| Boundary | Actual |
| --- | --- |
| Resolver | `generation`. Contract operation `unresolved`. Resolution kind `None`. No interlocutor. `passive_interruption_wait` does not match `"I wait."` (that parser only matches disturbance-specific clauses such as "holds position and waits"). |
| Passive bookkeeping | `passive_action_streak` 0 → 1. `last_player_action_passive` true. Marker `wait`. |
| Session clock | `time_pressure` 0 → 1. `current_date` stays `Day 1`. World clocks stay `{}`. |
| Scheduled evaluation | House Verevin pressure 2 → 3 and Ash Cowl pressure 2 → 3. Both emit `faction_pressure` into `event_log` and `resolution.world_tick_events`. Ordo Pyric pressure 1 → 2, below the event threshold of 3. Agenda progress 0 → 1, below the flag threshold of 3. Projects stay empty. NPCs stay at `frontier_gate`. |
| Validation | Accepted response is immutable, provenance `initial_generation`, `hard_valid` true. Text equals the stub. |
| Pressure rewriter | `escalate_passive_scene` is not called. The PR-CK seal runs first because no question or stall retry is owed. |
| Final text | `Rain beads on the checkpoint while nobody moves first.` Tags empty. No `passive_scene_pressure` debug note. |
| First divergence | The assertion demands an interruption phrase. The sealed line, the visible facts, and the faction-event texts contain none of those phrases. |

Scene momentum is not due on this first exchange (`momentum_exchanges_since` becomes 1 only after the turn). No stall retry runs.

## Test 2 — repeated passive actions

Turn 1 input: `"I wait."` Stub: `The damp air hangs over the gate as everyone watches everyone else.`

Same seal as test 1. Final text is the stub. `time_pressure` becomes 1. Verevin and Ash Cowl pressure events are stored and not narrated. Streak becomes 1. Momentum exchanges become 1.

Turn 2 input: `"I hold position and watch."` The same stub is returned for every provider call.

| Boundary | Actual |
| --- | --- |
| Resolver | `generation` / `unresolved` again. |
| Clock | `time_pressure` 1 → 2. Date still `Day 1`. World clocks still `{}`. |
| Scheduled evaluation | Ordo Pyric pressure crosses 3 and appends `Ordo Pyric's pressure mounts.` Verevin and Ash Cowl continue to 4. No NPC moves. |
| Scene stall | Momentum is due. Two provider retries still return the atmosphere stub. The escape hatch selects a grounded line from the visible fact. |
| Candidate narration | `As you watch the scene, a guard leans near the checkpoint, watching the road.` |
| Pressure rewriter | Now runs, because the stall replacement is not the sealed first line. Source `visible_figure`, streak 2. It appends the same grounded sentence again. |
| Final emission | Player text is the single grounded sentence. Tags include `retry_escape_hatch`, `forced_retry_fallback`, `retry_exhausted`, `scene_momentum:consequence_or_opportunity`, and `passive_scene_pressure`. Debug notes include `passive_scene_pressure:visible_figure:streak=2`. |
| First divergence | `_assert_concrete_pressure` fails on that grounded sentence. The later assertions (`passive_scene_pressure:` and `streak=2`) are already true and are not reached. |

Momentum bookkeeping resets (`momentum_exchanges_since` 0, `momentum_next_due_in` 3), so the engine treated the grounded line as the momentum beat.

A side effect of that fallback sentence: lead extraction stores a `visible_suspicious_figure` whose subject is `as you`. That is a bad parse of the fallback prose. It is not the assertion that fails, and it is outside the phrase contract. It was not repaired.

## Exact assertions

Test 1:

1. HTTP 200.
2. Player text matches `_assert_concrete_pressure`.
3. `gm_output.tags` contains `passive_scene_pressure`.

Test 2, on the second response only:

1. Both HTTP responses are 200.
2. Second player text matches `_assert_concrete_pressure`.
3. Debug notes contain `passive_scene_pressure:`.
4. Debug notes contain `streak=2`.

Neither test asserts clock movement, `event_log`, NPC location, or a durable scene-state transition.
