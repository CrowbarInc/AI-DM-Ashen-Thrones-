# 09 — Semantic Requalification

The original 24 are the unchanged PR-EF holdouts plus R1 independent holdouts. Nine additional expressions were frozen before production changes (additional_holdouts.json). No expression was removed/reworded. Strict raw labels, normalized labels and end-to-end behavior are distinct. In fresh production original 24: 24 behavioral passes, zero detected authority/state violations or authoritative-result contradictions. In additional nine: five passes, four intent/ownership failures, one critical ambiguous-target authorization/state violation, zero identified disclosures or contradictions of an already validated target. Critical turn and full state evidence are retained in behavior_1.json. Holdouts replay interpretation while stubbing narration; behavior_1 uses fresh production interpretation AND narration. Deterministic fast paths have no raw provider label and are excluded from label denominator.

| Sample | Original behavior /24 | Additional /9 | Raw strict agreement / available | State violations |
|---|---:|---:|---:|---:|
| holdouts_1.json | 21 | not sampled | 14/24 | 0 |
| holdouts_2.json | 24 | not sampled | 14/24 | 0 |
| holdouts_3.json | 22 | 2 | 17/33 | 0 |
| holdouts_4.json | 24 | 5 | 17/33 | 0 |
| behavior_1.json | 24 | 5 | 14/25 | 1 |

Fresh isolated holdouts_3 were collected before the final topic-containment/head-noun/secondary-retention refinements. Final holdouts_4 is explicitly recorded replay of those outputs. Additional implicit-context isolated row 27 was evaluated without conversation log due to the harness's prior log=[] input; do not treat that row as a valid context-aware isolated qualification. Fresh production behavior_1 uses actual persisted setup and log and is final-code evidence. Its four additional failures are preserved in the detailed table below. Core final-code fresh 24 behavioral result is independently demonstrated; final fresh isolated remeasurement of all 33 was not performed.

Behavior checks include attribution, resolver identity and actual state as appropriate; they remain bounded assertions and do not establish all language semantics. One additional fresh production ambiguous-target holdout (turn 33) executed a social turn and advanced time/faction state when clarification was required: a critical authorization/state-integrity failure. No hidden-information disclosure or contradiction of an already validated final social target was identified; rejected provider drafts contain unauthorized claims and remain evidence of successful rejection, not emitted authority violations. Ownership/response relevance failures are correctness defects and block acceptance.

- Turn 26: I ask the sergeant who owns the lantern. → That has not been established in the information available to you.
- Turn 27: What does she mean by the road? → Sergeant Mara mutters, "Word is, the street beyond the gate is the north road." The street beyond the gate is the north road. That establishes the observation or result; its cause has not been established.
- Turn 31: Instead, make that a question about the lamp. → A soot-streaked lantern burns beside the courtyard gate.
- Turn 33: I ask one of them what happened. → Sergeant Mara says, "I cannot answer that from what is settled here."
