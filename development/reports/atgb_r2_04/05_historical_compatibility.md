# 05 — Historical Compatibility

Four synthetic_positive_control cases reuse the exact controlled raw substitutions from R2-03 adapter_controls.json. They are not newly sampled interpretations. They pass through current interpret_production_turn, then the existing decision_from_interpretation_record reconsideration used by API ownership. Complete records, preceding exchanges, exact inputs and decisions are in historical_compatibility.json. Original historical failures remain in the prior R2-03 behavioral packet and original traces, unchanged.

| Turn | Controlled subject | Host disposition | Exact host output |
|---|---|---|---|
| S02.2 | curfew start time | ANSWER | That has not been established in the information available to you. |
| S02.3 | curfew start time | ANSWER | That has not been established in the information available to you. |
| S02.4 | Posted last-seen location of missing patrol | ANSWER | That has not been established in the information available to you. |
| S05.3 | Which account of the missing patrol? | CLARIFY | Do you mean the runner's rumor, or what you wanted to learn from the notice board? |

S02 controls set QUESTION / OTHER, no operations, no answer evidence, no clarification text. S02.3 explicitly restores curfew timing; the original stale requested_outcomes/premise strings remain recorded for transparency and are not promoted to authoritative facts. The unchanged adapter may report SAFE_ABSTENTION / clarification_required for zero-operation OTHER; it still preserves a valid record, and host reconsideration returns the honest limitation. This is not described as accepted action execution. No curfew or patrol hour is invented and the generic notice-board category is not emitted as an answer.

S02.4 uses the undiscovered baseline scene; the gated last-seen clue never enters the effective public request. Invalid clue selection is rejected. No automatic investigation is created. The runner's public rumor remains distinct from the posted warning.

S05.3 uses the same minimal active-social runner session as R2-03, with GM/CLARIFICATION, no operations and a runner-versus-board account question. The active NPC remains tavern_runner. An independent existing grounding call resolves tavern_runner contextually with executable addressee eligibility, while the subject remains unresolved; no NPC operation is executed. This tests independent slots, not a schema field for subject ambiguity or newly inferred topic certainty. R2-02's unchanged captured ASK-route tests continue to pass separately.

All four scene/world/session/raw inputs equal deep copies after decision; all decisions require no authoritative execution and have no context_update. No file-backed gameplay store is written by these controls. Original historical complete preturn snapshots are absent: these are controlled minimal-state compatibility experiments, not exact full-session historical replays. They establish host compatibility with appropriate interpretations; they do not establish that the live model will generate those interpretations or preserve authority on future completions. Human review remains pending; no new evaluator judgment or benchmark score.
