# 06 — Semantic Generalization Results

The expressions in holdouts.json were written before production edits. No exact-match production handlers were added for holdout failures. The 12-call live test exercised the production interpreter in the same authored scene, without pending proposals or active NPC setup. It tests the interpreter contract, not complete conversational behavior.

| Expression | Expected | Observed label | Result |
|---|---|---|---|
| Could you paint a picture of this place? | GM | GM | PASS |
| What does her worried expression tell me? | GM | NPC | FAIL |
| I ask Mara what troubles her. | NPC | NPC | PASS |
| I make for the courtyard gate. | CHARACTER | CHARACTER | PASS |
| Would a check be needed for that? | SESSION | GM | FAIL |
| Actually, use the lantern instead. | CORRECTION | ACTION | FAIL |
| All right, proceed. | CONFIRMATION | ACTION | FAIL |
| Forget that plan. | WITHDRAWAL | ACTION | FAIL |
| That one over there. | AMBIGUOUS | GM | FAIL |
| Is it safe to go outside? If so, I head out. | MIXED | GM | FAIL |
| I tell the sergeant to describe the courtyard. | NPC | NPC | PASS |
| Could I travel through the gate? | GM | GM | PASS |

**Observed strict label score: 5/12.** The NPC-expression error is materially unsafe for GM/non-mutating intent. Rules-question mode was present despite a GM/QUESTION extension label. Ambiguity safely clarified despite a GM recipient label. Correction and withdrawal are intercepted before interpretation by the production continuity layer, so their standalone provider errors do not prove full-pipeline execution. Bare confirmation without pending context must clarify; its standalone ACTION label is wrong. The mixed input kept ASK+MOVE components while calling the recipient GM: the final structural safeguard now emits MIXED/CLARIFY with both components retained.

Development examples are the ten-turn fixture and focused authority/proposal tests. Final-code changes made after this measurement were checked deterministically/with recorded data; these original holdouts cannot be called unseen requalification after those changes. No provider-disabled test is presented as natural-language competence. The final recommendation remains C.

Full production HTTP replay of those captured holdout records: **10/12 behavioral checks pass**, separately from the strict live interpreter label score. Confirmation is tested with a genuine API-created pending two-step proposal; other expressions start from the authored scene. Failures: the expression question invokes social/world progression; 'I make for the courtyard gate' reaches a deterministic execution decision but emits an unresolved result instead of completing movement. The latter did not call the wire interpreter. The replay source and full resolutions are in replay_holdouts.py and production_holdout_replay.json. These checks reuse measured expressions and are not an unseen holdout rerun.
