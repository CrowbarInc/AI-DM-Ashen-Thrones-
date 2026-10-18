# 03 — Authorization Contract Design

## Boundary

`assess_addressee_grounding` in `game/ordinary_semantic_ownership.py` is the shared addressee decision. These callers read it and do not invent a replacement target:

- `decision_from_interpretation_record` / `_communication_decision`, before any execute fall-through.
- `normalized_action_from_interpretation`, before an ASK is accepted.
- `establish_ordinary_gameplay_contract`, before a bridge id is copied onto the contract.
- `chat`, immediately before `turn_counter` is incremented.

`conversational_authorization_record` stores the disposition. On a resolved turn it lives at `resolution_contract.construction.conversational_authorization`. On an unresolved address it is also attached to the conversational decision (`authorization`), which the non-mutating response already publishes.

## Fields

| Field | Values used |
| --- | --- |
| communication_ownership | `npc_directed`, `gm_directed`, `ambiguous_unresolved` |
| intent_purpose | `address_npc`, `request_information` |
| target_resolution | `explicit`, `contextual`, `ambiguous`, `unresolved`, `none_required` |
| target_provenance | `explicit_canonical`, `unique_contextual`, `established_interlocutor`, `authoritative_world_state`, `provider_candidate_only`, `none` |
| target_id | Canonical id, or null |
| candidate_target_ids | Provider ids that were not authorized |
| operation_eligibility | `executable`, `requires_clarification`, `not_assessed`, `no_consequential_operation` |
| mutation_eligibility | World advancement. False does not forbid conversational bookkeeping |
| authority_provenance | `communication_decision`, `pre_tick_addressee_gate`, or `resolution_contract` |
| conflict_status | `none`, `unresolved`, `resolved_by_explicit_wording` |
| pending_intention_relationship | `starts_new`, `continues`, `requires_clarification` |

Confirmation, correction, and withdrawal reuse `pending_clarification`, `pending_intention`, and `last_executed_intention` on `conversational_context`. Those are saved with the session.

## Target rules

- A provider id alone is not provenance. The bridge rejects an ASK whose grounding is not `executable`.
- Non-unique nominals (`one of them`, `either guard`, `someone`) require clarification whether one or several people are visible. The provider id is stored as a candidate.
- A singular pronoun continues the active social interlocutor, or the single visible person when that person matches.
- A role or name hit resolves to that person. A contradictory provider id is recorded as `resolved_by_explicit_wording` and does not win.
- An extra distinguishing word resolves only when that word appears in that NPC’s own description or in a scene sentence that names them. A shared scene sentence does not.
- Third-person questions (“what did she mean”) are not treated as continuation just because an interlocutor is active. Second-person follow-ups are.
- Movement and “where can I find them” are not speech-act addresses. The speech nominal covers ask, tell, warn, inform, address, speak to, talk to, turn to, and question-to.

## Mutation

The pre-tick gate returns a non-mutating clarification only when the utterance is a direct address and eligibility is `requires_clarification`. Ordinary unmatched narration is not blocked by this gate. Clarification bookkeeping writes `pending_clarification` and `pending_intention` without incrementing the turn counter or calling `advance_world_tick`.
