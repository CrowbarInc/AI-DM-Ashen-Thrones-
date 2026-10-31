# 25 — First-Failure Attribution

Rules are in `experiments/pr_eg_r6_r5/score.py`. They read the frozen label and the locked plan. They do not treat the engine class as truth. F06 and F09 are named and are not emitted. F18 is the residual.

## All 105 baseline failures

| Code | Name | First | Also downstream |
|---|---|---:|---:|
| F01 | Wrong operation | 20 | 0 |
| F02 | Wrong referent | 0 | 0 |
| F03 | Wrong semantic role | 0 | 0 |
| F04 | Wrong question proposition | 26 | 1 |
| F05 | Relevant source omitted | 17 | 21 |
| F07 | Correspondence false rejection | 5 | 6 |
| F11 | Sufficiency misclassification | 15 | 51 |
| F12 | Excessive clarification | 0 | 6 |
| F13 | False uncertainty | 0 | 44 |
| F15 | Expression distortion | 2 | 0 |
| F18 | Evaluation disagreement / residual | 20 | 0 |

F13 appears 44 times as a downstream code. Many of those turns already failed at the proposition or the operation, and the player then heard ignorance. Sufficiency is usually a consequence.

## Validation failures only

| Code | First |
|---|---:|
| F01 | 9 |
| F04 | 12 |
| F05 | 4 |
| F07 | 1 |
| F11 | 4 |
| F18 | 6 |

Host reason counts on the full baseline, including successes: unexpected_referent_operation 27, no_relevant_source 26, unwitnessed_referent_request 19, authorized_direct 15, authorized_partial 12.

Per-turn codes: `first_failures.json`.
