# 03 — Semantic Authority Inventory

Interpretation proposes meaning. Authorization decides whether that meaning may execute, mutate state, or be shown. Several components currently do both, and a later one can replace an earlier result.

| Component | File and function | Input | Output | Authority claimed | Binding? | Can override earlier? | Mutates state? | Can clarify or refuse? | Provider call? |
|---|---|---|---|---|---|---|---|---|---|
| Live interpretation | `game/live_chat_interpretation.py` `interpret_production_turn` | Player text, scene catalog, last two visible turns, public evidence, ownership context | Recipient, purpose, operations, target ids, unresolved refs, correction | What the utterance is | Proposal, until accepted | Can relabel the player | No | Blocked clarification text | Yes, one, purpose `interpretation` |
| Eligibility | `experiments/pr_do/eligibility.py` `evaluate_eligibility` | Closed enums and ids only | `ELIGIBLE_FOR_VALIDATION` or a block | Whether the record may be offered | Binding for the offer | Yes, blocks the offer | No | Yes | No |
| Social-scope normalization | `live_chat_interpretation.py` `normalize_social_scope` | NPC record with one ASK | Incidental gestures removed; some unresolved refs dropped when they match the subject | Compatibility cleanup | Binding on the record | Yes, deletes refs | No | No | No |
| Communication decision | `game/conversational_orchestration.py` `_communication_decision` | Interpretation record plus public evidence | GM/session/mixed answer, or None so execution continues | Who is being addressed and whether to execute | Binding when it returns | Yes, discards ASK components | No, early return | Yes | No |
| Continuation fast path | `_gm_continuation_decision` | Leading "actually", "never mind", "why" | Correction or withdrawal | Pending-control owner | Binding when it returns | Yes | Clears pending only | Yes | No. Returns None for ordinary lines while live interpretation is on |
| Bridge | `game/player_interpretation_bridge.py` `normalized_action_from_interpretation` | Record plus visible catalog | Normalized action or rejection | Whether the id may be executed | Binding | Rejects unresolved refs and invisible ids | No | Clarification via rejection | No |
| Ordinary contract | `game/ordinary_semantic_ownership.py` `establish_ordinary_gameplay_contract` | Lexical contract plus bridge id | One resolution contract | Addressee and operation | Binding | Yes. A validated ASK id replaces an unresolved lexical person | Writes the contract onto the resolution | Only if it leaves operation unresolved | No, unless interpretation was not yet consumed and the model path is re-entered |
| Lexical person binder | `game/incidental_entity.py` `resolve_proposed_interlocutor` | Nominal such as "one of them" | Unresolved, ambiguous, or incidental binding | Proposed person | Advisory once the bridge id is present | No | No | Can mark unresolved | No |
| Social target selection | `game/interaction_context.py` explicit-target branch | Normalized `target_id` | `target_resolved`, source `explicit_target` | Which NPC speaks | Binding | Yes, if the id is on the roster | Social and discourse state after resolution | No, if the id matches | No |
| Authoritative carry | `carry_authoritative_contract` | Pre-resolver contract plus social result | Compact `authoritative_result`; may restamp the interlocutor | Identity after resolution | Binding | Protects an unresolved explicit person. Does not see one after the bridge overwrite | No extra world facts | Records `authority_conflict` | No |
| Referent tracking | `game/referent_tracking.py` | Already chosen target and visible people | Ambiguity class and risk | Narration grounding | Advisory for prose | Does not select the target | No | Can forbid risky pronouns in narration | No |
| World tick | `game/api.py` `chat` calling `game/world.py` `advance_world_tick` | Any turn that did not return early | Turn counter, time-pressure clock, faction pressure and agenda | That a turn was played | Binding | No semantic judgment | Yes | No | No |
| Narration | `game/gm.py` message builder, `game/api.py` `_bounded_call_gpt` | Bound contract, policy, scene payload | Candidate prose | Wording only | Advisory | Cannot change the contract | No, until a proposal is accepted | No | Yes, `strict_social`, `primary_turn`, or `retry_escalation` |
| Final validation and safe line | `game/immutable_valid_response.py` `safe_nonresolution` | Bound contract and social result | Player-visible fallback | Whether the sentence may be shown | Binding for text | Does not reinterpret the player | No | Replaces invalid prose | No |

## Boundary violations

Eligibility's own comment says `ELIGIBLE_FOR_VALIDATION` is not permission to execute (`execution_authorized` stays false). `chat` treats an accepted bridge as permission. The captured ambiguous turn was eligible, bridge-accepted, and then ticked.

The lexical binder found "one of them" unresolved. The contract constructor had that finding in `pre_bridge_addressee_binding` and then overwrote it. That is interpretation treated as authorization.

`_communication_decision` can answer a turn the eligibility layer blocked. `chat` calls `decision_from_interpretation_record` on a blocked record (`game/api.py` around the live-outcome branch) and returns that answer instead of the blocked clarification text. Validation of a response is being used as a second interpretation of the player.

`ConversationalDecision.__post_init__` forces `EXECUTE` plus `ASK` to owner NPC and leaves purpose at the default `ACTION`. A question that was labeled QUESTION becomes an action by the time it is executable. The speech-act field is not preserved.

Final validation cannot refuse an unauthorized target. By the time it runs, the contract says the target is bound and unambiguous. The safe line then speaks as that NPC. A response check is acting as confirmation of the addressee.

Referent tracking is not a competing selector in the ambiguous-target failure. It reported `single_visible_person_like` and risk 0 after Mara had already been chosen, in a scene that contained only one visible person. It echoed the decision. It did not make it.
