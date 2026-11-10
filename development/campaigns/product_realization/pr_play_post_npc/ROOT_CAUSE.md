# Root cause

Traces: `artifacts/pr_play_post_npc/baseline_trace.json` before the repair, `artifacts/pr_play_post_npc/corrected_trace.json` after the solo rerun.

## T04

Utterance: "I walk over to the notice board and put a hand on the frame."

Scene: `frontier_gate`, interactable `notice_board`. Previous publication: the captain's patrol sentence. Parser result: none. The movement clause still extracted destination "the notice board." Catalog grounding already matched one inspect target. `_resolve_move_target` then called `_unknown_destination`. Earliest wrong decision: treating a unique local catalog hit as an unestablished destination. Publication: `destination_not_established`. No scene change.

Corrected decision: `local_object_not_a_destination`. Visible text says the notice board is here and the player has not moved. The clue stays undisclosed. The scene stays `frontier_gate`.

## T05

Utterance: "Read me the missing-patrol notice, not the tax lines."

The clause analyzer can see an inspection. Continuity ran first. `_supplied_overlap` matched tokens in the captain's sentence and returned `repeat_delivered_statement`. Earliest wrong decision: overlap replay before the inspection owner. The captain's sentence was published again.

Corrected path: continuity abstains because the utterance names the notice board. The turn discovers `notice_patrol_route`. The visible text starts with "The missing patrol was last seen taking the northwest mud track past the crates." The existing diegetic fallback then appends a stock sentence about someone jabbing at the board.

## T06

Utterance: "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording."

This is not an inspect. The same overlap branch replayed the captain. Earliest wrong decision: the same overlap replay, on a non-question. No inventory change occurred in the failure, because the turn never reached action adjudication.

Corrected decision: `unsupported_physical_manipulation`, using the existing unadjudicated sentence. Character JSON is unchanged. No writing mechanic was added.

## T09

Utterance: "What did that notice say about where the patrol was last seen?"

The deictic-question branch bound the ask to the previous NPC. The addressee bridge then returned `ungrounded_provider_target` because the ask had no confirmed addressee. Earliest wrong decision: forcing a named-object question onto the previous speaker. The bridge refusal was consistent with that ask.

Corrected decision: `INSPECT` of `notice_board`, reason `single_authoritative_component`. The publication is the already-searched recall of the disclosed clue. Hidden patrol details are not added.

## Shared versus independent

T05 and T06 share the overlap replay. T04 is a destination classification that ignored a local catalog hit. T09 is an earlier deictic binding. They meet only because conversational continuity runs before the current owner.

## Corrected boundaries

- `game/conversational_orchestration.py`: local catalog decline, grounded object question, ambiguous-object clarify, unbound physical decline.
- `game/conversational_continuity.py`: object abstain, overlap abstain, explicit-repeat recovery for a GM-owned delivered row.
- `game/referenced_surface.py`: keep a multi-token interactable prefix; add the past-tense content question.
- `game/intent_parser.py`: the same past-tense pattern, and one leading determiner stripped before the existing notice trim.

`git diff HEAD` on `conversational_orchestration.py` also contains preexisting dirty work. This cycle did not rewrite the intent parser or add a memory store.
