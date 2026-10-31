# Diagnostic Probes

Isolated calls. The preserved session was not replayed. No chat POST. No write to `data/session.json` or the playtest bundle.

Scene envelope: `artifacts/human_playtests/20260926_post_pr_bk_latest_human_playtest/scene_definitions/frontier_gate.json`.

Functions: `parse_freeform_to_action`, `extract_travel_destination_phrase`, `resolve_authored_exit_from_player_travel`, `find_world_npc_reference_id_in_text`, `_residual_directed_prep_npc_should_bind`.

World NPCs for the alias probe: the three NPCs in `data/world.json` (`gate_guard`, `gate_serjeant`, `tavern_runner`). Read only.

## Travel / exit binding

| Utterance | Parse type | Target | Lane | Destination extract | Exit resolve |
| --- | --- | --- | --- | --- | --- |
| `Inclined to take this matter into my own hands, I proceed North-West, as the runner directed.` | None | — | — | None | None |
| `I proceed northwest.` | None | — | — | None | None |
| `I proceed along the eastern lanes.` | None | — | — | None | None |
| `I continue following the path.` | None | — | — | None | None |
| `Not deterred, I continue following the path.` | None | — | — | None | None |
| `I'll head northwest.` | `travel` | none | `actionable_stay_leave_or_pursuit` | `northwest` | None |
| `I head northwest along the mud track.` | None | — | — | None | None |
| `Take the path the runner described.` | `travel` | none | — | `path the runner described` | None |
| `I follow the missing patrol rumor.` | `scene_transition` | `old_milestone` | `actionable_stay_leave_or_pursuit` | None | `old_milestone` |
| `I follow the northwest mud track.` | `scene_transition` | `old_milestone` | `legacy_follow_exit_match` | None | None on the separate resolver; the parser's follow matcher bound it |
| `I pursue the missing patrol rumor northwest.` | `scene_transition` | `old_milestone` | `legacy_follow_exit_match` | None | None on the separate resolver |
| `I'll head toward the old milestone.` | `scene_transition` | `old_milestone` | `actionable_stay_leave_or_pursuit` | `old milestone` | `old_milestone` |
| `I go to the old milestone.` | `scene_transition` | `old_milestone` | `embedded_named_place_travel` | None | `old_milestone` |
| `I enter Cinderwatch.` | `scene_transition` | `market_quarter` | `embedded_named_place_travel` | None | `market_quarter` |
| `I walk a few steps closer to the crates.` | `custom` | none | `local_physical_movement` | None | None |

Reading:

- The authored rumor exit is already usable in natural language that follows the rumor, follows the mud track, pursues the rumor, or names the old milestone.
- Bare compass `northwest` after a recognized travel verb is unresolved `travel`. That is the PR-BF situation. It does not invent `old_milestone`.
- `proceed` and `I continue following the path` never become travel, so PR-BF's kind check never applies.
- Local `walk a few steps closer` stays `custom`. A repair must not turn that into a scene change.

## Notice board

| Utterance | Parse |
| --- | --- |
| `I examine the curfew section more carefully. I need to know what times are limited.` | `investigate` / `notice_board` |
| `I read the notice board.` | `investigate` / `notice_board` |
| `What do the notices say about the curfew?` | None |

The session's examine sentence is in the working bind family. The failure on turn 02 is the payload, not a missed interactable. The `What do the notices say` shape remains the already-recorded untargeted residue.

## Interlocutor continuity

`find_world_npc_reference_id_in_text` with the world roster:

| Utterance | Bound id |
| --- | --- |
| `Well, is there a reward for who finds out? Or perhaps, can turn in useful information to the watch?` | `gate_guard` |
| `Is there a bounty if I report what I learn to the watch?` | `gate_guard` |
| `Can I give useful information to the city watch?` | None |
| `Is there a reward for whoever finds the patrol?` | None |
| `Should I take this rumor back to the tavern runner?` | `tavern_runner` |
| `I ask the gate serjeant whether the watch pays for information.` | None from this function (`ask the` is not the `to/toward/at` prep) |

`_residual_directed_prep_npc_should_bind` on `can turn in useful information to the watch?`: `watch` true; `guard`, `runner`, and `serjeant` false.

The switch is the alias `watch` in `to the watch`, not the words reward, information, or patrol.

## What these probes do not execute

They do not call the model, the emission gate, or scene-update adoption. Those behaviors are taken from the log rows: turn 06 `generated_candidate` plus approved `scene_update`; turns 08–09 `anti_reset_local_continuation_fallback` with empty `speaker_label`.

No production repair was made in this audit, so no regression suite was run.
