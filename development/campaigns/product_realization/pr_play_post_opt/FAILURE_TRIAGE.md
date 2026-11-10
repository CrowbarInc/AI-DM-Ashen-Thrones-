# Failure triage

## Inventory

| Turn | Class | Repeated | State changed | Provider | Publication |
|---|---|---|---|---|---|
| T01 | Narrative realization of an already resolved observation | No | Turn advanced; scene held | `call_gpt` entered, not dispatched | Disabled sentence published as completed gameplay |
| T04 | Routing, conversational orchestration | Related to T05, T06, T09 | No | None | Event written; pointer held |
| T05 | Routing, `repeat_delivered_statement` | Yes, with T06 | No | None | Same NPC sentence published again |
| T06 | Routing, `repeat_delivered_statement` | Yes, with T05 | No | None | Same NPC sentence published again |
| T07 | Narrative fallback on an unresolved utterance | No | Turn advanced; incidental retained | `call_gpt` entered, not dispatched; one retry escape | Mashed sentence published |
| T08 | Narrative fallback; agency not answered | No | Turn advanced; scene held | Two `call_gpt` entries, not dispatched | Generic sentence published |
| T09 | Routing, `ungrounded_provider_target` | Related to T04–T06 | No | None | Clarification event; pointer held |
| T10 | Adjudication premise | No | Turn advanced; no items | None | Completed gameplay; trade refused |

T02 is weak and is not counted as a failure. T03 and T11 succeeded. T12 is a correct operational refusal.

## Dominant blocker

**Conversational orchestration answers a changed player intent with the previous NPC result.**

Evidence:

- T05 and T06 are different actions, a notice reading and a mud copy. Both resolved as `repeat_delivered_statement` and both spoke the captain's milestone line. Confidence is high. The reason is stored on the conversational decision, and no later resolver ran.
- T04 named the notice board, which is an interactable in `frontier_gate`, and was declined as `destination_not_established`. The player stayed, which is safe, and the action was not adjudicated.
- T09 asked what that notice said. The notice and the patrol were already in the conversation. The decision was `ungrounded_provider_target`, and the player was told the addressee was unknown.

This pattern is 4 of 12 turns, it sits on the turns where the player tries to leave the dialogue and use the scene, and it does not depend on a live model. It removes the player's next choice. It is reproducible from this seed and these utterances. The owner is the existing conversational-orchestration decision, not a missing campaign fact.

## Why it outranks the alternatives

Primary narration cost is real and is a known limitation. In this run the expensive path was not dispatched. T01 shows a separate realization gap: observation facts were selected and the disabled-provider sentence was published. That hurts one turn. The orchestration capture blocks the following inspection, reading, improvisation, and recall, which is the stretch a player actually needs after an NPC answer.

T07's mashed incidental is severe and should not be promoted into world truth. It happened once, on an intentionally vague command, and the retry path was already inside a provider-disabled run. It is the next candidate after the orchestration boundary, not the first repair.

T10's tavern premise is a single adjudication miss. The runner is present. The trade was still refused and no item was created.

Publication disagreement on T04 and T09 is real: an engine-response event was written while `last_publication` stayed on an earlier sentence. T12 shows the operational-refusal path still withholds the event. The pointer split is a consequence of the orchestration replies, and repairing the replies matters more than relabeling them.

## Root-cause hypothesis

After a hosted social answer, the conversational layer treats a later utterance as either a repeat of that answer, travel to a named noun, or an unclear addressee. The notice board loses its interactable identity in that layer. Confidence is high for the observed reasons and moderate for the exact predicate, because this cycle did not edit or step through `conversational_orchestration.py`.

## Recommended next cycle

**Option A — targeted gameplay repair.**

- Subsystem: conversational orchestration's post-answer decision (`repeat_delivered_statement`, `destination_not_established`, `ungrounded_provider_target`).
- Minimal correction: a new utterance that names a visible interactable, asks to read it, or recalls it, must leave the previous NPC sentence and reach the existing inspection or recall owner. A visible object must not be classified as an unestablished travel destination.
- Regression fixtures: T04, T05, and T09 on this seeded gate, after T03's captain line.
- Negative controls: a genuine repeat of the patrol question may return the same line; travel to a place that is not an exit still declines and does not move; T12's retreat with physical adjudication off stays an operational refusal with no `call_gpt` entry and no pointer advance; hidden facts stay unspoken.
- Authority risks: do not invent a sleeve-writing mechanic for T06; do not move the player onto the board; do not promote the captain's speech into a new authoritative clue beyond the discovery owner that already ran on T03.
- Player-experience change: after one NPC answer, the player can read and recall the notice.

Option B is not the next step. The blocking turns never called the provider. A live model would not be asked to repair T04, T05, T06, or T09.

Option C is not the next step. The existing continuation harness produced twelve classified turns. The missing capability is a repair, not another recorder.

Do not implement the repair in this cycle. Do not open PR-PLAY-80. Do not start AT-OPT-07.
