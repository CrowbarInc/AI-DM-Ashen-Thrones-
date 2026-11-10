# Transition semantics

`transition.transition_required` on the narration payload is a copy of `narrative_plan.transition_node.transition_required`. `prompt_context` does not infer it. It also writes that boolean onto `narration_obligations.must_advance_scene`.

The node is derived by `_derive_transition_node` in `game/narrative_planning.py` when a narration plan is built. It is stored on the session as `_runtime_narration_plan_bundle_v1` and reused while the CTIR stamp matches. `detach_ctir` removes the CTIR and that bundle together.

## What the flag means in code

It means “at least one listed signal was present,” not “the scene changed,” and not “narrative mode is transition.”

| Signal | Sets required | Recorded or synthetic result |
| --- | --- | --- |
| No signal | No | `transition_type: none`, mode `continuation` |
| `state_mutations.scene.scene_id` equal to `ctir.scene_id` | Yes | `location_change`, both anchors the same scene, mode stays `continuation` |
| `state_mutations.scene.scene_id` naming a different scene | Yes | `location_change`, mode stays `continuation` |
| `state_mutations.scene.activate_scene_id` | Yes | Covered by `test_state_mutations_scene_activates_transition_node`. Mode stays `continuation` |
| `resolution.target_scene_id` | Yes | `location_change`, mode stays `continuation` |
| `resolution.resolved_transition` | Yes | Mode becomes `transition` |
| `resolution.state_changes.arrived_at_scene` with a target scene | Yes | Type `travel`, mode `transition` |
| `resolution.metadata.transition_type = time_skip` | Yes | Type `time_skip`, mode stays `continuation` |

`game.ctir_runtime._slice_state_mutations` writes `scene.scene_id` whenever the narration has a scene id. That is the current scene, including when `resolved_transition` is false. The predicate then treats that field the same as `activate_scene_id`.

Narrative mode is chosen earlier, in `build_narrative_mode_contract`, while `derive_narration_obligations` still has `must_advance_scene` hardcoded false. Mode becomes `transition` only for an opening miss, or for `resolved_transition` / the scene-change state flags. A same-scene stamp does not select transition mode. Role weights for `action_outcome` already include a transition axis of 10. That weight is the mode table, not this flag.

`scene_advancement` on the payload is separate. It is true only for `resolved_transition` or the state-change flags. On the F3 examine turn those three flags are false while `transition_required` is true.

## Lifecycle

| Event | Flag |
| --- | --- |
| Initial obligation derivation | `must_advance_scene` false. No transition node yet |
| Plan build | Node is computed from the CTIR. Same-scene `scene_id` makes it true |
| Prompt render | Payload `transition` copies the node. `must_advance_scene` is overwritten from it |
| Same-stamp retry | `ensure_narration_plan_bundle_for_turn` returns the existing bundle. The flag is not recomputed |
| New resolved turn with a new stamp | A new CTIR is sliced. The current scene id is written again, so the new node is true again for the same reason |
| `resolution` is not a dict | API calls `detach_ctir` before prompt build. The node is gone and `transition` is null |
| `build_messages` alone, resolution `None` | Does not detach. A previously attached node is consumed. This is the AT-OPT-03 reconstruction |
| Publication rejected | No code on this path clears the node because narration failed. The stamp reuse keeps it. This was not replayed as a live publication |

The flag does not survive as a completed transition marker. It is either the current stamp’s node or a leftover attachment. It is true for ordinary non-transition actions because the current scene id is always a signal.

## Recorded examples

| Source | Player text on the CTIR | Resolved transition | Before | After | Required | Source field |
| --- | --- | --- | --- | --- | --- | --- |
| F3 snapshot `2026-11-08T16-50-45_8caf7aff` | I examine the notice board. | false | frontier_gate | frontier_gate | true | `state_mutations.scene.(scene_id\|activate_scene_id)` |
| F3 `http_data/session.json` | CTIR not at the file root |  | frontier_gate | frontier_gate | true | same |
| PR-PLAY-79 live session |  |  | frontier_gate | frontier_gate | true | same |
| PR-PLAY-79B live session |  |  | old_milestone | old_milestone | true | same |
| 79B snapshot `2026-11-08T03-56-00_28192c06` | I look around the milestone. | false | old_milestone | old_milestone | true | same |

## Suspected defect

**Class: implementation.** The earliest incorrect decision is the `scene_id or activate_scene_id` predicate in `_derive_transition_node`. The contributing writer is `_slice_state_mutations`, which records the current scene on every narration. Existing tests cover `activate_scene_id`, not a same-scene `scene_id`.

Gameplay consequence: the model is told a location change is required inside the scene it is already in, while the mode contract still says `action_outcome` and `scene_advancement` says nothing moved. This cycle did not show that the false label moved the player. The F3 step-back publication was a replaced fallback, and that routing defect stays closed.

Context-cost consequence: the false flag is the only compact blocker on the attached F3 rebuild, so the 78-line instruction list stays. Fixing the flag without a hold would select compact and drop authority lines. That cost is real. It is not a reason to keep calling a same-scene stamp a location change.

This is a correctness defect. It is also the reason the compact gate looks broader than the transitions it was meant to protect. It was not repaired in this cycle.

A related gap, not this defect: `target_scene_id` and `time_skip` set `transition_required` while narrative mode stays `continuation`. Mode and the node do not share one definition of “transition.” AT-OPT-06 should not redraw mode selection.
