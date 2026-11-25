# Regression results

| Suite | Historical pass / fail | Current pass / fail | New failure identities |
| --- | ---: | ---: | ---: |
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

The first focused pass recorded one extra failure, `tests.test_grounded_marking_removal::test_http_lifecycle_persists_reloads_and_restores`. The child process exited `3221225794` (`0xC0000142`) while the suites, the prior matrices, and the movement matrix were running together. The player lines in that test are sleeve inspection and mark removal, not destination alternatives. Rerunning that partition alone passed, and the merged focused result is 470/1 with no new failure identity. The inherited failure remains `tests.test_combat_resolution::test_api_roll_initiative_returns_canonical_resolution`.

Historical recall **71/71**. Reference matrix **111/111**, with the exact T02, T03, T06, T13, and T16 checks passing in the exact phase. Attention matrix **103/103**, plus the exact T02/T03 sequence. Correction matrix **97/97**. Correction recovery sequence **7/7**. Clarification-recovery controls **115/115**, plus the exact board replays and their sequence, runner exit 0. That is the historical 120.

New material regression failure identities: **0**. Combat resolver controls **5/5**.

[Isolated partitions](evidence/regression_isolated) · [Prior matrices](evidence/prior_acceptance/runner_status.json) · [Board](evidence/board)
