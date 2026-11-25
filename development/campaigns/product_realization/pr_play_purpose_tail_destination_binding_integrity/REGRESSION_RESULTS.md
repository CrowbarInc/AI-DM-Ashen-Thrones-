# Regression results

New material failure identities: **0**.

Partitions ran two at a time, then any non-zero runner exit was eligible for one isolated retry. None needed a retry. No partition was counted before it executed. Network attempts: none.

| Suite | Historical | Current | New identities |
| --- | ---: | ---: | --- |
| Combined | 455 / 17 | 455 / 17 | 0 |
| Focused | 470 / 1 | 470 / 1 | 0 |
| Scoped | 191 / 0 | 191 / 0 | 0 |
| Inspection admission | 64 / 0 | 64 / 0 | 0 |
| Statement ownership | 65 / 0 | 65 / 0 | 0 |
| NPC addressee and social commitment | 71 / 0 | 71 / 0 | 0 |
| Social grounding reconciliation | 37 / 0 | 37 / 0 | 0 |
| Incidental posture | 85 / 0 | 85 / 0 | 0 |
| Current-scene evidence | 84 / 0 | 84 / 0 | 0 |
| Harness reconciliation | 43 / 0 | 43 / 0 | 0 |
| Previous movement acceptance | 109 / 0 | 109 / 0 | 0 |
| Compound-social acceptance | 87 / 0, looking-for counted as a failed transition | 87 / 0, looking-for is an authorized arrival | 0 |
| Disjunctive script | 53 / 0 with the social residual still traveling | 52 / 53 | the one failure is the obsolete `compound/social-residual` assertion that still expects travel |

The focused failure is the inherited `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`. Combined failures match the baseline set: none added, none removed.

Prior matrices, runner exit 0:

| Matrix | Result |
| --- | --- |
| Historical recall | 71 / 71 |
| Reference grounding | 111 / 111 |
| Exact captured turns T02, T03, T06, T13, T16, and the T02/T03 sequence | 6 / 6 |
| Attention posture | 103 / 103 |
| Correction and pronoun | 97 / 97 |
| Correction recovery sequence | 7 / 7 |

Counted the way the previous handoff counted them, reference is 116, attention is 105, and correction is 106. No case in those matrices failed.

Clarification-recovery board: routing 13/13, recognition 17/17, scope 31/31, components 27/27, lifecycle 8/8, controls 7/7, sequence 12/12. That is **115/115**. Exact board replays and their sequence exited 0. Together with those exact checks this is the historical 120. Combat resolver controls **5/5**.

[Isolated suites](evidence/regression_isolated) · [Prior](evidence/prior_acceptance/runner_status.json) · [Board](evidence/board/acceptance) · [Movement](evidence/previous_movement_acceptance/result.json)
