# Ambiguity analysis

`REVIEW_REQUIRED` is fail-closed in `apply_consequential_gate`. It sets `hard_valid` false and adds `consequential_review_required`. It is not a pass.

## Where it is used

| Source | Rows | Why |
| --- | --- | --- |
| PR-PLAY-54 `R1` | The compartment yields. | The result is underspecified. Existing reason `ambiguous_consequential`. |
| PR-PLAY-54 `R2` | The lock resists your efforts. | The investigation succeeded and the resistance is not an authorized outcome. |
| Development `D17` | You notice an unfamiliar marking near the door. | `AMBIGUOUS_CONSEQUENCE` |
| Holdout `R01`–`R10` | Unfamiliar or odd marks, symbols, glyphs, inscriptions, runes. | `AMBIGUOUS_CONSEQUENCE` |

Holdout review rate: 10/70. All 10 were labeled ambiguous before the run. None of the 30 fabrications were parked in review. None of the 20 harmless lines were parked in review.

## Where it is not used

A clear find, a clear acquisition, a confession, a collapsed jetty, or a contradicted route is `FAIL`. Missing input types are `VALIDATION_ERROR`, not review. An empty authority plus a clear new object is `FAIL`.

Reason codes actually emitted:

| Code | Use |
| --- | --- |
| `AMBIGUOUS_CONSEQUENCE` | Unfamiliar mark |
| `CONTRADICTORY_AUTHORITY` | Compass opposite |
| `POTENTIAL_HIDDEN_DISCLOSURE` | Restricted-text overlap |

`MISSING_AUTHORITY_CONTEXT` and `UNSUPPORTED_CLAIM_STRUCTURE` were not needed. Invalid input is already `VALIDATION_ERROR` with `invalid_validation_input`. Adding those codes as a second review bucket would have widened review without a case that required it.

Speculation (`wonder`, `suspect`, `might`, `as though`) stays `PASS` when it does not presuppose a recovery. That is a non-claim, not a review.
