# 36 — Acceptance Gates

| Gate | Result | Evidence |
|---|---|---|
| 1 — Referent identity | PASS | Stable host conversation UUID + monotonic sequence; 47 controlled tests and persisted records. |
| 2 — Active focus | FAIL | 111/120 = 92.5%; local audit; target 95%. |
| 3 — Corrections | FAIL | 7/13 = 53.8%; local audit; target 90%. |
| 4 — Follow-ups | FAIL | 18/28 = 64.3%; local audit; target 90%. |
| 5 — Referent binding | FAIL | 25/41 = 61.0%; local audit; target 95%. |
| 6 — False clarification | FAIL | 22/120 = 18.3%; target <=10%. |
| 7 — Answer relevance | PASS | Matched sequence: 14/30 to 25/30 in local audit; identical initial fixtures, later histories diverge. One sample, not causal proof. |
| 8 — Answer sufficiency | LIMITED | Matched locally scored sufficiency improves 14/30 to 23/30, but three intended partial answers were overstated as direct; no broad nonregression claim. |
| 9 — Save/load | PASS | Disk reloads, controlled persistence and separate-process correction: {'loaded_identity': True, 'http': True, 'parent': True, 'revision': True, 'subject': True, 'sealed': True, 'history_exact': True}. |
| 10 — Disclosure | PASS (MEASURED SCOPE) | 0 failed observed checks across 149 turns; finite coverage limits in integrity_results.json. |
| 11 — Canonical state | PASS (MEASURED SCOPE) | 0 failed observed checks across 149 turns; finite coverage limits in integrity_results.json. |
| 12 — Discovery | PASS (MEASURED SCOPE) | 0 failed observed checks across 149 turns; finite coverage limits in integrity_results.json. |
| 13 — Final delivery | PASS (MEASURED SCOPE) | 0 failed observed checks across 149 turns; finite coverage limits in integrity_results.json. |
| 14 — Regression | PASS | 431 passed, 5 inherited failed, 0 new failures. |
| 15 — Holdouts | FAIL | Hashes unchanged and evaluated, but failed role reversal, source interpretation and original correction cases do not support qualification. |
| 16 — Performance | FAIL | Mean input 3188.3, P95 input 3635; P95 latency 5107.1 ms; one strict_social context outlier. |
| 17 — Fresh provider | PASS | 120 turns / 8 primary groups, plus 29 predecessor-holdout turns / 2 groups and one restarted-process turn; source hashes unchanged. |
