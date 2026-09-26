# Scene-Update Authority Inventory

`_validate_gm_scene_update_for_legacy_adoption` checks shape: a dict, the four known keys, string lists, and short strings. Its comment says it does not make a gameplay-policy decision. PR-BL leaves that validator as the shape owner.

The policy owner is the next step, `_apply_post_gm_updates`, which calls `omit_unowned_transition_scene_update` before overlay writes. The success signal is `_resolution_supports_travel_success`: `resolved_transition is True`, or `scene_transition_occurred` / `scene_changed` / `arrived_at_scene`.

A missing resolution is not success.

## Fields

| Field | Class | When no transition succeeded |
| --- | --- | --- |
| `visible_facts_add` | A or B, per string | Keep strings that do not assert a spatial transition. Drop strings that do. |
| `discoverable_clues_add` | A or C | Keep the list when no string in the payload asserts a transition. If any string does, drop the whole list. Those clues are the invented journey's attachments. |
| `hidden_facts_add` | A or C | Same package rule as clues. |
| `mode` | A or B | Keep `social` and `combat`. Drop `exploration` and `travel` when the same payload asserts a transition. |

## A. Valid same-scene realization

A visible fact about the current scene, such as a loose mooring ring or a legacy test fact, with no arrival or route-progression claim. Also a clue, hidden fact, or mode on a payload that never asserts a transition. Existing gateway tests adopt those without a transition, and they still do.

## B. Transition-dependent realization

Player-progression claims: reached a place, arrived, entered the next district, left a place behind, proceeded down a road, were led past a boundary, a route stretches ahead, followed a track into the countryside, stepped into that stretch. The human overlay sentence `You have reached the northwest mud track...` is this class. It is not kept unless a transition actually succeeded.

## C. Unauthorized generative world mutation

A new clue or hidden fact that rides in the same `scene_update` as a class-B claim. The human banner clue and the hidden watcher are this class. They are not promoted into interactables. The strings are simply not written.

A clue with no transition claim, sent alone, remains class A. Noun-to-object promotion is out of scope. PR-BL blocks the transition package, not every new noun.

## D. Ambiguous legacy residue

`mode: exploration` on a payload that does not assert a transition. That still adopts, matching the existing mode test. It is not evidence that the player moved.

`activate_scene_id` and `new_scene_draft` were already ignored as advisory. PR-BL does not reopen that owner.

## Not the rule

No transition does not mean discard every `scene_update`. Same-scene facts stay.
