# 05 — Prioritization Matrix

Judgment scale 1–5: severity 1 cosmetic to 5 blocks meaningful interaction; exposure 1 niche to 5 pervasive inferred play interaction; generalizability 1 isolated to 5 broad coherent mechanism; confidence 1 speculation to 5 direct records plus owning code; feasibility 1 broad redesign to 5 small existing-owner change; safety 1 high authority risk to 5 low regression risk. Exposure is an ordinal inference supported by observed examples, not measured population frequency. Feasibility and safety higher means easier/safer.

Weights: severity .25, exposure .20, generalizability .20, confidence .15, feasibility .10, safety .10. Weighted score = sum(weight × ordinal rating), maximum 5. Scores guide judgment, not empirical efficacy estimates.

| Eligible rank | Candidate boundary | Severity | Exposure | Generality | Confidence | Feasibility | Safety | Weighted |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | F1 shared host speech-role/addressee rejection | 5 | 4 | 4 | 5 | 4 | 3 | 4.30 |
| 2 | F2 legacy question/evidence sufficiency | 5 | 5 | 4 | 3 | 2 | 3 | 4.00 |
| 3 | F3 ordinary remark ownership/acknowledgment | 4 | 4 | 3 | 4 | 4 | 4 | 3.80 |
| 4 | F4 correct-plan expression/assembly quality | 3 | 5 | 3 | 3 | 3 | 4 | 3.50 |
| Excluded | F5 correction comparison, existing R1-07 | 5 | 4 | 3 | 4 | 3 | 4 | 3.95 |

Machine-readable ratings, weights and computed sums: `prioritization_scores.json` and `.csv`. F5's numerical value does not create implementation eligibility; the user explicitly excludes reopening it and latest live acceptance is pending.

## Evidence, uncertainty and expected benefit

F1: two matching host rejections after model selects runner, with persistent active social focus. Highest diagnostic confidence and a deterministic repair boundary; expected benefit is letting reasonable follow-ups reach the existing authority path. Risks: wrong-speaker execution, explicit target override, absent interlocutor, speech recipient confusion, pronoun/topic conflation. Safety is only 3 because the owner guards actual execution and world advancement. Generality 4 refers to grammatical address roles across NPCs, not all anaphora. S05 content ambiguity reduces the breadth of claimed benefit.

F2: repeated S02 non-answers and related S03.5 mismatch, supported conceptually by R5 paired proposition interventions. Highest likely exposure. However hours do not exist, clue disclosure is gated and legacy membership checking cannot prove entailment. A safe bounded semantic sufficiency repair is less specified; use a narrow investigation if chosen. Confidence/feasibility fall below F1. No new world facts should be manufactured to answer a recognized question.

F3: identical SESSION/OBSERVATION fallback in two scenarios and raw model acknowledgment intent. Small existing-owner contract work seems feasible; authority can remain non-mutating. Lower severity/general scope than meaningful NPC questions and some overlap with existing R1-07 acknowledgment guidance. Fixing only the string would mask model ownership; a new ACK speech act is not automatically justified.

F4: many poor-sounding replies, but broad symptom counts confound wrong content with expression. R5 isolates a small expression gain; ATGB S03.5 is wrong before expression. Naturalness-only repair ranks lower despite exposure. Keep correct-plan expression as a future, separately validated boundary.

## Sensitivity and decision stability

F1–F2 gap is 0.30, not decisive numerical separation. Raising F2 diagnostic confidence from 3 to 5 ties at 4.30; raising F2 feasibility by two also ties if combined with one confidence increment. Lowering F1 generality by one and confidence by one puts it at 3.95, below F2. Reducing F1 exposure by one gives 4.10, still narrowly ahead. F3 ties F2 if its generality rises one point, but evidence does not currently establish that broader mechanism.

Thus the ranking is conditional on defensible diagnostic/repair-boundary judgments, not a claim of precise utility. Direct host evidence breaks the close F1/F2 comparison: F1 can remove an established incorrect deterministic rejection without solving general semantic relevance. If owner-level reconstruction disproves the described grammatical boundary, stop and reconsider F2; do not preserve rank by weakening authority. F2's potential total benefit could be larger, but its currently credible one-pass implementation scope is weaker. No fabricated failure rate, aggregate recovery estimate or provider-cost savings is used.
