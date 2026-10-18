# 08 — Semantic Holdout Results

Both original frozen 12 and independent 12 expressions are unchanged. Independent expressions froze before production edits. Metric A: strict label agreement. Metric B: reviewed player-facing behavior. Routing-only assertions are NOT behavioral correctness.

## holdouts_1.json

Fresh isolated provider after first repair, before later refinements

| Set | Raw strict | Normalized strict | Routing | Reviewed behavior | Critical observed |
|---|---:|---:|---:|---:|---:|
| frozen | 7/12 | 7/12 | 12/12 | 10/12 | 0 |
| independent | 7/12 | 7/12 | 8/12 | 8/12 | 0 |

| Expression | Expected | Raw / normalized | Behavioral | Impact |
|---|---|---|---|---|
| Could you paint a picture of this place? | GM | GM / GM | PASS | agreement, correct behavior.  |
| What does her worried expression tell me? | GM | GM / GM | PASS | agreement, correct behavior.  |
| I ask Mara what troubles her. | NPC | NPC / NPC | FAIL | D: correct label, incorrect downstream behavior. Social resolver binds Mara, but final emission says the person cannot be identified. |
| I make for the courtyard gate. | CHARACTER | SESSION / SESSION | PASS | A: incorrect label, correct behavior.  |
| Would a check be needed for that? | SESSION | SESSION / SESSION | PASS | agreement, correct behavior.  |
| Actually, use the lantern instead. | CORRECTION | ACTION / ACTION | PASS | A: incorrect label, correct behavior.  |
| All right, proceed. | CONFIRMATION | ACTION / ACTION | PASS | A: incorrect label, correct behavior.  |
| Forget that plan. | WITHDRAWAL | WITHDRAWAL / WITHDRAWAL | PASS | agreement, correct behavior.  |
| That one over there. | AMBIGUOUS | GM / GM | PASS | A: incorrect label, correct behavior.  |
| Is it safe to go outside? If so, I head out. | MIXED | GM / GM | PASS | A: incorrect label, correct behavior.  |
| I tell the sergeant to describe the courtyard. | NPC | NPC / NPC | FAIL | D: correct label, incorrect downstream behavior. NPC ownership is retained in resolution, but generic no-one prose does not deliver NPC communication. |
| Could I travel through the gate? | GM | GM / GM | PASS | agreement, correct behavior.  |
| Describe the light around us. | GM | GM / GM | PASS | agreement, correct behavior.  |
| Is Mara visibly uneasy, or merely watching? | GM | GM / GM | PASS | agreement, correct behavior.  |
| I turn to Mara and ask about the north road. | NPC | NPC / NPC | FAIL | D: correct label, incorrect downstream behavior. Unsupported ancillary SOCIAL_SIGNAL and unresolved dialogue topic block a supported ASK. |
| I cross through the courtyard gate. | CHARACTER | SESSION / SESSION | FAIL | B: incorrect label, inappropriate response.  |
| How do you decide whether I need to roll? | SESSION | GM / GM | PASS | A: incorrect label, correct behavior.  |
| Please continue with the proposed first step. | CONFIRMATION | CONFIRMATION / CONFIRMATION | PASS | agreement, correct behavior.  |
| Revise my earlier intention to examine the lamp. | CORRECTION | CORRECTION / CORRECTION | PASS | agreement, correct behavior.  |
| Drop my outstanding request. | WITHDRAWAL | WITHDRAWAL / WITHDRAWAL | PASS | agreement, correct behavior.  |
| The nearer of those. | AMBIGUOUS | GM / GM | PASS | A: incorrect label, correct behavior.  |
| Once we know the way is clear, I will leave through the gate. | MIXED | SESSION / SESSION | FAIL | B: incorrect label, inappropriate response.  |
| Describe her posture; then I ask Mara about the road. | MIXED | GM / GM | FAIL | B: incorrect label, inappropriate response.  |
| What was the reason for the discovery? | GM | GM / GM | PASS | agreement, correct behavior.  |

