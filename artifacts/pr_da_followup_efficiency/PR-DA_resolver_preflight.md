# PR-DA Resolver Preflight

The follow-up was submitted through the chat route with the provider call aborted before the network.

Player: Does the rain make it harder to keep watch?

Selected resolver: `social`.

Operation: `ask`.

Authoritative interlocutor id, projected as `resolution_contract.interlocutor`: `guard_captain`.

The provider payload does not carry a separate `interlocutor_id` key. `resolution_contract.py` copies `contract.interlocutor_id` into that `interlocutor` field.

interaction_obligation.interlocutor_id: `None`.

interaction_obligation.resolution_mode: `clarification_target_failure`.

active_interlocutor payload: `null`.

social.npc_id: `None`. social.target_resolved: `False`.

Speaker selection: `{"primary_speaker_id": null, "allowed_speaker_ids": [], "authoritative_reason": "no addressable target resolved"}`.

Scene payload id: `None`. Session scene remains frontier_gate in the reconstructed state.

Response envelope: `narration_only`.

Authorized answer scope:

```json
{
  "permitted_state_mutations": [],
  "objective_world_fact_authority": null,
  "npc_speech_authority": null,
  "reply_plan_kind": null,
  "incidental_subjective_allowed": null,
  "durable_state_mutation_allowed": null,
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "incidental_dialogue",
    "declaration_expectation": "reply_not_required",
    "semantic_ceiling": "transient_dialogue_not_durable_fact",
    "instruction": "On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. The reply itself belongs in narration. Do not declare that reply as a world fact. Do not establish a durable preference or history merely to answer. Listed claims may still be realized if restated."
  }
}
```

The provider call was aborted inside `responses.create` before any network request. TestClient then raised `CancelledError` while shutting down that aborted request. Resolution had already been captured. No billable preflight was made.

The isolated session was restored from the reconstructed backup after this preflight, because the chat route advances the world tick before narration.
