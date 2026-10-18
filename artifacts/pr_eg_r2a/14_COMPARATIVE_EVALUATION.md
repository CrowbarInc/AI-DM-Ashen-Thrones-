# 14 — Comparative Evaluation

All observational matrices use evaluated records only. Untested records are listed separately. `evaluation_measured_only.json` is authoritative for measured classification; legacy `metrics.json` also includes a fail-closed policy matrix on all cases, which must not be mistaken for completed experiments. D reuses C evidence and is not statistically independent.

| Split | Strategy | Evaluated | Untested | Safe accepted / safe | Unsafe accepted / unsafe | Safe rejects | Safe abstains | 3-way accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | A | 72 | 0 | 5/30 | 0/39 | 0 | 25 | 0.111 |
| development | B | 72 | 0 | 5/30 | 0/39 | 0 | 25 | 0.111 |
| development | C | 60 | 12 | 28/28 | 3/30 | 0 | 0 | 0.783 |
| development | D | 60 | 12 | 28/28 | 3/30 | 0 | 0 | 0.783 |
| holdout | A | 30 | 0 | 0/12 | 0/16 | 0 | 12 | 0.067 |
| holdout | B | 30 | 0 | 0/12 | 0/16 | 0 | 12 | 0.067 |
| holdout | C | 0 | 30 | 0/0 | 0/0 | 0 | 0 | None |
| holdout | D | 0 | 30 | 0/0 | 0/0 | 0 | 0 | None |

development: 72 evaluated, 0 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 5 | 0 | 25 |
| REJECT | 0 | 0 | 39 |
| ABSTAIN | 0 | 0 | 3 |

development: 72 evaluated, 0 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 5 | 0 | 25 |
| REJECT | 0 | 0 | 39 |
| ABSTAIN | 0 | 0 | 3 |

development: 60 evaluated, 12 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 28 | 0 | 0 |
| REJECT | 3 | 19 | 8 |
| ABSTAIN | 1 | 1 | 0 |

development: 60 evaluated, 12 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 28 | 0 | 0 |
| REJECT | 3 | 19 | 8 |
| ABSTAIN | 1 | 1 | 0 |

holdout: 30 evaluated, 0 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 0 | 0 | 12 |
| REJECT | 0 | 0 | 16 |
| ABSTAIN | 0 | 0 | 2 |

holdout: 30 evaluated, 0 untested. 

| Gold / actual | ACCEPT | REJECT | ABSTAIN |
| --- | --- | --- | --- |
| ACCEPT | 0 | 0 | 12 |
| REJECT | 0 | 0 | 16 |
| ABSTAIN | 0 | 0 | 2 |

holdout: 0 evaluated, 30 untested. No measured matrix.

holdout: 0 evaluated, 30 untested. No measured matrix.

Critical metric: C and D accepted three unauthorized high-risk development claims. A/B observed zero but have poor safe coverage; abstaining on safe cases is a usability failure, not a false safe acceptance. Exact gold REJECT vs actual ABSTAIN is a classification mismatch but still blocks unsafe delivery. An H case accepted is a separate unresolved-authority acceptance and is retained in failure lists.

Category/risk unsafe acceptances, category safe rejections/abstentions and every failure id are in `evaluation_measured_only.json`; no ambiguity cases were silently dropped. Small, authored, correlated samples and incomplete C coverage preclude a general error-bound claim. Claim coverage is not independently scored. Qualitative tradeoff: A low complexity/poor flexibility/high wording maintenance; B extra provider/format/schema overhead without semantic gain; C flexible but critical safety failures and model coupling; D low fast-path coverage and inherited unsafe tail. None earns readiness.

Evidence: STATIC = current source inspection; LOCAL = executed existing host functions with disposable fixtures; FRESH = new Responses API call; REPLAY = reuse of retained provider result; INFERENCE = recommendation beyond observed sample. No experiment changes production code. ABSTAIN prohibits delivery; it is not a safe acceptance.


## Existing hard-validator compatibility baseline

| Gold / direct seam | ACCEPT | REJECT |
| --- | --- | --- |
| ACCEPT | 22 | 20 |
| REJECT | 38 | 17 |
| ABSTAIN | 5 | 0 |

LOCAL: 38/55 gold-unsafe candidates passed the direct seam; 20/42 gold-safe candidates were rejected, and all 5 ambiguous candidates passed. These are synthetic-resolution helper outcomes, not full-handler delivery rates. The hard-validator interface explicitly checks high-confidence invalidity, so hard_valid cannot be repurposed as complete semantic certification.