## holdouts_3.json

Final-code replay of the same outputs; NOT fresh final-prompt holdouts

| Set | Raw strict | Normalized strict | Routing | Reviewed behavior | Critical observed |
|---|---:|---:|---:|---:|---:|
| frozen | 7/12 | 8/12 | 12/12 | 10/12 | 0 |
| independent | 7/12 | 9/12 | 11/12 | 11/12 | 0 |

| Expression | Expected | Raw / normalized | Behavioral | Impact |
|---|---|---|---|---|
| Could you paint a picture of this place? | GM | GM / GM | PASS | agreement, correct behavior.  |
| What does her worried expression tell me? | GM | GM / GM | PASS | agreement, correct behavior.  |
| I ask Mara what troubles her. | NPC | NPC / NPC | FAIL | D: correct label, incorrect downstream behavior. Social resolver binds Mara, but final emission says the person cannot be identified. |
| I make for the courtyard gate. | CHARACTER | SESSION / CHARACTER | PASS | A: incorrect label, correct behavior.  |
| Would a check be needed for that? | SESSION | SESSION / SESSION | PASS | agreement, correct behavior.  |
| Actually, use the lantern instead. | CORRECTION | ACTION / ACTION | PASS | A: incorrect label, correct behavior.  |
| All right, proceed. | CONFIRMATION | ACTION / ACTION | PASS | A: incorrect label, correct behavior.  |
| Forget that plan. | WITHDRAWAL | WITHDRAWAL / WITHDRAWAL | PASS | agreement, correct behavior.  |
| That one over there. | AMBIGUOUS | GM / GM | PASS | A: incorrect label, correct behavior.  |
| Is it safe to go outside? If so, I head out. | MIXED | GM / GM | PASS | A: incorrect label, correct behavior.  |
| I tell the sergeant to describe the courtyard. | NPC | NPC / NPC | FAIL | D: correct label, incorrect downstream behavior. NPC ownership is retained in resolution, but generic no-one prose does not deliver NPC communication. |
| Could I travel through the gate? | GM | GM / GM | PASS | agreement, correct behavior.  |
| Describe the light around us. | GM | GM / GM | PASS | agreement, correct behavior.  |
| Is Mara visibly uneasy, or merely watching? | GM | GM / GM | PASS | agreement, correct behavior.  |
| I turn to Mara and ask about the north road. | NPC | NPC / NPC | FAIL | D: correct label, incorrect downstream behavior. Unsupported ancillary SOCIAL_SIGNAL and unresolved dialogue topic block a supported ASK. |
| I cross through the courtyard gate. | CHARACTER | SESSION / CHARACTER | PASS | A: incorrect label, correct behavior.  |
| How do you decide whether I need to roll? | SESSION | GM / GM | PASS | A: incorrect label, correct behavior.  |
| Please continue with the proposed first step. | CONFIRMATION | CONFIRMATION / CONFIRMATION | PASS | agreement, correct behavior.  |
| Revise my earlier intention to examine the lamp. | CORRECTION | CORRECTION / CORRECTION | PASS | agreement, correct behavior.  |
| Drop my outstanding request. | WITHDRAWAL | WITHDRAWAL / WITHDRAWAL | PASS | agreement, correct behavior.  |
| The nearer of those. | AMBIGUOUS | GM / GM | PASS | A: incorrect label, correct behavior.  |
| Once we know the way is clear, I will leave through the gate. | MIXED | SESSION / MIXED | PASS | A: incorrect label, correct behavior.  |
| Describe her posture; then I ask Mara about the road. | MIXED | GM / GM | PASS | A: incorrect label, correct behavior.  |
| What was the reason for the discovery? | GM | GM / GM | PASS | agreement, correct behavior.  |

No fresh final-prompt holdout accuracy is claimed. The first fresh sample informed refinements; final replay is containment/regression evidence, not an unseen requalification. Original failed messages and outputs are preserved.
