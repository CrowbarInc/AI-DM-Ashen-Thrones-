# PR-BW P1 Declaration/Narration Semantic Delta

## Evidence

Source: `artifacts/pr_bv_turn_operation_projection_micro_live/evidence/P1/raw_generation_attempt_1.json` and `validation.json`.

Player input:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Turn operation:

`bounded_interpretation`, `optional_bounded_inference`, `interpret_observations_not_unauthorized_cause`.

## Exact Declaration

```json
{
  "declaration_id": "rc_infer_damage_nature",
  "declaration_mode": "propose",
  "source_claim_id": null,
  "premise_claim_ids": ["rc_db5ec0aa65c3", "rc_b31ecb1fd1c7"],
  "semantic_identity": {},
  "provenance_requested": "gm_inference",
  "epistemic_status": "inferred",
  "modality": "possible",
  "realization_role": "MAY_STATE",
  "relation_kind": "epistemic_status",
  "text": "The split wooden yoke and torn leather hanger could indicate strain or wear on the bell's supports."
}
```

Declaration validation: hard valid. Accepted as `accepted_bounded_declared_inference`.

## Exact Narration

> The bell's wooden yoke is split, and its leather hanger is torn. This damage could suggest that the bell has been subjected to strain or wear on its supports over time.

Narration validation: hard invalid. Violation reason: `unsupported_narrator_lead`.

## Atomic Propositions

Declaration:

1. The wooden yoke is split. Premise, authorized world truth.
2. The leather hanger is torn. Premise, authorized world truth.
3. The combined damage could indicate strain or wear on the bell's supports. Proposed bounded inference, possible/inferred.

Narration:

1. The wooden yoke is split. N1 direct verbalization.
2. The leather hanger is torn. N1 direct verbalization.
3. The damage could suggest strain or wear on the supports. N1 direct verbalization of the accepted declaration.
4. The strain or wear occurred "over time." N3 new consequential/epistemic content.

## N1/N2/N3 Classification

| Narration proposition | Class | Authority status |
| --- | --- | --- |
| Bell's wooden yoke is split | N1 | Authorized realization claim |
| Bell's leather hanger is torn | N1 | Authorized realization claim |
| Damage could suggest strain or wear on supports | N1 | Matches accepted bounded inference |
| Strain/wear happened over time | N3 | Unsupported temporal/history implication |

`over time` is N3. It adds duration/history. The GMResolutionDecision explicitly says qualified possibilities may be inferred from observations, but no cause, actor, or history is established.

## Semantic Delta

```json
{
  "declaration_semantics": {
    "premises": [
      "wooden yoke split",
      "leather hanger torn"
    ],
    "inference": "damage could indicate strain or wear on supports",
    "modality": "possible",
    "history_or_duration": "not selected"
  },
  "narration_semantics": {
    "premises": [
      "wooden yoke split",
      "leather hanger torn"
    ],
    "inference": "damage could suggest strain or wear on supports",
    "modality": "possible",
    "history_or_duration": "over time"
  },
  "added_meaning": [
    "temporal implication",
    "history/duration",
    "mechanism-shaped persistence of strain or wear"
  ]
}
```

## Counterfactual

If narration had preserved the declaration ceiling, the initial response probably would have been valid and playable. A version ending at "could indicate strain or wear on the bell's supports" would have retained the useful answer while avoiding unsupported history/duration. No second full generation should have been needed for the semantic core.

## Salvageability

S2 - narratively salvageable. The structured semantic choice was good; narration added a small but consequential semantic expansion.

## P1 Confound

The known direct-question classification debt does not materially erase this defect. Even if request classification were perfect, the declaration-to-narration drift would remain real: the model selected an acceptable declaration and then exceeded it in prose.
