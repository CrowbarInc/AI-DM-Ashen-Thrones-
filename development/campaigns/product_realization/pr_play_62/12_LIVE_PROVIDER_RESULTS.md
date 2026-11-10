# Live provider results

OpenAI existing expression adapter, gpt-4.1-mini-2025-04-14. Three dispatched
requests, no retries; 1,412 input + 113 output = 1,525 tokens. Budget 8 requests /
15,000 tokens; existing output cap 80 retained. Credentials are not exported.

| Turn | Decision | Input/output/total tokens | Publication |
|---|---|---|---|
| 1 | PASS | 436/24/460 | AI |
| 2 | REVIEW_REQUIRED | 488/41/529 | Deterministic fallback |
| 4 | REVIEW_REQUIRED | 488/48/536 | Deterministic fallback |

Turns 3/5 are zero-call fast paths, not AI acceptance samples. Validated/published
AI 1/1; rejection fallbacks 2; fast paths 2. No favorable-output retries.
Original candidates, complete validation traces and ledger remain restricted
machine evidence. New barrel/gate semantic and legacy layers passed, mandatory
route coverage did not. Gate “only lead” is also unsupported on manual inspection.
Validation PASS is not semantic proof.
