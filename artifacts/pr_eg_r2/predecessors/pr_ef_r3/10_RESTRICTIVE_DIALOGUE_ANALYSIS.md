# 10 — Restrictive Dialogue Analysis

The stock sentence is produced by `safe_nonresolution` in `game/immutable_valid_response.py`. When the operation is ask, the social result resolved a target, and that target equals the contract interlocutor, the line is `{Name} says, "I cannot answer that from what is settled here."` The historical ambiguous turn and conversation turns 3, 5, and 10 all took this branch after narration failed validation.

The social resolver had already chosen `reply_plan_kind=genuine_uncertainty`, `npc_speech_authority=none`, and `objective_world_fact_authority=none`. `live_resolution_mode` was `grounded_information_request`, with `improvisation_opportunity_detected` false and `proposal_reason` `not_improvable_mode`. Bounded improvisation is implemented and is opened for other modes. This mode does not open it.

The narration prompt tells the model that mundane NPC talk may be bounded incidental realization and that unsupported durable facts need structured lanes. Validation then rejects durable-looking inventions. The retry tells the model to keep the same contract. The model has no legal specific answer, so the safe line replaces both drafts.

## Classification of the observed lines

| Utterance | Class | Why |
|---|---|---|
| Mara cannot say who owns the lantern, or who forged it, when no such fact is authored | A and B. Correct refusal to invent a canonical owner or maker. | No topic, speech authority none. |
| "I ask Mara what troubles her" and "describe the courtyard" also receive the same sentence | C and D. The visible scene already says she looks concerned and describes the courtyard. A partial, source-limited answer was available. The fallback replaced it. | The safe line does not consult visible facts once a speaker is bound. |
| The player hears the same sentence on unrelated topics | D. Generic fallback. | One template for every unknown ask. |
| A natural aside that is not a new fact | E. Missing capability. | Grounded-information mode never creates an incidental proposal, and incidental text is not distinguished from a proposed world fact at emission time. |

## Does the architecture distinguish the kinds of fact?

The pieces exist and are not connected for ordinary NPC answers.

- Canonical world facts live on clues, topics, and world state. The north-road topic is one of these. Turn 7 spoke it without a narration call.
- Player-visible established facts live in public evidence and revealed topics. GM answers concatenate them.
- NPC knowledge is the topic list and speech-authority code. `none` means silence.
- Noncanonical descriptive detail is mentioned in the system prompt and in bounded-improvisation proposals. The social path under test does not emit it without persisting it.
- Proposed new facts are improvisation proposals. They are not created for `grounded_information_request`.
- Consequential changes are resolver results and the world tick. The safe line does not itself change factions. The tick already ran because the ask was authorized.

The missing connection is an emission rule: an NPC may add a non-persisted, non-consequential detail, or may point at a visible fact, without that detail becoming a clue, a topic, or a faction change. The current rule collapses "not in the topic list" into "no sentence except the template." That is why ordinary talk sounds like a policy refusal.

This cycle does not recommend letting NPCs invent owners, orders, routes, or causes. It also does not recommend writing a fact for every possible question. The existing authored-topic path and the existing improvisation proposal type are the two boundaries. The social emission path needs to use them, or to skip the model when neither applies. That use belongs with the authorization record: if the record says "no canonical answer, incidental color allowed, nothing persisted," validation can accept color and reject canon. Today it only has "none," and the model call is wasted.
