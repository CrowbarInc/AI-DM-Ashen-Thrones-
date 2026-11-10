# Validation results

| Candidate | Final gate | PR55 | Coverage |
|---|---|---|---|
| A1 | FAIL | FAIL | REVIEW_REQUIRED |
| A2 | PASS | PASS | PASS |
| B1 | PASS | PASS | PASS |
| B2 | PASS | PASS | PASS |
| C1 | PASS | PASS | PASS |
| C2 | REVIEW_REQUIRED | PASS | REVIEW_REQUIRED |
| D1 | REVIEW_REQUIRED | PASS | REVIEW_REQUIRED |
| D2 | REVIEW_REQUIRED | PASS | REVIEW_REQUIRED |

Detailed claims and reasons are in validation_decisions.json. PR55 SHA-256 stays ed29349cde1bb641178b01175f608142707dcc21a7d387e4b0f57707a1d0d6b6. Existing legacy mechanical/hidden/authority checks remain mandatory. Any FAIL, REVIEW_REQUIRED or VALIDATION_ERROR forces a quarantined deterministic fallback. A PASS still never promotes the candidate. A1 illustrates a conservative unauthorized_discovery rejection of apparently authorized route paraphrase; review is separate from the validator output.
