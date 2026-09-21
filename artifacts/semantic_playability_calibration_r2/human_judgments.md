# PR-AC Human Semantic Judgments

These judgments are the calibrated semantic authority for Round #2. Automated `semantic_result` is supporting evidence only.

Severity: Critical / Major / Moderate / Minor.
Owning layer is probable, not a production assignment.

| ID | Case | Turn | Symptom | Evaluator | Human | Severity | Probable owner | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J01 | R2-P1 | 1-2 | Untargeted watch/relic questions become the murmur bridge. Model was called, then rejected for `question_rule:social_exchange_first_sentence_not_speaker_grounded`. | FAIL | Fail | Major | Realization / speaker-grounding / social fallback | High |
| J02 | R2-P2 | 1 | "Tell me about the thief" dumps mashed visible facts; no thief exists here. | FAIL | Fail | Major | Context selection + realization | High |
| J03 | R2-P2 | 2 | Dye-vat question becomes "the moment passes…" bridge. | FAIL | Fail | Major | Realization / social fallback | High |
| J04 | R2-P3 | 1 | "What do I see" binds `gate_guard` and emits ignorance, while `captain_thoran_watch` is written. | PASS | Fail | Major | State ↔ narration + social fallback | High |
| J05 | R2-P3 | 2 | Notice pressure emits `Gate Guard mutters,` | FAIL | Fail | Critical | Final emission / social fallback | High |
| J06 | R2-P4 | 1 | "Glance at the notice" describes the crowd, not the board. | PASS | Fail | Major | Intent/object routing + observation realization | High |
| J07 | R2-MT01 | 2-3 | Reading / asking about the notice emits guard ignorance; `notice_patrol_route` never appears. | FAIL | Fail | Major | Intent routing + social fallback | High |
| J08 | R2-MT01 | 4-6 | Guard Captain is bound but only says "I don't know" about posted/authored patrol facts. | mixed | Fail | Major | Authored-knowledge realization | High |
| J09 | R2-MT01 | 7 | "Follow the missing patrol rumor" stays in social lock; scene remains `frontier_gate`. | PASS | Fail | Critical | Interaction routing / player-agency handling | High |
| J10 | R2-MT02 | 1-5 | Approach and watch-command questions collapse to the same Captain ignorance line. Authored topic exists on `gate_guard`. | mixed | Fail | Major | Authored-knowledge realization | High |
| J11 | R2-MT02 | 6 | Interlocutor swaps to `gate_guard`; Thoran lead is written; speech still denies knowledge. | PASS | Fail | Major | State ↔ narration | High |
| J12 | R2-MT02 | 7 | `Gate Guard mutters,` | FAIL | Fail | Critical | Final emission | High |
| J13 | R2-MT02 | 8 | Wait beat finally names Captain Thoran. Playable, but only after seven failed turns. | PASS | Pass with residue | Moderate | Realization recovered late | High |
| J14 | R2-MT03 | 2,5 | Runner emits broken refusal `I cannot answer that from what.` while `muddy_footprints_northwest` is written. | FAIL | Fail | Critical | Final emission + state ↔ narration | High |
| J15 | R2-MT03 | 3,6 | Runner can give grounded traveler talk. Continuity works when fallback does not fire. | PASS | Pass | — | — | High |
| J16 | R2-MT03 | 4 | `Tavern Runner mutters,` | FAIL | Fail | Critical | Final emission | High |
| J17 | R2-MT03 | 7 | "I'll stay at the gate instead of entering Cinderwatch" transitions to `market_quarter`. | FAIL | Fail | Critical | Intent parsing / scene transition | High |
| J18 | R2-MT03 | 3 | Narration is ingested as `narration_ctx_…` lead. | PASS | Fail | Moderate | Unsupported invention into lead registry | High |
| J19 | R2-MT04 | 1 | Lirael question does not instantiate an NPC. RC-21 state policy holds. | PASS | Pass | — | — | High |
| J20 | R2-MT04 | 2 | Investigate writes `notice_patrol_route` but narrates the crowd template. | FAIL | Fail | Major | State ↔ narration | High |
| J21 | R2-MT04 | 3,6 | "I read the notice" / pursue official follow-up emit guard ignorance. | mixed | Fail | Major | Object-intent routing + fallback | High |
| J22 | R2-MT04 | 5 | Looking for Lirael correctly finds nobody. Slight unsupported suggestion that the runner overheard her. | PASS | Pass with residue | Minor | Model / context | Moderate |
| J23 | R2-MT05 | 2,4,6 | Unusual sneak/climb/impossible-fly attempts produce usable diegetic consequences. | PASS | Pass | — | — | Moderate |
| J24 | R2-MT05 | 3,5 | Bribe and punch collapse to guard ignorance. | PASS | Fail | Major | Intent routing + social fallback | High |
| J25 | R2-MT05 | 1 | Investigate writes the notice clue while emitting scene-summary template. | PASS | Fail | Moderate | State ↔ narration | High |
| J26 | R2-MT05 | 4 | Climb invents House Verevin and rooftop sentries adjacent to hidden facts. | PASS | Fail | Moderate | Knowledge leakage / unsupported invention | Moderate |
| J27 | R2-MT05 | 7 | Look-around is replaced by a forced "Board, runner, or road" fork. | PASS | Fail | Moderate | Player-agency / UX | Moderate |
| J28 | R2-MT06 | 1-2 | Observation invents an unnamed speaker who hijacks the turn. | mixed | Fail | Major | Unsupported invention | High |
| J29 | R2-MT06 | 3-4 | Visible-actor and hidden-list probes become murmur bridges. Hidden list is not leaked. | FAIL | Fail | Major | Realization fallback; knowledge boundary partly OK | High |
| J30 | R2-MT06 | 5 | Captain ignorance of Ash Cowl hidden fact is legitimate. | PASS | Pass | — | Knowledge boundaries | High |
| J31 | R2-MT06 | 6 | "What have I confirmed with my own eyes" is treated as a Captain question and refused. | FAIL | Fail | Major | Intent routing | High |
