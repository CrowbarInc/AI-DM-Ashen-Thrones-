# Root cause

## Original T04 trace

Provider-free HTTP request, unchanged scene seed, captured before the production edit:

> I walk over to the notice board and put a hand on the frame.

Published:

> Notice board is here. Approaching or touching it is not a supported action, and you have not moved.

| Field | Before |
|---|---|
| Scene | `frontier_gate`, location Cinderwatch Gate District |
| Interactable | `notice_board` |
| Category | `DECLINE` |
| Reason | `local_object_not_a_destination` |
| Intent family | `local_interaction` |
| Execution policy | `decline_unadjudicated_contact` |
| Kind | `conversational_decline` |
| Success | false |
| Scene transition | false |
| Publication pointer | the preceding Guard Captain line |

Evidence: `artifacts/pr_play_t04_local_action/before/t04_before.json`.

## Target resolution

The conversational move resolver uniquely grounded “notice board” in the current-scene catalog. Target identity was not the failure.

## Accessibility evidence

`frontier_gate.json` lists `notice_board` as a visible investigate interactable. No scene file under `data/` carries `accessible: true`. Positive accessibility for this class is the intersection of `visible_catalog` (`inspect_target` or `perceive_target`) and `classify_referenced_surface` returning `authored_interactable` with existence, visibility, and inspectability for the same id. The original decline never consulted that intersection. It treated every unique local catalog hit as unadjudicated contact.

## Physical-action owner

`game/local_interaction.py` already owned same-scene approach normalization for ASK/INSPECT and explicitly did not grant movement. `game/physical_adjudication.py` is a separate experimental owner. It persists `ledger["position"]` and defaults `accessible=True`. The twelve-turn harness leaves that flag unset, and this cycle does not route through it.

## Blocking boundary

The earliest wrong decision is `_local_presence_decision` in `game/conversational_orchestration.py`. After a unique local-object hit it returned a decline. `_chat_turn` published that decision through the non-mutating conversational response because the category was not `EXECUTE`. Exploration and physical adjudication never received the turn.

This is an implementation failure of an existing owner, not a missing verb synonym and not a missing action subsystem.

## Why the action was refused

The owner recognized the board and then had no authorized transient outcome for low-stakes approach or contact. The published sentence stated the refusal and that the character had not moved. Scene, inventory, and clues stayed unchanged, which was correct for the refusal and is preserved for the successful transient outcome.
