# Validator decisions

Every candidate was passed through the frozen validator twice in effect: once inside `validate_prelude`, and once by a direct call on the same raw string after the turn. The direct call is the same function. It is not an independent semantic judge.

| Candidate | Direct decision | Direct reasons | Claims | Legacy `hard_valid` | Pipeline diagnostic | Pipeline consequential decision |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | PASS | none | 0 | true | `heuristic_pass_pending_review` | PASS |
| A2 | PASS | none | 0 | true | `heuristic_pass_pending_review` | PASS |
| B1 | PASS | none | 0 | true | `heuristic_pass_pending_review` | PASS |
| C1 | PASS | none | 0 | true | `heuristic_pass_pending_review` | PASS |
| C2 | PASS | none | 0 | true | `heuristic_pass_pending_review` | PASS |
| D1 | PASS | none | 0 | true | `heuristic_pass_pending_review` | PASS |

Counts: PASS 6, FAIL 0, REVIEW_REQUIRED 0, VALIDATION_ERROR 0.

`heuristic_pass_pending_review` means the pipeline kept the prelude in the quarantine assembly. It does not authorize showing that prelude to the player. `review_required` on the preview object remains the anchored-preview default and is not the consequential decision. The consequential decision for all six is PASS.

Direct validator latency: 1.526, 1.082, 1.119, 1.285, 1.065, 0.614 ms. Mean 1.115 ms. Maximum 1.526 ms.

Pipeline validation latency, which includes the legacy check: 18.858, 2.229, 2.330, 3.985, 3.784, 2.470 ms. Mean 5.609 ms. Maximum 18.858 ms. The first call is the outlier.

No validation exception was raised. `provider_requests` on every validator result is 0.

The full claim lists and legacy audits are in `validator_decisions.json`.
