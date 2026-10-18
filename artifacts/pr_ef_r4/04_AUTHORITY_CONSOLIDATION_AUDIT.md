# 04 — Authority Consolidation Audit

## Previous owners

PR-EF-R3 traced independent decisions in the lexical addressee binder, the interpretation record, `establish_ordinary_gameplay_contract` (which copied a bridge id over an unresolved explicit person), the communication-decision recipient, the social resolver’s `target_source`, and the final safe line’s speaker choice. The world tick ran before the contract existed.

## Consolidated owner

Addressee eligibility is `assess_addressee_grounding`. The contract constructor and the pre-tick gate both refuse to execute when that function says clarification is required. Later stages read `conversational_authorization` or the decision that carries it.

## Overrides constrained

- Bridge ASK no longer clears an unresolved explicit person by writing `ambiguous=false` and `identity:validated_interpretation_bridge`.
- A lexical `not_a_person` result does not veto a name the world uniquely grounds. “I ask Mara” still binds Mara.
- A GM recipient plus one direct ASK is reclassified to the NPC only when grounding says the address is executable. Otherwise a third-person question stays with the GM.
- `not_assessed` ASK ids are rejected as `ungrounded_provider_target` unless the player confirmed a pending candidate (`confirmed_pending_addressee`).
- The safe line does not speak as an NPC when authorization says mutation is false and the target is ambiguous or unresolved.
- A non-`INTERPRETED` record still returns before addressee grounding. That is why one live holdout showed the provider’s clarification question for “one of them” instead of the authorization template. The turn still did not execute or tick.

## Boundaries left in place

Social, exploration, movement, combat, time, and faction resolvers still decide outcomes. `select_ordinary_resolver` was not replaced. Authorization means the operation may be attempted. Compound-intent confirmation from PR-EC is still the owner of “ask, then leave” and “if so, I go through.”
