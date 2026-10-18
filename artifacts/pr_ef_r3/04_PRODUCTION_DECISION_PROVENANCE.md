# 04 — Production Decision Provenance

The live path in `game/api.py` `chat` is the production graph. Early returns never reach the world tick.

1. Load campaign, character, session, world, scene, and log. Reset the live-interpretation consumed flag.
2. Resolve UI communication mode. An OOC or mode conflict returns without a tick.
3. If no stored interpretation and this is not a campaign-start turn, try `deterministic_conversational_decision`. While live interpretation is enabled, ordinary sentences fall through. Only a narrow withdrawal or a "why" after a refusal returns here.
4. Otherwise call `interpret_production_turn`. One provider call. The schema asks for recipient and purpose before operations. The prompt tells the model that speaking to an NPC is NPC, that "what did they mean" is GM, and that AMBIGUOUS is for a demonstrative with no unique referent. Plural "one of them" is not named.
5. If the outcome is blocked, `decision_from_interpretation_record` still runs on the record. A non-EXECUTE decision returns immediately. The blocked clarification sentence is discarded. This is how cases C and D become GM answers.
6. If the outcome is accepted, or the blocked record is reclassified as EXECUTE, the bridge builds a normalized action. Rejection returns a non-mutating clarification.
7. The turn counter increments, `advance_world_tick` runs, and the time-pressure clock advances. This is before narration.
8. `establish_ordinary_gameplay_contract` builds the resolution contract. Because interpretation is already marked consumed, the fast-path rebuild does not run. A bridge ASK id overwrites an unresolved lexical addressee.
9. The selected resolver runs. For a bound ask, social resolution treats the normalized id as `explicit_target` when it is on the scene roster.
10. Narration is conditional. An authored social fact or a deterministic move can skip the provider. A knowledge-gap social turn calls `strict_social`. A failed validation calls `retry_escalation` once, with the same contract.
11. Final validation accepts the narration, or `safe_nonresolution` replaces it. The replacement uses the bound NPC name. The tick is not rolled back.

## What each stage keeps, drops, and can reverse

| Stage | Enters | Leaves | Discarded | Becomes authoritative | Later reversal? | Reinterprets player text? | Mutates? | Another provider call? |
|---|---|---|---|---|---|---|---|---|
| Interpretation | Raw text, catalog, two turns, public evidence | Structured record | Wording that does not fit the schema | Nothing yet | Yes | Yes, that is its job | No | This is the call |
| Eligibility | Enums and ids | Offer or block | Model sentences, by design | Offer status | The blocked-record branch can ignore the block text | No | No | No |
| Communication decision | Record | Answer, clarify, or None | ASK components when recipient is GM and the purpose is a question | Owner and the answer | No, it returns | Yes. It answers from evidence instead of the ask | No | No |
| Bridge | Record and catalog | Id or rejection | Unresolved refs only by rejecting the whole record | Target id, if accepted | The contract can still conflict with a previously bound person | No | No | No |
| Ordinary contract | Lexical binding plus bridge id | One contract | The unresolved lexical person, when a bridge id exists and no prior bound person conflicts | Addressee, operation, `ambiguous=false` | Social carry can record a conflict only if the binding is still unresolved | No new reading of the sentence | Contract metadata | Only if interpretation was not consumed |
| Social resolver | Contract and normalized id | Speaker, topic, reply kind, knowledge authority | The original plural | Speaker and whether a fact was selected | Validation can reject prose, not the speaker | Roster match only | Social, discourse, NPC runtime | No |
| Tick | The fact that the turn did not return | Counters and faction step | Nothing semantic | That a turn occurred | No | No | Yes | No |
| Narration | Bound payload | Candidate sentences | Not applicable | Nothing | Validation | It can invent wording | No | Yes |
| Final validation | Candidate plus contract | Shown text or the safe line | Invalid sentences | The shown sentence | No | No | No | The retry is the extra call |

## Repeated questions

Who is addressed is answered by the provider, again by the lexical binder, again by the bridge, again by the contract override, again by the social resolver, and again described by referent tracking. The lexical answer and the bridge answer are competing sources. The social resolver and referent tracking are cross-checks of an id that has already been authorized. They are not independent readings of "one of them."

Whether the player is talking to the GM is answered by the provider's recipient and again by `_communication_decision`, which can discard an ASK the provider also emitted. Those two fields are competing.

Whether the turn may change the world is answered by eligibility (`execution_authorized: false` even when eligible), then by the bridge (`accepted: true`), then by `chat` (tick). The tick does not see addressee ambiguity.

Whether the reply is valid is answered by narration validation. It consumes the bound speaker. It does not reopen the player sentence.
