# Transition correction

## Root cause

`_slice_state_mutations` writes `state_mutations.scene.scene_id` for every narration that has a scene id. That value is the current scene. `_derive_transition_node` treated any `scene_id` or `activate_scene_id` as a required transition. On the F3 examine turn the only scene signal was `scene_id: frontier_gate`, equal to `ctir.scene_id`, with `resolved_transition` false. The node was still `location_change`, and `must_advance_scene` copied that flag. The player was not moved by the flag. Mode stayed `action_outcome`. Scene-advancement flags stayed false.

Failure class: implementation.

## Implementation boundary

The change is the scene-block predicate in `_derive_transition_node`. Comparison uses the existing `_as_str` strip. No second classifier was added. Caller-owned CTIR and public-slice objects are not mutated.

`_project_transition_node_for_prompt` now accepts null anchors when `transition_required` is false. That is the valid not-required shape the planner already emits. A required node still needs mapping anchors. Without that acceptance, the corrected node was dropped as a type error and a seam audit was attached to ordinary turns. Empty-dict anchors used by the existing consumption test still pass.

## Same-scene behavior

When the current scene id and the stamped scene id are both known and equal, and no other signal is present:

- `transition_required` is false.
- `transition_type` is `none`.
- Anchors are null.
- The scene-id source field is not recorded.
- `must_advance_scene` is false on the assembled narration payload.

Whitespace around the same id still matches. Ordinary same-scene physical action, NPC address, and inspection CTIRs do not require advancement.

## Genuine-transition controls

These still set `transition_required` on a same-scene stamp:

- stamped scene id different from the current scene (`location_change`)
- `activate_scene_id`, including an activation of the current scene
- `resolved_transition`, including a resolved transition whose target is another scene and one with no new target
- `target_scene_id`
- `arrived_at_scene` with another scene
- `time_skip`
- `scene_transition_occurred`

Equality does not clear those signals. Time skip stays type `time_skip`. Resolved travel to another scene still selects narrative mode `transition`. Mode selection itself was not edited. `target_scene_id` and `time_skip` can still require a node while mode stays `continuation`. That mismatch remains out of scope.

## Unknown identity

If the current scene id is missing and a scene-id stamp is present, the prior signal remains and the type is still `location_change`. A current id is not invented to force equality. If the destination stamp is missing, or both ids are missing, no location change is invented.

## State-mutation safeguards

Derivation does not write campaign, session, or scene state. The F3 rederivation left `active_scene_id` at `frontier_gate` and left the CTIR equal to its input copy. The historical snapshot file was not modified. Scene movement code was not changed.
