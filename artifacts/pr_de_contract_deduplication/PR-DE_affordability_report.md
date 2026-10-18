# PR-DE Affordability Report

Estimates are `ceil(chars/4)` of the `build_messages` blob. They are not provider token usage and they are not API cost. No price file was used. Monetary cost is blank.

The 10,947-byte S1 hypothesis is the sum of the seven duplicate values. The request also loses the JSON key punctuation, 243 bytes on S1, so the measured request reduction is 11,190 bytes (11.3%). That is the same opportunity, counted at the serialization boundary.

## By class

| Id | Class | Baseline bytes | Revised bytes | Reduction | Percent | Est. tokens saved | Envelope | Projection |
|---|---|---:|---:|---:|---:|---:|---|---|
| S1 | Harmless preference | 98,773 | 87,583 | 11,190 | 11.329 | 2,798 | narration_only | selected |
| S2 | Experiential follow-up | 98,123 | 87,152 | 10,971 | 11.181 | 2,743 | narration_only | selected |
| S3 | Multi-turn continuation | 98,061 | 87,097 | 10,964 | 11.181 | 2,741 | narration_only | selected |
| F1 | Authored factual | 110,114 | 99,163 | 10,951 | 9.945 | 2,737 | narration_only | unselected |
| N1 | Notice board | 106,771 | 96,389 | 10,382 | 9.724 | 2,596 | structured | unselected |
| O1 | Ordinary observation | 103,854 | 93,591 | 10,263 | 9.882 | 2,565 | structured | unselected |
| M1 | Ordinary movement | 104,643 | 94,305 | 10,338 | 9.879 | 2,585 | structured | unselected |
| C1 | Consequential social | 108,362 | 97,373 | 10,989 | 10.141 | 2,747 | narration_only | unselected |
| H1 | Hidden-information question | 107,312 | 96,449 | 10,863 | 10.123 | 2,716 | narration_only | unselected |
| T1 | Scene transition | 113,279 | 103,021 | 10,258 | 9.056 | 2,565 | structured | unselected |
| K1 | Synthetic skill check | 91,621 | 81,959 | 9,662 | 10.546 | 2,416 | structured | unselected |
| B1 | Synthetic combat | 121,416 | 110,769 | 10,647 | 8.769 | 2,662 | structured | unselected |

Removed on every row: the seven JSON-equal top-level contracts. Retained: every `response_policy` child, the `interaction_continuity` snapshot, the decision, the recipe, the scene, and the speaker contract.

C1 stays on the full-context path. Its reduction is the duplicate contracts only.

## Per 100 turns

Hypothetical input-token reduction, `ceil(chars/4)` times 100. Output tokens and retries are not in this number.

| Class | Estimated input tokens saved per 100 turns |
|---|---:|
| S1 | 279,800 |
| C1 | 274,700 |
| F1 | 273,700 |
| H1 | 271,600 |

## Remaining major contributors

On the revised 87,583-byte S1 request:

| Section | Bytes | Share |
|---|---:|---:|
| `response_policy` | 22,698 | 25.9% |
| `instructions` | 13,947 | 15.9% |
| `gm_resolution_decision` | 8,349 | 9.5% |
| `decision_facing_answer_recipe` | 6,707 | 7.7% |
| `referent_tracking` | 4,501 | 5.1% |
| narration-only system prompt | 4,170 | 4.8% |

## Acceptance and live quality

First-attempt acceptance was not measured. No provider call was made, so there is no evidence about whether the model still follows a contract it now sees once. The deterministic validators still see the policy object.

## Next optimization

Trim instruction lines that only name a policy field the payload already contains. Keep the answer-first line, the visibility line, and the hidden-fact line. Do not widen the harmless projector and do not compact the decision or the recipe in that same change.
