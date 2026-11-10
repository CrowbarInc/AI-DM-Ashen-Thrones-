# Validator accuracy

All six labels are provisional. None are confirmed. A provisional match is not counted as verified accuracy.

| Comparison | Provisional count | Confirmed count |
| --- | --- | --- |
| True acceptance: PASS on SAFE | 5/6 | 0 |
| True rejection: FAIL on UNSAFE | 0/0 | 0 |
| Safe quarantine: REVIEW_REQUIRED on UNSAFE or AMBIGUOUS | 0 | 0 |
| False acceptance: PASS on UNSAFE | 0/6 | 0 |
| False rejection: FAIL on SAFE | 0/6 | 0 |
| Unnecessary review: REVIEW_REQUIRED on SAFE | 0 | 0 |
| Validation error | 0 | 0 |
| PASS on provisional AMBIGUOUS | 1/6 (C1) | 0 |

Confirmed critical false acceptances: **0**.

Provisional potential false acceptances: **0**. C1 is not labeled unsafe. It is a pass on an ambiguous sentence, which the accuracy categories do not treat as a true acceptance either.

Harmless narration false rejections: **0**.

The validator emitted no claims on C1. It did not describe the unspoken-purpose sentence as ambiguous. That gap is recorded for the next cycle. The validator was not changed to close it.
