# 06 — Remaining Holdout Failures

All three are from `behavior_1.json`, fresh production, and were replayed through current `decision_from_interpretation_record` and the bridge. None of them ticked the world. Each wrote a GM conversational-context record. That is session bookkeeping, not faction or clock advancement.

## Case B — "I ask the sergeant who owns the lantern."

Earliest incorrect decision: the provider set recipient GM and purpose QUESTION, and also emitted ASK `sergeant_mara` with empty unresolved refs. The prompt says speaking to an NPC is recipient NPC, and it says not to convert GM communication into ASK. The model did both.

Eligibility still says the ASK is eligible. `_communication_decision` runs first. Owner GM and purpose QUESTION do not become MIXED unless the component is MOVE, ATTACK, USE, FOLLOW, or there is more than one ASK. A single ASK is discarded. The answer is the empty-evidence sentence: "That has not been established in the information available to you." One interpretation call. No narration. `nonmutating` true.

Later chances to correct it: the bridge would have accepted Mara if orchestration had not returned. It was never consulted for an answer, though a replay today shows the bridge would accept the id. Final validation did not run.

Player-facing consequence: a direct question to the sergeant became a GM refusal about world facts. The sergeant was not asked. No social state was updated.

Smallest repair boundary: when the utterance is an explicit address and the record also contains one ASK to a visible NPC, recipient GM must not silently win. Record an owner conflict and either execute the ask or ask which was intended. Do not answer from empty evidence.

## Case C — "What does she mean by the road?"

The provider set recipient GM, purpose EXPLANATION, legacy mode CLARIFICATION, ASK `sergeant_mara`, and evidence `npc_latest_reply` plus `npc:sergeant_mara:street`. The clarification question it also wrote, asking what "the road" refers to, was not shown.

Eligibility blocks legacy mode CLARIFICATION. `chat` then ignores the blocked sentence and calls the communication decision. Purpose EXPLANATION with public evidence joins the evidence strings and, because none of the refs start with `cause:`, appends "That establishes the observation or result; its cause has not been established." That suffix is deterministic. It is not a second narrator. The shown text is Mara's earlier line, repeated, plus the street fact, plus that suffix.

The same join explains turn 6 of the preserved eleven-turn conversation. The player said "GM, can you clarify what Mara just said?" The record was GM/CLARIFICATION with `npc_latest_reply`. Status was blocked. The shown text is Mara's previous inability line. No suffix, because the purpose was CLARIFICATION rather than EXPLANATION. Explicit GM address still came out as NPC dialogue, because the answer is the stored NPC sentence.

So the defect is not a missing interlocutor id. The GM answer path has no "explain this utterance" result. It concatenates passages. The prompt also tells the model that questions about what an NPC meant are GM questions, while the R2 holdout expected NPC. Those two expectations disagree. The player-facing failure remains even if GM ownership is accepted: the response does not say what she meant. It restates her and then denies a cause the player did not ask for.

State: non-mutating. One interpretation call.

Smallest repair boundary: a GM explanation must answer the asked relation, or say that the words' meaning is not in the stored passage. It must not append the cause template unless the player asked why. Quoting the NPC inside a GM answer has to stay marked as quotation, which the current join does not distinguish from a new speech act. Whether "what does she mean" should instead reopen the NPC channel is a product choice. The concatenation bug does not depend on that choice.

## Case D — "Instead, make that a question about the lamp."

The snapshot's conversational context before this turn was null. There was no `pending_clarification` to revise. The provider set correction subject NONE, recipient GM, purpose CLARIFICATION, evidence `visible:0`, and an ASK aimed at `courtyard_lantern`. Legacy mode was CLARIFICATION, so eligibility blocked. The communication decision then saw CLARIFICATION plus public evidence plus status INTERPRETED and joined the evidence. The player saw "A soot-streaked lantern burns beside the courtyard gate."

Why each suspected cause does or does not fit:

- No structured pending intention: true. Ordinary questions do not leave a revisable intention. The only rewrite path requires `pending_clarification.kind == compound_sequence` and a single new component.
- Context invalidated too early: the context was already absent at the start of the turn. This cycle did not find a deletion inside the turn.
- Interpreter missed correction semantics: true for this sample. A fresh probe of the same sentence today returned purpose CORRECTION, subject REFERENT, and no components. Provider behavior is not stable.
- Normalization removed the correction: no. The stored correction is NONE because the model wrote NONE.
- Continuation handler did not run: true. `_gm_continuation_decision` only matches a leading "actually" or a withdrawal pattern, and it returns None for other lines while live interpretation is enabled.
- Another route took precedence: true. The evidence-join answer replaced both the blocked clarification text and any correction.

The fresh CORRECTION label would still not ask the lamp question. Purpose CORRECTION with no compound pending returns the canned "I've set aside the unexecuted intention" line. That is a withdrawal announcement, not a revised ask. Both labels fail the player's request. They fail in different words.

State: non-mutating. One interpretation call.

Smallest repair boundary: a correction needs a pending intention object that exists for an unexecuted ask, not only for a compound proposal. The handler should rewrite that intention or ask what to revise. It should not describe a visible object as the answer, and the canned set-aside line should not be the only successful correction.

## Shared versus independent

B and D share the GM evidence answer and the rule that a blocked interpretation is re-decided. C shares that rule and adds the cause suffix, which is local to purpose EXPLANATION. B additionally shares the recipient-versus-ASK conflict with the ambiguous-target case, in the opposite direction: there, an NPC label plus an id became execution; here, a GM label discarded a usable id. The independent local defect is the cause-template sentence. The shared defect is that recipient, purpose, unresolved refs, and the lexical addressee are not one authorization record.
