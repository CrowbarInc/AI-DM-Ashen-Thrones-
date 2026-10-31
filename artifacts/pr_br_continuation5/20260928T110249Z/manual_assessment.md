# Continuation 5 focused live — manual assessment

Stamp `20260928T110249Z`. Isolated storage. Model `gpt-4.1-mini`. Five completed turns, zero aborted, five model calls, zero retries. The sixth budgeted turn was not sent. Smoke was not started.

| Turn | Player | Contract | Model vs final | Class |
|---|---|---|---|---|
| 1 | Ask the serjeant what rumor travelers are repeating | ask, no dimension | Model named woods hearsay. Final: "I have heard talk, but I cannot verify it." | PLAYER-FACING SEMANTIC FAILURE. Layer: strict-social catalog. No dimension, so the preservation check did not treat the model line as a resolved contract. |
| 2 | Ask him to repeat that rumor | ask, no dimension | Same model rumor. Final: "I will not carry out that request; you will need another route." | PLAYER-FACING SEMANTIC FAILURE. Layer: obligation fallback for an action/social request. No `active_claim`, so the source follow-up was not sent. |
| 3 | Look the posted sheet over | inspect, target posted sheet, `active_inspected` set | Model listed taxes, curfew, and the missing patrol. Final: "The inspection establishes no further reliable detail about gate_serjeant." | PLAYER-FACING SEMANTIC FAILURE. Layer: inspection fallback. Both lines scored `satisfied` under the eight-word inspection rule, so preservation did not block the swap. |
| 4 | What does it actually say? | ask, ambiguous, clarification | Model repeated the notice. Final: "Which do you mean?" | Contract failed to bind `active_inspected`. Clarification matches that contract. Not a destruction of a correct contract. |
| 5 | Does it look like people use this often? | perceive, use+appearance, inherited posted sheet | Model answered frequency of use. Final keeps the use answer and drops a rumor aside. Status `partial` (`covered:use`, `missing:appearance`). | ACCEPTABLE for the use question. Appearance was an extra cue, not a destroyed use answer. |

Evaluator: false PASS on turns 1 and 3 (PASS while the useful line was replaced). Turn 4 PASS follows the ambiguous contract, not the player's sheet. Turn 2 FAIL is a true fail. Turn 5 PASS matches the surviving use answer. False FAIL: 0.

Semantic-destroying replacements of a useful generated line: 3 (turns 1–3). The automated flag counted only turn 5, because turns 1–2 are `unchecked` and turn 3's stock line is also `satisfied`.
