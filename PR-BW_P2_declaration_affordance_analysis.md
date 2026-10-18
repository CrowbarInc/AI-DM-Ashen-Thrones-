# PR-BW P2 Declaration Affordance Analysis

## Evidence

Source: `artifacts/pr_bv_turn_operation_projection_micro_live/evidence/P2/`.

Player input:

> Baker, which loaf do you usually keep for yourself?

## Exact Turn Operation

```json
{
  "response_operation": "incidental_dialogue",
  "declaration_expectation": "reply_not_required",
  "semantic_ceiling": "transient_dialogue_not_durable_fact",
  "instruction": "On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. The reply itself belongs in narration. Do not declare that reply as a world fact. Do not establish a durable preference or history merely to answer. Listed claims may still be realized if restated."
}
```

## Exact No-Declaration Guidance

Model-facing signals supporting no declaration:

1. `declaration_expectation`: `reply_not_required`.
2. `semantic_ceiling`: `transient_dialogue_not_durable_fact`.
3. Instruction: "The reply itself belongs in narration."
4. Instruction: "Do not declare that reply as a world fact."
5. Instruction: "Do not establish a durable preference or history merely to answer."
6. `permitted_inference.allowed`: false.
7. `bounded_inference`: "not permitted on this turn".
8. `epistemic_premise`: no player hypothesis, NPC claim, or unresolved premise is authorized.
9. `ordinary_incidental_expression`: refusal, hesitation, mannerism, and phrasing may stay plain narration or bounded incidental improvisation.

## Provider-Visible Declaration Schema

The system prompt still exposes the universal declaration machinery:

```json
"declared_claims": [
  {
    "declaration_id": "string",
    "declaration_mode": "realize|propose",
    "source_claim_id": null | "claim_id_from_gm_resolution_decision",
    "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
    "semantic_identity": {},
    "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
    "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
    "modality": "established|possible|hypothetical|unresolved",
    "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
    "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
    "text": "short internal claim text"
  }
]
```

## Exact Initial Declaration

```json
{
  "declaration_id": "decl_1",
  "declaration_mode": "realize",
  "source_claim_id": null,
  "premise_claim_ids": ["rc_9ab69105465f", "rc_2bb408577206"],
  "semantic_identity": {},
  "provenance_requested": "authored_world_fact",
  "epistemic_status": "established",
  "modality": "established",
  "realization_role": "MUST_STATE",
  "relation_kind": "ordinary_predicate",
  "text": "The baker does not disclose which loaf they keep for themselves."
}
```

Validator result: rejected as `unauthorized_declared_claim`.

## Exact Initial Narration

> The baker glances around cautiously, then shakes their head. "I don't have a particular favorite loaf I keep for myself," they say. "Truth be told, everything I bake is meant for my customers."

## Independent Narration Quality

The narration is playable ordinary NPC dialogue. It answers with a refusal/deflection, uses an allowed speaker, and stays locally social. The only concern is that the line "everything I bake is meant for my customers" could imply a preference/history if treated as durable truth, but spoken as NPC dialogue it is acceptable claim-only/social prose under the contract. Without the invalid declaration, the initial output probably would have been accepted or at least much closer to accepted.

## Why Declaration Was Unnecessary

The decision already authorized the baker's existence and visible bread-stall fact. The turn request required a transient reply, not a durable world update about the baker's private preference or disclosure policy. The model already placed the reply in narration. Declaring the reply as `authored_world_fact` added no player-facing value and created the failure.

## Likely Schema Pressures

Ranked by salience:

1. Universal schema exposes `declared_claims` first and every turn.
2. `realize` is the first declaration mode and sounds like the ordinary/default act.
3. `authored_world_fact`, `established`, and `MUST_STATE` are present as attractive vocabulary.
4. The declaration field is structurally present in the example, while `declared_claims: []` is not positively demonstrated in the system prompt.
5. The structured claim rule says every consequential proposition intended for narration must appear in declarations, creating a possible over-cautious tendency to declare dialogue content.
6. Required content includes two existing world-truth claims; the model may treat premise linkage as license to realize a new statement about the reply.

## Empty-Declaration Affordance

Empty declarations are allowed and can succeed. Evidence:

| Gate | Probe/attempt | Result |
| --- | --- | --- |
| PR-BV | P1 retry | `declared_claims: []`, accepted |
| PR-BV | P2 retry | `declared_claims: []`, accepted |
| PR-BV | P3 initial | `declared_claims: []`, accepted |
| repaired pre-PR-BV | P1 retry | `declared_claims: []`, accepted |
| repaired pre-PR-BV | P2 retry | `declared_claims: []`, accepted |
| PR-BS | P2 initial | `declared_claims: []`, accepted |

But the provider-visible schema does not make empty declarations visually normal in the main example. The empty case is learned mainly from retry feedback or historical behavior, not from a prominent schema affordance.

## Retry Comparison

Initial: declaration manufactured an authored established fact; narration was playable but rejection happened before narration validation.

Retry: declaration removed (`declared_claims: []`); narration remained ordinary refusal/dialogue and was accepted. Player-facing content improved stylistically but did not need a new semantic discovery. The retry mainly succeeded by removing structured authorship.

Retry input cost: 26,142 input tokens for P2 alone.

## Counterfactual No-Declaration Envelope

If P2's model-facing schema had no consequential declaration capability, the already-generated initial narration probably would have been a valid/playable response. This is a high-confidence schema-exposure signal.

## Salvageability

S1 - structurally salvageable. Player-facing content was good enough; removing/avoiding the structured declaration would likely have sufficed.
