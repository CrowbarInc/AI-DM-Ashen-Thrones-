# Fixed samples

| ID | Previous coverage | Updated coverage | Previous combined | Updated combined | Consequential |
|---|---|---|---|---|---|
| A1 | REVIEW_REQUIRED | PASS | FAIL | FAIL | FAIL |
| A2 | PASS | PASS | PASS | PASS | PASS |
| B1 | PASS | PASS | PASS | PASS | PASS |
| B2 | PASS | PASS | PASS | PASS | PASS |
| C1 | PASS | PASS | PASS | PASS | PASS |
| C2 | REVIEW_REQUIRED | PASS | REVIEW_REQUIRED | PASS | PASS |
| D1 | REVIEW_REQUIRED | PASS | REVIEW_REQUIRED | PASS | PASS |
| D2 | REVIEW_REQUIRED | PASS | REVIEW_REQUIRED | PASS | PASS |

All mandatory facts are covered after the change, with none missing, ambiguous or contradicted in these eight fixed rows. Only A1 has a consequential addition flagged (unauthorized urgent update). Full evidence strings, authority, facts, previous pipeline reexecution, current semantic/legacy/coverage and final decisions are in fixed_results.json. Original raw SDK response file is byte-preserved; raw_text_integrity.json verifies exact extracted prose and archived baseline reproduction.
