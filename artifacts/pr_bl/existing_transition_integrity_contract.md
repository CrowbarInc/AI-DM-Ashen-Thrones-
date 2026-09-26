# Existing Transition Integrity Contract

Mapped before the PR-BL production edit. Owners below are the ones the repair uses. No second travel router was added.

## Successful travel

Player text
→ `parse_freeform_to_action` (`game/intent_parser.py`)
→ travel or `scene_transition` when a prefix, declared-travel pattern, embedded named place, or follow/pursue matcher hits
→ destination extraction: `extract_travel_destination_phrase` (`game/scene_destination_binding.py`)
→ exit match: `resolve_authored_exit_from_player_travel`, `_match_follow_pursuit_exit`, `_match_exit`
→ execution: `resolve_exploration_action` (`game/exploration.py`)
→ success signal: `resolved_transition is True`, or `state_changes.scene_transition_occurred` / `scene_changed` / `arrived_at_scene`
→ narration agreement: `apply_stay_leave_narration_agreement_to_gm` (`game/narration_state_consistency.py`)
→ scene state: authoritative `activate_scene` from the resolution, not from model `activate_scene_id`

`I'll head toward the old milestone` and `I go to the old milestone` already took this path. `I follow the missing patrol rumor` and `I follow the northwest mud track` bind `old_milestone` through the existing follow/pursue matcher when the scene clue and exit label overlap.

## Recognized but unresolved travel

Player text
→ travel kind, no `target_scene_id`
→ `resolved_transition` is not true
→ PR-BF: `apply_stay_leave_narration_agreement_to_gm` rewrites false arrival only when kind is `travel` or `scene_transition`
→ scene-emit integrity: `unresolved_travel` in `game/final_emission_scene_emit_integrity.py` selects the unfinished-way line when that travelish fallback runs

`I'll head northwest` is this case. Destination is the compass word. It does not select an exit merely because an exit is thematically northwest.

## Unparsed movement (the human failure)

Player text such as `I proceed northwest`
→ `parse_freeform_to_action` returned `None` because `proceed` was outside the travel-verb family
→ no travel owner, no PR-BF kind check
→ procedural freeform narration (`resolution` is None)
→ `_validate_gm_scene_update_for_legacy_adoption` (`game/api.py`) accepts any small string lists
→ `_apply_post_gm_updates` copies `visible_facts_add`, `discoverable_clues_add`, `hidden_facts_add`, and `mode` into the runtime overlay

## Function map

| Concern | Owner |
| --- | --- |
| Travel-verb recognition | `TRAVEL_PREFIXES`, `_RE_SCENE_TRAVEL_DESTINATION`, `_RE_ACTIONABLE_COMMITMENT`, `_TRAVEL_VERB_PREFIX_RE`, `_DECLARED_TRAVEL_WITH_DEST_PATTERNS` |
| Destination extraction | `extract_travel_destination_phrase` |
| Exit matching | `resolve_authored_exit_from_player_travel`, `_match_follow_pursuit_exit` |
| `resolved_transition` | `resolve_exploration_action`; success helper `_resolution_supports_travel_success` |
| PR-BF narration agreement | `apply_stay_leave_narration_agreement_to_gm`, gated on kind `travel` / `scene_transition` |
| Model realization | `_build_gpt_narration_from_authoritative_state`; unparsed path passes `resolution=None` |
| Legacy scene_update shape check | `_validate_gm_scene_update_for_legacy_adoption` (structure only) |
| scene_update adoption | `_apply_post_gm_updates` → `get_runtime_scene_overlay` |
| Overlay mutation | `visible_facts_add` on the overlay; clues, hidden facts, and mode under `mutations` |
| Discoverable clue / hidden fact / mode | those same overlay keys; not a separate gameplay policy |
| Local movement | `looks_like_local_physical_movement` → kind `custom`, lane `local_physical_movement` |

## What the repair is allowed to change

Directional `proceed` joins the existing travel-verb family when a compass direction or a route/destination follows. Bare compass words still do not choose an exit.

Narration agreement and scene-update adoption consult the same success signal even when kind is missing or `custom`. The structural validator stays structural.
