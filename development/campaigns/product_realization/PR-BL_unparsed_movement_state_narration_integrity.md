# PR-BL — Unparsed Movement Must Not Narrate or Commit a Spatial Transition

Date: 2026-09-26
Era: Product Realization
Primary lane: State ↔ Narration Integrity

## Answer

Generative narration may decorate an authoritative gameplay result. It may not create one.

When no authoritative scene transition has succeeded, player-facing narration does not assert arrival or progress into new geography, and a model `scene_update` does not store that journey. The success signal is `resolved_transition is True`, or `state_changes.scene_transition_occurred`, `scene_changed`, or `arrived_at_scene`. Travel wording, movement verbs, and the presence of a `scene_update` are not that signal.

## First incorrect decision

Confirmed. On the human turn `I proceed North-West, as the runner directed.`, `parse_freeform_to_action` returned `None` because `proceed` was outside the travel-verb family. PR-BF never ran. Legacy scene-update adoption then stored the model's arrival.

The parser miss was not sufficient by itself. Ownerless realization was the second unsafe condition. Both are repaired.

## Production changes

1. `game/scene_destination_binding.py`
   Directional `proceed` / `proceeds` / `proceeding` joins destination extraction when a compass direction or a route preposition follows. `proceed with` and `proceed to <verb>` stay out.

2. `game/intent_parser.py`
   That same shape is scene-travel intent, so it reaches the existing travel branch and declared-travel patterns. It does not add a router.

3. `game/narration_state_consistency.py`
   `apply_stay_leave_narration_agreement_to_gm` now treats a missing resolution as no success. A transition claim is replaced with the existing unresolved terminal even when kind is absent or `custom`. Local repositioning does not match. `omit_unowned_transition_scene_update` drops a failed transition from a generative `scene_update` without dropping same-scene facts.

4. `game/api.py`
   `_apply_post_gm_updates` calls that omission after the structural validator and before the overlay write. The validator remains a shape check.

No geography database, second travel resolver, or noun-to-interactable promotion was added.

## Behavior

| Utterance | Result |
| --- | --- |
| `I proceed northwest.` | unresolved travel, destination northwest |
| `I proceed North-West, as the runner directed.` | unresolved travel, not `old_milestone` |
| `I follow the northwest mud track.` | transition to `old_milestone` |
| `I'll head northwest.` | unresolved travel, PR-BF unchanged |
| `I walk a few steps closer to the crates.` | local `custom` |
| `I proceed with the inspection.` | not scene travel |

## Validation

Focused: PR-BL 12 passed, PR-BF 14 passed, PR-BK 9 passed.

Full suite: 7,065 collected, 6,937 passed, 29 failed, 99 skipped. The 12 new tests account for the collection increase. 27 failures match the PR-BK inventory. Two additional failures are Windows `PermissionError` on pytest temp renames and pass alone. No unexplained PR-BL regression remains.

PR-BF remains settled. PR-BK remains settled.

## Deferred

Notice-board subject versus payload, social fact-versus-refusal, `to the watch` rebind, empty `The guard` fallback, compound execution, world time, and missing authored content stay deferred. Do not open PR-BM from this closeout.

## Next action

Stop. Run a fresh human playtest. Do not continue session `735ebd1cfb4567c4f97df6dc`.
