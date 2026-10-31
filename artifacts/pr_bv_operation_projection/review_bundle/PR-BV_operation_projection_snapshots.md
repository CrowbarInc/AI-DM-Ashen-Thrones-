# PR-BV — Operation projection snapshots

MODE: DETERMINISTIC. MODEL/API CALLS: ZERO.

These excerpts are the model-facing recipe fields that select the turn's response. Claim lists are omitted here; they are unchanged and still travel in `required_content`.

## 1. P1 — bounded interpretation

Model-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.

```json
{
  "projection_only": true,
  "authority_owner": "gm_resolution_decision",
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "bounded_interpretation",
    "declaration_expectation": "optional_bounded_inference",
    "semantic_ceiling": "interpret_observations_not_unauthorized_cause",
    "instruction": "Interpret what the listed observations may indicate. Do not explain an unauthorized cause, actor, time, or history. A bounded inference may be proposed as gm_inference, inferred, possible, or left in narration. Do not declare a new world fact merely to answer."
  },
  "answer_strategy": "Answer the interpretation with one qualified possibility grounded in the required observations. Use could, may, or might, and keep the wording tied to those observations. Do not explain an unauthorized cause, actor, time, or history.",
  "declaration_guidance": {
    "consequential_authorized_claim": "realize with source_claim_id and the claim provenance",
    "bounded_inference": "propose only; provenance gm_inference; epistemic_status inferred; modality possible; relation_kind epistemic_status. Not authored_world_fact.",
    "epistemic_premise": "No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.",
    "ordinary_incidental_expression": "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."
  },
  "incidental_improvisation_guidance": "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."
}
```

## 2. P2 — incidental dialogue

Model-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.

```json
{
  "projection_only": true,
  "authority_owner": "gm_resolution_decision",
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "incidental_dialogue",
    "declaration_expectation": "reply_not_required",
    "semantic_ceiling": "transient_dialogue_not_durable_fact",
    "instruction": "On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. The reply itself belongs in narration. Do not declare that reply as a world fact. Do not establish a durable preference or history merely to answer. Listed claims may still be realized if restated."
  },
  "answer_strategy": "Have baker reply in ordinary dialogue: a direct answer, a refusal, a hesitation, or an admission that they do not know.",
  "declaration_guidance": {
    "consequential_authorized_claim": "Listed claims may be realized with source_claim_id and their provenance. The turn-local reply is narration, not a new authored world fact.",
    "bounded_inference": "not permitted on this turn",
    "epistemic_premise": "No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.",
    "ordinary_incidental_expression": "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth."
  },
  "incidental_improvisation_guidance": "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth."
}
```

## 3. P3 — player-hypothesis discussion

Model-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.

```json
{
  "projection_only": true,
  "authority_owner": "gm_resolution_decision",
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "player_hypothesis_discussion",
    "declaration_expectation": "hypothesis_discussion_not_required",
    "semantic_ceiling": "conditional_hypothesis_not_established",
    "instruction": "Discuss whether the player's hypothesis fits the listed observations, conditionally. Do not establish the hypothesis, an actor, a motive, a tool, or timing. No declaration is needed merely to discuss it. Realize only claims already listed."
  },
  "answer_strategy": "Realize the listed claims. Discuss the player's hypothesis conditionally. Do not establish it.",
  "declaration_guidance": {
    "consequential_authorized_claim": "realize with source_claim_id and the claim provenance",
    "bounded_inference": "not permitted on this turn",
    "epistemic_premise": "A player hypothesis on this turn may be discussed conditionally. It is not an authorized claim and it is not world truth.",
    "ordinary_incidental_expression": "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."
  },
  "incidental_improvisation_guidance": "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."
}
```

## 4. Consequential realization control

Model-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.

```json
{
  "projection_only": true,
  "authority_owner": "gm_resolution_decision",
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "consequential_realization",
    "declaration_expectation": "required_for_authorized_realization",
    "semantic_ceiling": "authorized_consequential_state_only",
    "instruction": "Realize the consequential state this decision authorizes. Declare those authorized claims with source_claim_id and their provenance. Do not add a further cause, actor, or history."
  },
  "answer_strategy": "Realize the authorized consequential claims and declare them with source_claim_id and their provenance.",
  "declaration_guidance": {
    "consequential_authorized_claim": "realize the authorized consequential claims with source_claim_id and the claim provenance",
    "bounded_inference": "not permitted on this turn",
    "epistemic_premise": "No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.",
    "ordinary_incidental_expression": "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth."
  },
  "incidental_improvisation_guidance": "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth."
}
```

## 5. Ordinary NPC generalization control

Model-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.

```json
{
  "projection_only": true,
  "authority_owner": "gm_resolution_decision",
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "incidental_dialogue",
    "declaration_expectation": "reply_not_required",
    "semantic_ceiling": "transient_dialogue_not_durable_fact",
    "instruction": "On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. The reply itself belongs in narration. Do not declare that reply as a world fact. Do not establish a durable preference or history merely to answer. Listed claims may still be realized if restated."
  },
  "answer_strategy": "Have miller reply in ordinary dialogue: a direct answer, a refusal, a hesitation, or an admission that they do not know.",
  "declaration_guidance": {
    "consequential_authorized_claim": "Listed claims may be realized with source_claim_id and their provenance. The turn-local reply is narration, not a new authored world fact.",
    "bounded_inference": "not permitted on this turn",
    "epistemic_premise": "No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.",
    "ordinary_incidental_expression": "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth."
  },
  "incidental_improvisation_guidance": "Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth."
}
```

## 6. Bounded-interpretation generalization control

Model-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.

```json
{
  "projection_only": true,
  "authority_owner": "gm_resolution_decision",
  "turn_operation": {
    "projection_only": true,
    "authority_owner": "gm_resolution_decision",
    "response_operation": "bounded_interpretation",
    "declaration_expectation": "optional_bounded_inference",
    "semantic_ceiling": "interpret_observations_not_unauthorized_cause",
    "instruction": "Interpret what the listed observations may indicate. Do not explain an unauthorized cause, actor, time, or history. A bounded inference may be proposed as gm_inference, inferred, possible, or left in narration. Do not declare a new world fact merely to answer."
  },
  "answer_strategy": "Answer the interpretation with one qualified possibility grounded in the required observations. Use could, may, or might, and keep the wording tied to those observations. Do not explain an unauthorized cause, actor, time, or history.",
  "declaration_guidance": {
    "consequential_authorized_claim": "realize with source_claim_id and the claim provenance",
    "bounded_inference": "propose only; provenance gm_inference; epistemic_status inferred; modality possible; relation_kind epistemic_status. Not authored_world_fact.",
    "epistemic_premise": "No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.",
    "ordinary_incidental_expression": "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."
  },
  "incidental_improvisation_guidance": "Harmless sensory detail and mannerism may stay plain narration. They are not consequential claims."
}
```
