# PR-CM test changes

No product file changed. The obsolete phrase helper `_assert_concrete_pressure` was removed from `tests/test_turn_pipeline_shared.py`.

## Before

`test_chat_single_wait_in_tense_scene_forces_interaction_pressure`

1. HTTP 200.
2. Player text matches `_assert_concrete_pressure`.
3. `gm_output.tags` contains `passive_scene_pressure`.

`test_chat_repeated_passive_actions_do_not_stall_into_atmosphere`

1. Both HTTP responses are 200.
2. Second player text matches `_assert_concrete_pressure`.
3. Debug notes contain `passive_scene_pressure:`.
4. Debug notes contain `streak=2`.

Neither test inspected `time_pressure`, `world_tick_events`, NPC location, scene momentum, or a hard-valid seal.

## After

`test_chat_single_wait_records_world_progress_and_keeps_hard_valid_narration`

1. HTTP 200.
2. Resolution is not social dialogue and has no interlocutor.
3. `session.clocks.time_pressure` is 1. `current_date` stays `Day 1`. World clocks stay empty.
4. Tick events and `event_log` contain `House Verevin's pressure mounts.` and `The Ash Cowl's pressure mounts.`
5. Faction pressure is Verevin 3, Ash Cowl 3, Ordo Pyric 2.
6. The accepted response is immutable, `hard_valid`, and equal to the provider line `Rain beads on the checkpoint while nobody moves first.`
7. The obsolete interruption lexicon and quotation marks are absent. Tick sentences are not copied into the player line.
8. `passive_scene_pressure` is absent from tags and debug notes.
9. Default NPCs stay `available` at `frontier_gate`. No discovered clues are added.
10. Passive streak is 1. Momentum exchanges are 1 and `momentum_next_due_in` is still 2. This turn did not take the scene-stall retry.

`test_chat_repeated_passive_waits_advance_world_and_ground_scene_stall`

1. Both HTTP responses are 200, and neither turn is social dialogue.
2. `time_pressure` is 2 after the second turn.
3. Both responses carry `world_tick_events`.
4. `event_log` still contains the Verevin and Ash Cowl events, plus `Ordo Pyric's pressure mounts.` Pressure is 4, 4, and 3.
5. After the first turn, exchanges are 1, `momentum_next_due_in` is 2, and `_scene_momentum_due` is true.
6. The second line is not the atmosphere stub. It contains `a guard leans near the checkpoint`.
7. Tags include `passive_scene_pressure`. Debug notes include `passive_scene_pressure:` and `streak=2`.
8. Stored streak is 2. Momentum resets to exchanges 0, kind `consequence_or_opportunity`, next due 3.
9. NPCs do not move. No discovered clues are added. Tick sentences stay out of the player line. The obsolete lexicon is absent.
10. `validate_generated_response` reports `hard_valid` for the final line. A sealed accepted record, when present, is not `rejected` and matches that line.

## Added controls

`tests/test_pr_cm_passive_pressure_contract.py`

- `test_quiet_wait_with_no_due_world_event_keeps_narration`
- `test_faction_threshold_wait_records_event_without_narrating_it`
- `test_seeded_mobile_npc_moves_offscreen_on_wait`
- `test_repeated_quiet_waits_ground_stall_without_a_new_event`
- `test_diagnostic_scene_stall_fallback_stores_as_you_lead_subject`

The diagnostic is a record of the known lead parse. It is not a passive-pressure contract requirement, and it does not repair the parse.
