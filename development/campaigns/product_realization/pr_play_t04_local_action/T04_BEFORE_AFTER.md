# T04 before and after

Request, unchanged:

> I walk over to the notice board and put a hand on the frame.

## Published text

| | Text |
|---|---|
| Before | Notice board is here. Approaching or touching it is not a supported action, and you have not moved. |
| After | You walk over to the notice board and rest a hand on its frame. You remain in Cinderwatch Gate District. |

## Routing

| Field | Before | After |
|---|---|---|
| Kind | `conversational_decline` | `conversational_answer` |
| Reason | `local_object_not_a_destination` | `transient_local_action_completed` |
| Policy | `decline_unadjudicated_contact` | `record_transient_outcome` |
| Owner | none | `local_interaction` |
| Success | false | true |
| Scene transition | false | false |
| Target | notice board, then declined | `notice_board` |

## Structured outcome

After the repair the metadata record completes both `local_movement` and `physical_contact`. Authority basis is `authored_interactable_visible_catalog` with existence, visibility, and inspectability. `scene_transition` and `persistent_state_changed` are false. `narration_authorized` is true.

## State

Scene stays `frontier_gate` on both sides. Character inventory is unchanged. The touch does not add `notice_patrol_route`. Clues already discovered from the preceding captain exchange remain.

## Publication pointer

Before, the pointer stayed on the Guard Captain’s milestone sentence because the decline did not publish. After, the pointer is the approach-and-contact narration. The accepted immutable text matches it. The next turn, T05, replaces the pointer with the authorized clue sentence, as it did before.
