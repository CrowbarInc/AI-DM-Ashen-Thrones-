# 05 — Ambiguous-Target Root Cause

Player: "I ask one of them what happened."

Historical result, `behavior_1.json` turn 33, fresh production interpretation and narration: Sergeant Mara says she cannot answer from what is settled here. The turn was critical. It was not non-mutating. It used three provider calls.

## Where certainty was introduced

The provider record is the first certainty. Recipient NPC, purpose QUESTION, one ASK, `target_ref` `sergeant_mara`, `unresolved_references` empty, clarification question empty, correction subject NONE. Subject text was "what happened to the people in the courtyard." Nothing in the record says the addressee is plural or unresolved.

Eligibility then returns `ELIGIBLE_FOR_VALIDATION` with `execution_authorized` still false. The reason string is `allowlisted_attempt_awaits_engine_validation`. Empty unresolved refs are why the clarification branch does not run. Replayed today, `decision_from_interpretation_record` returns EXECUTE, proposed target `sergeant_mara`, `requires_authoritative_execution` true. The bridge accepts ASK `sergeant_mara`.

The lexical binder, preserved on the historical contract trace, did the opposite. Before the bridge override: status unresolved, proposed interlocutor "one of them", `explicit_new_interlocutor` true, authority reason `proposal:not_a_person`, bound id null. That is the correct reading of the phrase as a person reference. It is not a canonical name.

`establish_ordinary_gameplay_contract` then copies that binding to `pre_bridge_addressee_binding` and, because the bridge operation is ASK and the target id is set, writes `interlocutor_id=sergeant_mara`, `ambiguous=false`, binding status `bound_canonical`, reason `identity:validated_interpretation_bridge`. The conflict guard in that function only fires when a different interlocutor is already `bound_canonical`. An unresolved explicit person does not count. The later guard in `carry_authoritative_contract` would have kept an unresolved explicit person, but by then the status is already `bound_canonical`, so the guard does not see it.

The social resolver reports `target_source=explicit_target` and `target_reason=normalized target_id matches scene-addressable roster`. It did not choose among people. It confirmed an id. Referent tracking then reported `ambiguity_risk` 0 and `single_visible_person_like`. The historical courtyard contained one visible NPC, Sergeant Mara. Guard Captain and Tavern Runner are in the world at `frontier_gate`, not in the scene. The single-person label is true of the fixture and irrelevant to the selection. Selection had already happened.

Narration ran as `strict_social`, failed hard validation, retried once as `retry_escalation`, and was replaced by the safe line attributed to Mara. `live_resolution_mode` was `grounded_information_request` with `improvisation_opportunity_detected` false and `proposal_reason` `not_improvable_mode`. Speech authority was `none`.

## State change

From the turn-33 snapshot, not from a new live campaign:

| Field | Before | After |
|---|---|---|
| `session.turn_counter` | 0 | 1 |
| `session.clocks.time_pressure` | 0 | 1 |
| House Verevin pressure / agenda | 2 / 0 | 3 / 1 |
| Ash Cowl pressure / agenda | 2 / 0 | 3 / 1 |
| Ordo Pyric pressure / agenda | 1 / 0 | 2 / 1 |

`chat` increments the counter and calls `advance_world_tick` for every turn that did not take an early non-mutating return. The tick steps faction pressure and agenda. A clarification returned from `_nonmutating_conversational_decision_response` never reaches that code. This turn reached it because the ask had been authorized.

## Two-NPC replay of the same captured record

Disposable world: the historical NPC list plus Corporal Bren in `waystation_courtyard`. Visible catalog ids: `corporal_bren`, `sergeant_mara`. No provider call.

- Bridge still accepts ASK `sergeant_mara`.
- The same record with `unresolved_references: ["one of them"]` is rejected, reason `unresolved_references`.
- With live interpretation marked consumed, matching production after an accepted interpretation, the contract binds Mara, `ambiguous` false, while `pre_bridge_addressee_binding` remains unresolved / `proposal:not_a_person`.
- Without that consumed flag, a second contract build abstains and the override does not stick. Production sets the flag before this build. The override is the production path.

## Fresh interpretation with both NPCs present

One call, 1,647 input tokens, 178 output tokens, model `gpt-4.1-mini-2025-04-14`. The model returned recipient GM, purpose QUESTION, ASK target null, unresolved refs empty. Orchestration answered as the GM (`communication_before_execution`). The bridge rejected the component for `missing_target`. This sample would not tick. It also would not ask which person the player meant. It would say the matter has not been established, because GM questions with empty evidence use that sentence.

So the historical certainty was the provider's id, ratified by the bridge override. It is not a stable provider habit, and it is not a uniqueness rule. The engine has no binding representation of "the player refused to choose."

## Who should have stopped execution

The contract constructor is the last component that still had both facts: the lexical result "one of them is unresolved," and the provider id. It had enough information. It permitted execution because a validated visible id is defined to replace an unresolved proposed person unless another person is already bound.

Eligibility and the bridge did not have the lexical finding. They only see `unresolved_references`, which the provider left empty. They could not have detected this ambiguity from their inputs. The information was not lost before them. It was created later by the lexical binder and then deleted by the override.

Final validation did not have the player plurality. It had a bound, unambiguous Mara. It correctly rejected invented facts and incorrectly delivered those facts' replacement in Mara's voice, after the tick.

## Repair boundary, not implemented

The authorization record must be able to say `addressee=ambiguous` even when a model supplied a visible id, whenever the player's own nominal is an explicit non-unique person and more than one person is visible. A single visible person can still be offered as a candidate. It must not be executed silently. `ambiguous` or `unresolved` on a consequential ask sets `mutation_eligible` false, so `chat` returns before the tick. The social resolver does not run. The safe line must not name a speaker the authorization record did not bind.

Do not special-case the sentence "one of them." Do not weaken the rule that an empty unresolved list may still be executed when the player named one visible person.
