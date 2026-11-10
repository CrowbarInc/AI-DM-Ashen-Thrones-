# Experiment matrix

| Case | Status | Evidence / limit |
|---|---|---|
| A Flag disabled | PASS | Five-action control |
| B Flag enabled | PASS | Session-bound HTTP run |
| C Discovery | PASS | Notice-board route |
| D No new information | PASS | Accurate fallback; AI acceptance remains partial |
| E Repeat | PASS | Known resolution; zero-call fast path |
| F Follow-up | PASS | Gate then barrel |
| G Continuity sequence | PASS | Five HTTP 200 responses |
| H Valid AI publication | PASS | Turn 1 |
| I Invalid rejection | PASS | Live REVIEW and injected FAIL |
| J Relevant fallback | PASS | Turns 2/4 and faults |
| K Fast path | PASS | Turns 3/5 |
| L Timeout recovery | PASS | Injected timeout and continuation |
| M Provider error | PASS | Injected error and continuation |
| N Validation recovery | PASS | FAIL/REVIEW/shape and exception controls |
| O Browser submission | BLOCKED | Attachment timeout twice; zero UI actions |
| P Frontend rendering | NOT TESTED | No attached tab |
| Q State integrity | PASS | Per-turn control agreement |
| R Provider accounting | PASS | 3 requests / 1525 tokens |
| S Latency measured | PASS | Measured; speed improvement not established |
| T Gameplay quality | PARTIAL | Provisional fallback gain; live no-discovery unreliable |
| U Regression | PASS | Focused: 746/749 passed, 3 failures, 0 errors; 0 new failures. Additional failed-examination boundary: 1 passed. PR55 holdout wrapper: 1/1 passed. Broader authority assurance: 9/9 failures involving hard_validation_attempt_1. Full suite NOT TESTED. |

Measurement PASS does not imply improved latency. Overall verdict remains B.
